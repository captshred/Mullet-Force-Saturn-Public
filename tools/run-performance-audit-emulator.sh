#!/usr/bin/env bash
# Pinned HLE smoke replay. The probe reads emulated work RAM and counts draw commands.
set -euo pipefail
cd "$(dirname "$0")/.."
pin=8926b0c6c347f8c5c755911ddb0ac695420ffbf8
core=.deps/performance-yabause
if [[ ! -d $core/.git ]]; then
    git clone "${MF_YABAUSE_REPO:-https://github.com/libretro/yabause.git}" "$core"
fi
git -C "$core" checkout --detach "$pin"
python3 - "$core" <<'PY'
from pathlib import Path
import subprocess
import sys

core = Path(sys.argv[1])
def original(name):
    return subprocess.check_output(["git", "-C", str(core), "show", f"HEAD:{name}"], text=True)

name = "yabause/src/libretro/libretro.c"
(core / name).write_text(original(name) + """
extern unsigned mf_probe_draws, mf_probe_primitives;
unsigned retro_mf_perf_read(unsigned addr) {
   return MappedMemoryReadLongNocache(MSH2, addr);
}
unsigned retro_mf_perf_draws(void) { return mf_probe_draws; }
unsigned retro_mf_perf_primitives(void) { return mf_probe_primitives; }
""")
name = "yabause/src/vdp1.c"
text = original(name)
text = text.replace("void Vdp1DrawCommands(u8", "unsigned mf_probe_draws, mf_probe_primitives;\n\nvoid Vdp1DrawCommands(u8", 1)
text = text.replace("   u32 returnAddr = 0xffffffff;", "   u32 returnAddr = 0xffffffff;\n   ++mf_probe_draws;", 1)
text = text.replace("         switch (command & 0x000F) {",
                    "         if ((command & 0x000F) <= 7) ++mf_probe_primitives;\n"
                    "         switch (command & 0x000F) {", 1)
(core / name).write_text(text)
PY
make -C "$core/yabause/src/libretro" -j4
cc -std=c99 -O2 -Wall -Wextra -Werror -DMF_PERFORMANCE_AUDIT=1 \
    -I"$core/yabause/src/libretro/libretro-common/include" -Isrc \
    tests/runtime/performance-audit-frontend.c -ldl -o build/performance-audit-frontend
mapfile -t addresses < <(awk '$2=="mf_perf_latest" {print $1}' build/game.map)
[[ ${#addresses[@]} == 1 ]] || { echo "Build with MF_PERFORMANCE_AUDIT=1 first." >&2; exit 1; }
build/performance-audit-frontend "$PWD/$core/yabause/src/libretro/yabause_libretro.so" \
    "$PWD/build/mullet-force.cue" "${addresses[0]}" "${1:-5200}" "${2:-walk}" > "${3:-build/performance-audit.csv}"
