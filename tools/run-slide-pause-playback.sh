#!/usr/bin/env bash
# Argument: CUE extracted from the approved D97 Wristbreaker playtest ZIP.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $# == 1 && -f $1 && -f build/mullet-force.cue ]]
baseline_cue=$(realpath "$1")
python3 tools/prepare-level1-refinement-probe.py
core="$PWD/.deps/refinement-yabause/yabause/src/libretro/yabause_libretro.so"
cc -O2 -I.deps/refinement-yabause/yabause/src/libretro/libretro-common/include -Isrc tests/slide_pause/frontend.c -ldl -o build/slide-pause-frontend
python3 tools/build-wristbreaker-driver-stress.py
python3 tools/build-slide-pause-driver.py
captures="$PWD/build/slide-pause-captures"
run_capture(){
 local name=$1 cue=$2 frames=$3 scenario=$4
 mkdir -p "$captures/$name"
 MF_AUDIO_TRACE="$captures/$name/events.csv" MF_AUDIO_STEMS="$captures/$name/stems" build/slide-pause-frontend "$core" "$cue" "$captures/$name" "$frames" "$scenario"
}
run_capture pause-loop "$PWD/build/mullet-force.cue" 19000 pause-loop
run_capture pause-loop-repeat "$PWD/build/mullet-force.cue" 19000 pause-loop
run_capture pause-loop-baseline "$baseline_cue" 19000 pause-loop
run_capture baseline-late "$baseline_cue" 19000 late-transition
run_capture pause-short "$PWD/build/mullet-force.cue" 6000 pause-short
run_capture pause-driver "$PWD/build/slide-pause-driver/game.cue" 15500 music
run_capture level2-after "$PWD/build/mullet-force.cue" 14000 l2-combat
run_capture level2-stress "$PWD/build/wristbreaker-driver-stress/game.cue" 11500 music
# Existing independent native analyzer: validate each current Level2 capture.
python3 - "$captures" <<'PY'
from pathlib import Path
import sys,json
p=Path('tools/analyze-wristbreaker-playback.py').resolve();scope={'__file__':str(p)}
exec(compile(p.read_text().split('result=dict(baseline=BASE,')[0],str(p),'exec'),scope)
out={n:scope['analyze'](n,False) for n in ('level2-after','level2-stress')}
for v in out.values():assert v['missing_or_reordered_note_ons']==v['global_music_interruptions']==v['cross_control_music_steals']==v['ordinary_one_shot_tails_cut']==v['clipped_samples']==0
(Path(sys.argv[1])/'level2-playback.json').write_text(json.dumps(out,indent=2)+'\n')
PY
python3 tools/analyze-slide-pause.py "$captures"
