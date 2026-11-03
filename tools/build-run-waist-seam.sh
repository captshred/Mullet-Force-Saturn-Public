#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_PLAYER_RUN_WAIST=1
bash tools/build-chuck-denim-cleanup.sh "$@"
