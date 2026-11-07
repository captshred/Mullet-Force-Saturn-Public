#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash tools/build-source-complete.sh "$@"
