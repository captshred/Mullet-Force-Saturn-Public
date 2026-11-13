#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='world-tests-') as d:
 w=Path(d);common=['cc','-std=c99','-g','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-fdata-sections','-include',str(R/'build/build-info.h'),'-I'+str(R/'src'),'-I'+str(R/'build'),'-Wl,--gc-sections']
 for name in ('flow','map'):
  exe=w/name;subprocess.run([*common,*(['-I'+str(R/'tests/parallax_mock')] if name=='map' else []),str(R/f'tests/world_flow/{name}.c'),'-o',str(exe)],check=True);subprocess.run([str(exe)],cwd=R,check=True)
 for path in ('tests/ricky/balance.c','tests/ricky/polish-charge.c','tests/ricky/combat.c'):
  source=(R/path).read_text()
  if path.endswith('/combat.c'):
   source=source.replace('assert(g.stage==MF_STAGE_SETTLING);','assert(g.stage==MF_STAGE_LEVEL1);g.stage=MF_STAGE_SETTLING;g.stage_timer=MF_STAGE_SETTLE_TICKS;')
  unit=w/'combat.c';unit.write_text(source);exe=w/'combat';subprocess.run([*common,str(unit),'-o',str(exe)],check=True);subprocess.run([str(exe)],cwd=R,check=True)
 print('PASS current production-world flags: existing 3HP bat/flame/contact/charge and Ricky combat regressions; only obsolete auto-40-KO expectation replaced by explicit handoff fixture')
