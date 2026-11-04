#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Future stage branches override this checked-in entry point.
bash tools/build-arcade-impact-fx.sh "$@"
