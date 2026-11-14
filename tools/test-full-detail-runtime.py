#!/usr/bin/env python3
"""Production traversal with telemetry for the combined background heap owner."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];m=json.loads((R/'assets/level1-intersection/manifest.json').read_text());heap=((m['packed_source_bytes']+7)&~3)+m['decode_cache_heap_bytes']
s=(R/'tools/test-intersection-runtime.py').read_text().replace('68284',str(heap)).replace('68292',str(heap+8)).replace('"_world_block_cache"','"_world_packed"')
s=s.replace('cpu_cache_address=','cpu_background_owner_address=').replace('cpu_cache_allocator_block_bytes=','cpu_background_allocator_block_bytes=').replace('cpu_cache_requested_bytes=','cpu_background_requested_bytes=')
s=s.replace('>=360','>=1100').replace("'3400'","'4400'").replace('3396','4396').replace('360-tick','1100-tick')
s=s.replace('(travel_phase==0 || travel_phase==2)', '(travel_phase==0 || travel_phase==2 || (travel_phase==1 && port && frame%180<3))').replace('travel_phase==4)return 1;', '(travel_phase==4 || (travel_phase==1 && !port && frame%180<3)))return 1;').replace('(travel_phase==1 || travel_phase==3 ||', '((travel_phase==1 && frame%180>=3) || travel_phase==3 ||')
exec(compile(s,str(R/'tools/test-intersection-runtime.py'),'exec'))
