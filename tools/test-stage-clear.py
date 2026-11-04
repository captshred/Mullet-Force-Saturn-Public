#!/usr/bin/env python3
"""Exercise actual damage/spawn/transition paths with the complete gameplay flags."""
from pathlib import Path
import json, subprocess, tempfile
r=Path(__file__).resolve().parents[1]
flags=json.loads((r/'assets/full-gameplay-sfx2/preservation.json').read_text())['profile_flags']
defines=[f'-D{k}={17 if v=="B" else v}' for k,v in flags.items()]
with tempfile.TemporaryDirectory(prefix='mf-stage-clear-') as d:
    exe=Path(d)/'stage'
    subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',*defines,
                    '-DMF_LEVEL1_STAGE_CLEAR=1','-Isrc','tests/stage_clear_test.c',
                    '-o',str(exe)],cwd=r,check=True)
    subprocess.run([str(exe)],cwd=r,check=True)
