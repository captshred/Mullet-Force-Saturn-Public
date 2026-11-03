#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_CHUCK_DENIM_CLEANUP=1
bash tools/build-player-death.sh "$@"
