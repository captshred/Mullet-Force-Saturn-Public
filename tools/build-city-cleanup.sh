#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_CITY_CLEANUP=1
bash tools/build-city-neon.sh "$@"
