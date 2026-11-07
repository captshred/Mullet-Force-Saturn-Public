#!/usr/bin/env bash
# Optional native playback comparison; requires gcc/make/git and network setup.
set -euo pipefail
cd "$(dirname "$0")/.."
core=.deps/recovery-yabause
pin=8926b0c6c347f8c5c755911ddb0ac695420ffbf8
if [[ ! -d $core/.git ]]; then git clone https://github.com/libretro/yabause.git "$core"; fi
git -C "$core" checkout --detach "$pin"
# Reset only the two observer files owned by this dedicated test checkout.
git -C "$core" restore yabause/src/scsp.c yabause/src/libretro/libretro.c
cat tests/runtime/recovery-scsp-probe.inc >> "$core/yabause/src/scsp.c"
cat >> "$core/yabause/src/libretro/libretro.c" <<'C'
extern unsigned short SoundRamReadWord(unsigned int);
unsigned retro_recovery_word(unsigned addr){return SoundRamReadWord(addr);}
C
make -C "$core/yabause/src/libretro" -j2
cc -O2 -I"$core/yabause/src/libretro/libretro-common/include" -Isrc tests/runtime/recovery-frontend.c -ldl -o build/recovery-frontend
python3 tools/build-level2-neon-city.py --out build/recovery-golden
mkdir -p build/recovery-golden-playback build/recovery-candidate-playback
lib="$PWD/$core/yabause/src/libretro/yabause_libretro.so"
build/recovery-frontend "$lib" "$PWD/build/recovery-golden/mullet-force.cue" "$PWD/build/recovery-golden-playback" 2200
build/recovery-frontend "$lib" "$PWD/build/mullet-force.cue" "$PWD/build/recovery-candidate-playback" 2200
python3 tools/compare-recovery-emulator.py build/recovery-golden-playback build/recovery-candidate-playback --out build/RECOVERY-EMULATOR.json
