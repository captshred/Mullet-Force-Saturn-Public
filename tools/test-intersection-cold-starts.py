#!/usr/bin/env python3
"""Approved repeat-boot/Level2 suite plus actual CPU decode-cache retirement."""
from pathlib import Path
source=(Path(__file__).with_name('test-ricky-playable-runtime.py')).read_text()
source=source.replace("phase=[v for k,v in s.items() if k.startswith('_phase.lto_priv.') and ws-256<v<ws];assert len(phase)==1", "phase=[min((abs(v-address(s,'_failed_reason')),v) for k,v in s.items() if k.startswith('_phase.lto_priv.'))[1]]")
source=source.replace("str(unit),'-ldl'", "f'-DMF_BACKGROUND_CACHE={address(s,\"_world_block_cache\")}',str(unit),'-ldl'")
needle='v=read32(ram,MF_SPRITE_COUNT);fwrite(&v,4,1,full_trace);'
assert source.count(needle)==1
source=source.replace(needle,needle+'\n if(ws_phase>=1 && read32(ram,MF_BACKGROUND_CACHE)){fprintf(stderr,"Background cache survived Stage2 handoff\\\\n");exit(6);}\n')
exec(compile(source,str(Path(__file__).with_name('test-ricky-playable-runtime.py')),'exec'))
