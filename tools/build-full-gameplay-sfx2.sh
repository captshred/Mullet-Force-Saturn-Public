#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Fail before building if approved graphics or any superseded audio are restored.
python3 tools/validate-full-gameplay-sfx2.py
export MF_PRESERVE_AUDIO=1
bash tools/build-gameplay-parallax.sh "$@"
