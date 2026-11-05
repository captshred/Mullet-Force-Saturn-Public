#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_DEV_STAGE_SKIP=${MF_DEV_STAGE_SKIP:-1}
export MF_LEVEL2_WINGSUIT=1 MF_LEVEL1_STAGE_CLEAR=1 MF_PRESERVE_AUDIO=1
python3 tools/validate-wingsuit.py
bash tools/build-level1-stage-clear.sh "$@"
