#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Explicit review candidate: the approved wrapper and Actions target stay unchanged.
export MF_CITY_NEON=1
bash tools/build-punch-combo.sh "$@"
