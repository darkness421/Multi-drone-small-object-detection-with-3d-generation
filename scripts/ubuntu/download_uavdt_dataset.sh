#!/usr/bin/env bash
set -euo pipefail

OUT_DIR=${OUT_DIR:-data/raw/downloads/uavdt}
RAW_ROOT=${RAW_ROOT:-data/raw/UAVDT}
MIN_FREE_GB=${MIN_FREE_GB:-35}
DOWNLOAD_BENCHMARK=${DOWNLOAD_BENCHMARK:-1}
DOWNLOAD_TOOLKIT=${DOWNLOAD_TOOLKIT:-1}
DOWNLOAD_ATTRS=${DOWNLOAD_ATTRS:-1}
EXTRACT=${EXTRACT:-0}
EXTRACT_DIR=${EXTRACT_DIR:-data/raw/UAVDT/_official_extract}

cd "$(dirname "$0")/../.."

mkdir -p "$OUT_DIR" "$RAW_ROOT" outputs/logs/server_baselines

free_gb=$(df -BG . | awk 'NR==2 {gsub("G","",$4); print $4}')
if [[ "${free_gb:-0}" -lt "$MIN_FREE_GB" ]]; then
  echo "Not enough free disk space: ${free_gb}GB available, ${MIN_FREE_GB}GB required."
  exit 1
fi

download_one() {
  local label=$1
  local file_id=$2
  local out_file=$3

  echo "== Downloading ${label} =="
  echo "target: ${out_file}"
  python -m gdown --continue "$file_id" -O "$out_file"
  ls -lh "$out_file"
}

if [[ "$DOWNLOAD_BENCHMARK" == "1" ]]; then
  download_one "UAVDT benchmark images/video frames" \
    "1m8KA6oPIRK_Iwt9TYFquC87vBc_8wRVc" \
    "$OUT_DIR/UAV-benchmark-M.zip"
fi

if [[ "$DOWNLOAD_TOOLKIT" == "1" ]]; then
  download_one "UAVDT DET/MOT toolkit and annotations" \
    "19498uJd7T9w4quwnQEy62nibt3uyT9pq" \
    "$OUT_DIR/UAV-benchmark-MOTD_v1.0.zip"
fi

if [[ "$DOWNLOAD_ATTRS" == "1" ]]; then
  download_one "UAVDT attributes" \
    "1qjipvuk3XE3qU3udluQRRcYuiKzhMXB1" \
    "$OUT_DIR/M_attr.zip"
fi

echo "== Downloaded files =="
find "$OUT_DIR" -maxdepth 1 -type f -printf "%s %p\n" | sort -nr

if [[ "$EXTRACT" == "1" ]]; then
  mkdir -p "$EXTRACT_DIR"
  for zip_file in "$OUT_DIR"/*.zip; do
    [[ -f "$zip_file" ]] || continue
    echo "== Extracting $zip_file to $EXTRACT_DIR =="
    unzip -qn "$zip_file" -d "$EXTRACT_DIR"
  done
  echo "== Extracted top-level structure =="
  find "$EXTRACT_DIR" -maxdepth 3 -type d | sort | head -n 120
fi

echo "UAVDT download step complete at $(date -Is)"
echo "Next, inspect/extract and prepare:"
echo "  EXTRACT=1 bash scripts/ubuntu/download_uavdt_dataset.sh"
echo "  SOURCE=data/raw/UAVDT/_official_extract bash scripts/ubuntu/prepare_uavdt_dataset.sh"
