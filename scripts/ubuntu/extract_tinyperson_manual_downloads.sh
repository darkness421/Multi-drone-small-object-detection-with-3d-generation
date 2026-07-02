#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

RAW_ROOT=${RAW_ROOT:-data/raw/TinyPerson}
MANUAL_DIR=${MANUAL_DIR:-$RAW_ROOT/manual_downloads}
EXTRACT_ROOT=${EXTRACT_ROOT:-$RAW_ROOT/extracted}
LOG_DIR=${LOG_DIR:-outputs/logs/datasets}

mkdir -p "$MANUAL_DIR" "$EXTRACT_ROOT" "$LOG_DIR"
LOG_FILE="$LOG_DIR/tinyperson_manual_extract_$(date +%Y%m%d_%H%M%S).log"

{
  echo "TinyPerson manual extraction started at $(date -Is)"
  echo "Manual download dir: $MANUAL_DIR"
  echo "Extract root: $EXTRACT_ROOT"
  echo
} | tee "$LOG_FILE"

found=0
while IFS= read -r archive; do
  found=1
  case "$archive" in
    *.zip)
      echo "Extracting zip: $archive" | tee -a "$LOG_FILE"
      unzip -n "$archive" -d "$EXTRACT_ROOT" | tee -a "$LOG_FILE"
      ;;
    *.tar|*.tar.gz|*.tgz)
      echo "Extracting tar: $archive" | tee -a "$LOG_FILE"
      tar -xf "$archive" -C "$EXTRACT_ROOT" 2>&1 | tee -a "$LOG_FILE"
      ;;
  esac
done < <(find "$MANUAL_DIR" "$RAW_ROOT" -type f \( -iname "*.zip" -o -iname "*.tar" -o -iname "*.tar.gz" -o -iname "*.tgz" \) | sort -u)

if [[ "$found" == "0" ]]; then
  echo "No archive files found. Put TinyPerson zip/tar files under $MANUAL_DIR and rerun." | tee -a "$LOG_FILE"
  exit 1
fi

image_count=$(find "$RAW_ROOT" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) | wc -l)
json_count=$(find "$RAW_ROOT" -type f -iname "*.json" | wc -l)

{
  echo
  echo "TinyPerson manual extraction finished at $(date -Is)"
  echo "Images found under raw root: $image_count"
  echo "JSON annotations found under raw root: $json_count"
  echo "Next: bash scripts/ubuntu/prepare_tinyperson_dataset.sh"
} | tee -a "$LOG_FILE"
