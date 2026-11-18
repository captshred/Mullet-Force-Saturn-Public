#!/usr/bin/env python3
"""Extend the existing SHA-pinned read-only observer with the native ECNT field."""
from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[1]
subprocess.run(['python3','tools/prepare-level1-refinement-probe.py'],cwd=R,check=True)
core=R/'.deps/refinement-yabause';p=core/'yabause/src/scsp.c';s=p.read_text();a='case 4:return s->tl;default:return (unsigned)s->env;';assert s.count(a)==1
p.write_text(s.replace(a,'case 4:return s->tl;case 6:return (unsigned)s->ecnt;default:return (unsigned)s->env;'))
subprocess.run(['make','-C',str(core/'yabause/src/libretro'),'-j2'],check=True)
