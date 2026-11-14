#!/usr/bin/env python3
"""Cold-start/Stage2 tests check both compressed owner and decode suffix retire."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'tools/test-intersection-cold-starts.py').read_text()
s=s.replace("exec(compile(source,",'''source=source.replace("str(unit),'-ldl'", "f'-DMF_BACKGROUND_OWNER={address(s,\\\"_world_packed\\\")}',str(unit),'-ldl'")
source=source.replace('v=read32(ram,MF_SPRITE_COUNT);fwrite(&v,4,1,full_trace);','v=read32(ram,MF_SPRITE_COUNT);fwrite(&v,4,1,full_trace); if(ws_phase>=1 && read32(ram,MF_BACKGROUND_OWNER))exit(7);')
exec(compile(source,''')
exec(compile(s,str(R/'tools/test-intersection-cold-starts.py'),'exec'))
