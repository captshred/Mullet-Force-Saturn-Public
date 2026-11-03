#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_HQ_TORCH=1 MF_PRESERVE_AUDIO=1
bash tools/build-jab-cohesion.sh
