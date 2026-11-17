#!/usr/bin/env bash
# Argument: CUE extracted from the approved custom-audio ZIP.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $# == 1 && -f $1 && -f build/mullet-force.cue ]]
baseline_cue=$(realpath "$1")
python3 tools/prepare-level1-refinement-probe.py
core="$PWD/.deps/refinement-yabause/yabause/src/libretro/yabause_libretro.so"
cc -O2 -I.deps/refinement-yabause/yabause/src/libretro/libretro-common/include -Isrc tests/level1_refinement/frontend.c -ldl -o build/refinement-frontend
python3 tools/build-level1-driver-stress.py
captures="$PWD/build/refinement"
run_capture(){
 local name=$1 cue=$2 frames=$3 scenario=$4
 mkdir -p "$captures/$name"
 MF_AUDIO_TRACE="$captures/$name/events.csv" MF_AUDIO_STEMS="$captures/$name/stems" build/refinement-frontend "$core" "$cue" "$captures/$name" "$frames" "$scenario"
}
run_capture compare-before "$baseline_cue" 15500 combat
run_capture compare-final "$PWD/build/mullet-force.cue" 15500 combat
run_capture driver-stress-capture "$PWD/build/refinement-driver-stress/game.cue" 15500 music
run_capture transition-before "$baseline_cue" 4800 transition
run_capture transition-after "$PWD/build/mullet-force.cue" 4800 transition
python3 tools/analyze-level1-refinement.py "$captures"
