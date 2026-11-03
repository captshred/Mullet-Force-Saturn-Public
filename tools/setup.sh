#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
revision=556d081146211b6a1cfa6591d70f9487d406758b
sdk=.deps/joengine
if [[ ! -d "$sdk/.git" ]]; then
    mkdir -p .deps
    git clone https://github.com/johannes-fetz/joengine.git "$sdk"
fi
if [[ $(git -C "$sdk" rev-parse HEAD 2>/dev/null || true) != "$revision" ]]; then
    git -C "$sdk" fetch origin "$revision"
    git -C "$sdk" checkout --detach "$revision"
fi
[[ $(git -C "$sdk" rev-parse HEAD) == "$revision" ]]
