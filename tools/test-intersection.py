#!/usr/bin/env python3
"""Current production flags: extended cache/world, approved combat and rendering."""
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
def run(args):subprocess.run(args,cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='intersection-tests-') as d:
 common=['cc','-std=c99','-g','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-fdata-sections','-include',str(R/'build/build-info.h'),'-I'+str(R/'src'),'-I'+str(R/'build'),'-Wl,--gc-sections']
 for path in ['tests/intersection/cache.c','tests/intersection/world.c','tests/coop_balance/combat.c','tests/ricky/balance.c','tests/ricky/polish-charge.c','tests/ricky/combat.c','tests/ricky/jump-chain.c','tests/ricky/jump-chain-frequency.c','tests/punch_combo_test.c','tests/bat_command_buffer_test.c']:
  source=(R/path).read_text();unit=Path(d)/Path(path).name;unit.write_text(source);exe=str(Path(d)/('run-'+Path(path).stem))
  if path=='tests/coop_balance/combat.c':unit.write_text(source.replace('camera<=960','camera<=MF_WORLD_CAMERA_MAX'))
  if path=='tests/ricky/jump-chain.c':unit.write_text(source.replace('c<=960','c<=MF_WORLD_CAMERA_MAX').replace('<=1254*256','<=MF_WORLD_RIGHT*256'))
  if path=='tests/ricky/combat.c':unit.write_text(source.replace('assert(g.stage==MF_STAGE_SETTLING);','assert(g.stage==MF_STAGE_LEVEL1);g.stage=MF_STAGE_SETTLING;g.stage_timer=MF_STAGE_SETTLE_TICKS;'))
  if path=='tests/bat_command_buffer_test.c':unit.write_text(source.replace('return original_fast_bat_tests();','return 0;'))
  run([*common,'-I'+str(R/'tests'),*(['-I'+str(R/'tests/parallax_mock')] if path.endswith('/cache.c') else []),str(unit),*(['src/game.c'] if path in ('tests/punch_combo_test.c','tests/bat_command_buffer_test.c') else []),'-o',exe]);run([exe])
 # Reuse the approved three-enemy renderer fixtures against current main/code.
 source=(R/'tools/validate-coop-balance.py').read_text();block=source[source.index(' # Use the production renderer'):]
 exec('\n'.join(line[1:] for line in block.splitlines()))
run(['python3','tools/test-ricky-jump-render.py'])
run(['python3','tools/validate-fire-hit.py'])
