#!/usr/bin/env bash
# Detect total memory and print recommended RAM disk size as 1/3 of total memory.
# Output is formatted as e.g. "2048M" or "2G" suitable for tmpfs size= option.

set -euo pipefail

if [ ! -r /proc/meminfo ]; then
  echo "Cannot read /proc/meminfo" >&2
  exit 2
fi

mem_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
if [ -z "$mem_kb" ]; then
  echo "Failed to detect total memory" >&2
  exit 2
fi

mem_mb=$((mem_kb/1024))
# compute one-third
ram_third_mb=$((mem_mb/3))

if [ "$ram_third_mb" -ge 1024 ]; then
  # print in gigabytes rounding down
  printf "%dG\n" $((ram_third_mb/1024))
else
  printf "%dM\n" "$ram_third_mb"
fi
