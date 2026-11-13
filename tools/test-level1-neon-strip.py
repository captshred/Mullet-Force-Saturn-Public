#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='neon-strip-host-') as d:
 exe=Path(d)/'cache'
 subprocess.run(['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-fdata-sections','-include',str(R/'build/build-info.h'),'-I'+str(R/'src'),'-I'+str(R/'build'),'-I'+str(R/'tests/parallax_mock'),str(R/'tests/neon_strip/cache.c'),'-Wl,--gc-sections','-o',str(exe)],check=True)
 subprocess.run([str(exe)],cwd=R,check=True)
 # The approved world/combat tests are still current; their original map test
 # belongs to the old chunk format and is preserved in the archived suite.
 s=(R/'tools/test-world-flow-phase1.py').read_text().replace("('flow','map')","('flow',)")
 exec(compile(s,str(R/'tools/test-world-flow-phase1.py'),'exec'),{'__file__':str(R/'tools/test-world-flow-phase1.py'),'__name__':'__main__'})
 exe=Path(d)/'jump'
 subprocess.run(['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all','-include',str(R/'build/build-info.h'),'-I'+str(R/'src'),'-I'+str(R/'build'),str(R/'tests/ricky/jump-chain.c'),'-o',str(exe)],check=True);subprocess.run([str(exe)],cwd=R,check=True)
