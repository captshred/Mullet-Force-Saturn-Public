#!/usr/bin/env python3
"""Read-only native scale-review run, extended normal combat to capture Ricky."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
m=json.loads((R/'assets/level1-intersection/manifest.json').read_text());heap=m['decode_cache_heap_bytes']
s=(R/'tools/test-intersection-runtime.py').read_text().replace('68284',str(heap)).replace('68292',str(heap+8))
s=s.replace('>=360','>=1100').replace("'3400'","'4400'").replace('3396','4396')
s=s.replace('(travel_phase==0 || travel_phase==2)', '(travel_phase==0 || travel_phase==2 || (travel_phase==1 && port && frame%180<3))')
s=s.replace('travel_phase==4)return 1;', '(travel_phase==4 || (travel_phase==1 && !port && frame%180<3)))return 1;')
s=s.replace('(travel_phase==1 || travel_phase==3 ||', '((travel_phase==1 && frame%180>=3) || travel_phase==3 ||')
exec(compile(s,str(R/'tools/test-intersection-runtime.py'),'exec'))
