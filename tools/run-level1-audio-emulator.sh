#!/usr/bin/env bash
# Optional HLE native-SCSP smoke; all media/logs stay in ignored build/.
set -euo pipefail
cd "$(dirname "$0")/.."
core=.deps/level1-yabause
pin=8926b0c6c347f8c5c755911ddb0ac695420ffbf8
if [[ ! -d $core/.git ]]; then git clone https://github.com/libretro/yabause.git "$core"; fi
git -C "$core" checkout --detach "$pin"
git -C "$core" restore yabause/src/scsp.c yabause/src/libretro/libretro.c
cat tests/runtime/recovery-scsp-probe.inc >> "$core/yabause/src/scsp.c"
cat >> "$core/yabause/src/libretro/libretro.c" <<'C'
extern unsigned short SoundRamReadWord(unsigned int);
unsigned retro_recovery_word(unsigned addr){return SoundRamReadWord(addr);}
C
make -C "$core/yabause/src/libretro" -j2
cc -O2 -I"$core/yabause/src/libretro/libretro-common/include" -Isrc tests/runtime/level1-audio-frontend.c -ldl -o build/level1-frontend
mkdir -p build/level1-playback
build/level1-frontend "$PWD/$core/yabause/src/libretro/yabause_libretro.so" "$PWD/build/mullet-force.cue" "$PWD/build/level1-playback" 15500
python3 tools/analyze-level1-emulator.py
