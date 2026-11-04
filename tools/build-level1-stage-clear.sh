#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_LEVEL1_STAGE_CLEAR=1 MF_PRESERVE_AUDIO=1
bash tools/build-arcade-impact-fx.sh "$@"
