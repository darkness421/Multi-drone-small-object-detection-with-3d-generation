#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

OVERLEAF_REPO=${OVERLEAF_REPO:-/tmp/accv-overleaf}
COMMIT_MESSAGE=${COMMIT_MESSAGE:-"Update ACCV experiment status"}
OVERLEAF_COMMIT_MESSAGE=${OVERLEAF_COMMIT_MESSAGE:-"Update paper experiment snapshot"}

DO_MAIN_COMMIT=${DO_MAIN_COMMIT:-0}
DO_MAIN_PUSH=${DO_MAIN_PUSH:-0}
DO_OVERLEAF_SYNC=${DO_OVERLEAF_SYNC:-1}
DO_OVERLEAF_COMMIT=${DO_OVERLEAF_COMMIT:-0}
DO_OVERLEAF_PUSH=${DO_OVERLEAF_PUSH:-0}
UPDATE_RESULTS_SECTION=${UPDATE_RESULTS_SECTION:-1}
TOP_K=${TOP_K:-8}
DO_NOTION_EXPORT=${DO_NOTION_EXPORT:-1}
DO_NOTION_UPDATE=${DO_NOTION_UPDATE:-0}
NOTION_EXPORT_DIR=${NOTION_EXPORT_DIR:-notion_exports/bidaily}
NOTION_MARKDOWN_PATH=${NOTION_MARKDOWN_PATH:-}
NOTION_NO_IMAGES=${NOTION_NO_IMAGES:-1}

PUBLISH_PATHS=${PUBLISH_PATHS:-docs/24h_experiment_orchestrator.md,docs/github_overleaf_automation.md,scripts/ubuntu/run_24h_experiment_orchestrator.sh,scripts/ubuntu/run_bidaily_publication_update.sh,scripts/ubuntu/publish_experiment_update.sh,scripts/export_overleaf_results.py,scripts/build_bidaily_update_markdown.py,notion_exports/bidaily,outputs/experiments/server_with_proposed,outputs/reports/server_with_proposed,outputs/experiments/server_fresh/large_20260524_140922,outputs/reports/server_fresh_baselines/large_20260524_140922}

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*"
}

git_commit_if_needed() {
  local repo=$1
  local message=$2
  shift 2
  local paths=("$@")
  git -C "$repo" add -- "${paths[@]}"
  if git -C "$repo" diff --cached --quiet; then
    log "No staged changes in $repo"
    return
  fi
  git -C "$repo" commit -m "$message"
}

maybe_push() {
  local repo=$1
  if git -C "$repo" rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
    git -C "$repo" push
  else
    log "No upstream configured for $(git -C "$repo" rev-parse --abbrev-ref HEAD); skipping push"
  fi
}

if [[ "$DO_OVERLEAF_SYNC" == "1" ]]; then
  update_flag=()
  if [[ "$UPDATE_RESULTS_SECTION" == "1" ]]; then
    update_flag+=(--update-results-section)
  fi
  python -m scripts.export_overleaf_results \
    --overleaf-repo "$OVERLEAF_REPO" \
    --top-k "$TOP_K" \
    "${update_flag[@]}"
fi

notion_markdown_file=""
if [[ "$DO_NOTION_EXPORT" == "1" ]]; then
  notion_args=(--output-dir "$NOTION_EXPORT_DIR" --top-k "$TOP_K")
  if [[ -n "$NOTION_MARKDOWN_PATH" ]]; then
    notion_args+=(--output "$NOTION_MARKDOWN_PATH")
  fi
  notion_markdown_file=$(python -m scripts.build_bidaily_update_markdown "${notion_args[@]}")
  log "Generated Notion/GitHub bi-daily markdown: $notion_markdown_file"
fi

if [[ "$DO_NOTION_UPDATE" == "1" ]]; then
  if [[ -z "${NOTION_TOKEN:-}" || -z "${NOTION_PAGE_ID:-}" ]]; then
    log "Skipping Notion append: set NOTION_TOKEN and NOTION_PAGE_ID when DO_NOTION_UPDATE=1."
  elif [[ -z "$notion_markdown_file" || ! -e "$notion_markdown_file" ]]; then
    log "Skipping Notion append: no generated markdown file was found."
  else
    notion_update_args=(--page "$NOTION_PAGE_ID" --markdown "$notion_markdown_file")
    if [[ "$NOTION_NO_IMAGES" == "1" ]]; then
      log "Appending text/table status to Notion without image uploads."
    fi
    python -m scripts.append_notion_markdown "${notion_update_args[@]}"
  fi
fi

if [[ "$DO_MAIN_COMMIT" == "1" ]]; then
  IFS=',' read -r -a paths <<< "$PUBLISH_PATHS"
  clean_paths=()
  for path in "${paths[@]}"; do
    path=${path//[[:space:]]/}
    [[ -z "$path" ]] && continue
    if [[ -e "$path" ]]; then
      clean_paths+=("$path")
    else
      log "Skipping missing publish path: $path"
    fi
  done
  if [[ "${#clean_paths[@]}" -gt 0 ]]; then
    git_commit_if_needed "$PWD" "$COMMIT_MESSAGE" "${clean_paths[@]}"
  else
    log "No existing main-repo publish paths."
  fi
fi

if [[ "$DO_MAIN_PUSH" == "1" ]]; then
  maybe_push "$PWD"
fi

if [[ "$DO_OVERLEAF_COMMIT" == "1" ]]; then
  git_commit_if_needed "$OVERLEAF_REPO" "$OVERLEAF_COMMIT_MESSAGE" \
    figures/auto \
    tables/auto_detector_results.tex \
    sections/auto_experiment_status.tex \
    sections/05_results.tex
fi

if [[ "$DO_OVERLEAF_PUSH" == "1" ]]; then
  maybe_push "$OVERLEAF_REPO"
fi

log "Publish step complete"
