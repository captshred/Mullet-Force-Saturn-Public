#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_BAT_MOMENTUM=1
bash tools/build-combat-review.sh
