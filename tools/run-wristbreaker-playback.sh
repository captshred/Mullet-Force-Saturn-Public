#!/usr/bin/env bash
# Requires a built game and a CUE extracted from the approved17445 playtest ZIP.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $# == 1 && -f $1 && -f build/mullet-force.cue ]]
baseline_cue=$(realpath "$1")
python3 tools/prepare-level1-refinement-probe.py
core="$PWD/.deps/refinement-yabause/yabause/src/libretro/yabause_libretro.so"
cc -O2 -I.deps/refinement-yabause/yabause/src/libretro/libretro-common/include -Isrc tests/wristbreaker/frontend.c -ldl -o build/wristbreaker-frontend
python3 tools/build-wristbreaker-driver-stress.py --baseline
python3 tools/build-wristbreaker-driver-stress.py
python3 tools/build-wristbreaker-driver-stress.py --music-only
captures="$PWD/build/wristbreaker-captures"
run_capture(){
 local name=$1 cue=$2 frames=$3 scenario=$4
 mkdir -p "$captures/$name"
 MF_AUDIO_TRACE="$captures/$name/events.csv" MF_AUDIO_STEMS="$captures/$name/stems" build/wristbreaker-frontend "$core" "$cue" "$captures/$name" "$frames" "$scenario"
}
run_capture capture-before "$baseline_cue" 14000 l2-combat
run_capture capture-after "$PWD/build/mullet-force.cue" 14000 l2-combat
run_capture capture-stress-before "$PWD/build/wristbreaker-driver-stress-before/game.cue" 11500 music
run_capture capture-stress "$PWD/build/wristbreaker-driver-stress/game.cue" 11500 music
run_capture capture-music "$PWD/build/wristbreaker-music-only/game.cue" 11500 music
run_capture capture-restart "$PWD/build/mullet-force.cue" 7200 l2-restart
python3 tools/analyze-wristbreaker-playback.py "$captures"
