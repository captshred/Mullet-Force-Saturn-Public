#!/usr/bin/env bash
# Fresh x86-64 Debian/Ubuntu Codex environment. Does not install a new compiler:
# setup.sh fetches the exact upstream SDK and bundled SH-2 compiler revision.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $(uname -m) == x86_64 ]] || { echo 'Use an x86-64 Linux environment (bundled compiler requirement).' >&2; exit 1; }
command -v apt-get >/dev/null || { echo 'Install README dependencies manually on this distribution.' >&2; exit 1; }
privilege=()
if [[ $(id -u) != 0 ]]; then
    command -v sudo >/dev/null || { echo 'An administrator must install the README apt packages.' >&2; exit 1; }
    privilege=(sudo)
fi
"${privilege[@]}" apt-get update
"${privilege[@]}" apt-get install -y --no-install-recommends \
    ca-certificates git make gcc libc6-dev python3 genisoimage libmpfr6 libmpc3 ffmpeg python3-pil
bash tools/setup.sh
.deps/joengine/Compiler/LINUX/bin/sh-none-elf-gcc-8.2.0 --version | head -n 1
printf '\nSetup complete. Run: make native && make check\n'
printf 'Docker is optional; if already installed and running, make uses the pinned container.\n'
