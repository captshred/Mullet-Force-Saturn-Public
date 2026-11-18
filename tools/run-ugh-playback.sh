#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/prepare-ugh-probe.py
core="$PWD/.deps/refinement-yabause/yabause/src/libretro/yabause_libretro.so"
cc -O2 -I.deps/refinement-yabause/yabause/src/libretro/libretro-common/include -Isrc tests/ugh/frontend.c -ldl -o build/ugh-frontend
python3 tools/build-ugh-driver.py
python3 tools/build-ugh-baseline-driver.py
python3 tools/build-ugh-stress.py
captures="$PWD/build/ugh-captures"
run_capture(){
 local name=$1 cue=$2 frames=$3 scenario=$4
 mkdir -p "$captures/$name"
 MF_AUDIO_TRACE="$captures/$name/events.csv" MF_AUDIO_STEMS="$captures/$name/stems" build/ugh-frontend "$core" "$cue" "$captures/$name" "$frames" "$scenario"
}
run_capture before-driver "$PWD/build/ugh-baseline-driver/game.cue" 2700 music
run_capture native-driver "$PWD/build/ugh-driver/game.cue" 16000 music
run_capture gameplay "$PWD/build/mullet-force.cue" 8000 combat
run_capture transition2 "$PWD/build/mullet-force.cue" 8000 pause-short
MF_UGH_SKIP_FRAME=2930 run_capture early-transition "$PWD/build/mullet-force.cue" 8000 pause-short
run_capture stress "$PWD/build/ugh-stress/game.cue" 14000 music
python3 tools/analyze-ugh-playback.py "$captures"
python3 tools/analyze-ugh-combat.py "$captures"
