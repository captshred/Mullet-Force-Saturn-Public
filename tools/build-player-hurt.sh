#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_PLAYER_HURT=1
bash tools/build-corporate-hq-combat.sh "$@"
