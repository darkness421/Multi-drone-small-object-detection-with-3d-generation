#!/usr/bin/env bash
set -euo pipefail

RESOURCE_PATH=${RESOURCE_PATH:-$PWD}
MIN_FREE_GB=${MIN_FREE_GB:-100}
MAX_DISK_USE_PERCENT=${MAX_DISK_USE_PERCENT:-92}
MIN_RAM_GB=${MIN_RAM_GB:-16}
MIN_GPU_FREE_GB=${MIN_GPU_FREE_GB:-6}
GPU_ID=${GPU_ID:-}
GUARD_WAIT_SECONDS=${GUARD_WAIT_SECONDS:-60}
GUARD_MAX_RETRIES=${GUARD_MAX_RETRIES:-0}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)
      RESOURCE_PATH=$2
      shift 2
      ;;
    --gpu)
      GPU_ID=$2
      shift 2
      ;;
    --min-free-gb)
      MIN_FREE_GB=$2
      shift 2
      ;;
    --max-disk-use-percent)
      MAX_DISK_USE_PERCENT=$2
      shift 2
      ;;
    --min-ram-gb)
      MIN_RAM_GB=$2
      shift 2
      ;;
    --min-gpu-free-gb)
      MIN_GPU_FREE_GB=$2
      shift 2
      ;;
    --wait-seconds)
      GUARD_WAIT_SECONDS=$2
      shift 2
      ;;
    --max-retries)
      GUARD_MAX_RETRIES=$2
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

gb_from_kb() {
  awk -v value="$1" 'BEGIN { printf "%.1f", value / 1024 / 1024 }'
}

gb_from_mib() {
  awk -v value="$1" 'BEGIN { printf "%.1f", value / 1024 }'
}

ge_float() {
  awk -v left="$1" -v right="$2" 'BEGIN { exit !(left >= right) }'
}

attempt=0
while true; do
  reasons=()
  disk_line=$(df -Pk "$RESOURCE_PATH" | awk 'NR == 2 { print $4, $5 }')
  disk_free_kb=${disk_line%% *}
  disk_use_pct=${disk_line##* }
  disk_use_pct=${disk_use_pct%%%}
  disk_free_gb=$(gb_from_kb "$disk_free_kb")
  if ! ge_float "$disk_free_gb" "$MIN_FREE_GB"; then
    reasons+=("disk_free=${disk_free_gb}GB < ${MIN_FREE_GB}GB")
  fi
  if [[ "$disk_use_pct" -gt "$MAX_DISK_USE_PERCENT" ]]; then
    reasons+=("disk_use=${disk_use_pct}% > ${MAX_DISK_USE_PERCENT}%")
  fi

  mem_available_kb=$(awk '/MemAvailable:/ { print $2 }' /proc/meminfo)
  mem_available_gb=$(gb_from_kb "$mem_available_kb")
  if ! ge_float "$mem_available_gb" "$MIN_RAM_GB"; then
    reasons+=("ram_available=${mem_available_gb}GB < ${MIN_RAM_GB}GB")
  fi

  gpu_free_gb="-"
  if [[ -n "$GPU_ID" ]]; then
    gpu_free_mib=$(nvidia-smi --id="$GPU_ID" --query-gpu=memory.free --format=csv,noheader,nounits | head -n 1 | tr -d ' ')
    gpu_free_gb=$(gb_from_mib "$gpu_free_mib")
    if ! ge_float "$gpu_free_gb" "$MIN_GPU_FREE_GB"; then
      reasons+=("gpu${GPU_ID}_free=${gpu_free_gb}GB < ${MIN_GPU_FREE_GB}GB")
    fi
  fi

  if [[ ${#reasons[@]} -eq 0 ]]; then
    echo "RESOURCE_OK path=$RESOURCE_PATH disk_free=${disk_free_gb}GB disk_use=${disk_use_pct}% ram_available=${mem_available_gb}GB gpu=${GPU_ID:-none} gpu_free=${gpu_free_gb}GB"
    exit 0
  fi

  echo "RESOURCE_WAIT $(date -Is) ${reasons[*]}" >&2
  attempt=$((attempt + 1))
  if [[ "$GUARD_MAX_RETRIES" -gt 0 && "$attempt" -ge "$GUARD_MAX_RETRIES" ]]; then
    echo "RESOURCE_FAILED after $attempt checks: ${reasons[*]}" >&2
    exit 1
  fi
  sleep "$GUARD_WAIT_SECONDS"
done
