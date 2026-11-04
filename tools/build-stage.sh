#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Stage branches own this stable entry point; the Actions interface stays fixed.
bash tools/build-level1-stage-clear.sh "$@"
