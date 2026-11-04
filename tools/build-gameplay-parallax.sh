#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_LIVE_CITY_PARALLAX=1
bash tools/build-city-cleanup.sh "$@"
