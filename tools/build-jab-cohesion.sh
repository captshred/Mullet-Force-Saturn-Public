#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_JAB_COHESION=1 MF_PRESERVE_AUDIO=1
bash tools/build-attack-sequence.sh
