#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_FAST_RUNNING_BAT=1
bash tools/build-run-waist-seam.sh "$@"
