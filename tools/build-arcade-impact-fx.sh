#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_ARCADE_FX=1 MF_PRESERVE_AUDIO=1
python3 tools/validate-arcade-fx.py
bash tools/build-full-gameplay-sfx2.sh "$@"
