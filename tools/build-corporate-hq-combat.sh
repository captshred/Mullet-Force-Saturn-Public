#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_CP_HQ_COMBAT=1
bash tools/build-custom-combat.sh "$@"
