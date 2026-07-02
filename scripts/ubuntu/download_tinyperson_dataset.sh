#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

RAW_ROOT=${RAW_ROOT:-data/raw/TinyPerson}
LOG_DIR=${LOG_DIR:-outputs/logs/datasets}
DRIVE_ID=${TINYPERSON_DRIVE_ID:-1KrH9uEC9q4RdKJz-k34Q6v5hRewU5HOw}
EXTRACT=${EXTRACT:-1}

mkdir -p "$RAW_ROOT" "$LOG_DIR"

summary="$RAW_ROOT/download_summary.txt"
download_dir="$RAW_ROOT/google_drive"
download_file="$RAW_ROOT/tinyperson_official_download"

{
  echo "TinyPerson download started at $(date -Is)"
  echo "Official source: https://github.com/ucas-vg/PointTinyBenchmark/tree/TinyBenchmark"
  echo "Google Drive id: $DRIVE_ID"
  echo "Raw root: $RAW_ROOT"
} | tee "$summary"

if ! command -v gdown >/dev/null 2>&1; then
  echo "ERROR: gdown is required. Install with: pip install gdown" | tee -a "$summary"
  exit 2
fi

mkdir -p "$download_dir"
folder_url="https://drive.google.com/drive/folders/$DRIVE_ID"
file_url="https://drive.google.com/uc?id=$DRIVE_ID"

echo "Trying Google Drive folder download..." | tee -a "$summary"
if gdown --folder --continue "$folder_url" -O "$download_dir"; then
  echo "Folder download finished." | tee -a "$summary"
else
  echo "Folder download failed; trying single-file download..." | tee -a "$summary"
  gdown --continue "$file_url" -O "$download_file"
fi

echo "Downloaded files:" | tee -a "$summary"
find "$RAW_ROOT" -maxdepth 3 -type f -printf "%p\t%s bytes\n" | sort | tee -a "$summary"

if [[ "$EXTRACT" == "1" ]]; then
  extract_root="$RAW_ROOT/extracted"
  mkdir -p "$extract_root"
  while IFS= read -r archive; do
    case "$archive" in
      *.zip)
        echo "Extracting $archive" | tee -a "$summary"
        unzip -n "$archive" -d "$extract_root"
        ;;
      *.tar|*.tar.gz|*.tgz)
        echo "Extracting $archive" | tee -a "$summary"
        tar -xf "$archive" -C "$extract_root"
        ;;
    esac
  done < <(find "$RAW_ROOT" -type f \( -iname "*.zip" -o -iname "*.tar" -o -iname "*.tar.gz" -o -iname "*.tgz" \) | sort)
fi

echo "TinyPerson download/extract finished at $(date -Is)" | tee -a "$summary"
echo "Next: bash scripts/ubuntu/prepare_tinyperson_dataset.sh" | tee -a "$summary"
