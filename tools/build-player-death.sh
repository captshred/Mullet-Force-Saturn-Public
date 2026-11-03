#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_PLAYER_DEATH=1
bash tools/build-player-hurt.sh "$@"
