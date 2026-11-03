#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MF_ATTACK_SEQUENCE=1
bash tools/build-bat-momentum.sh
