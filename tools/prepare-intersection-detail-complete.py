#!/usr/bin/env python3
"""Unchanged block/LZ/Huffman encoder; report heap owner vs static storage accurately."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];script=R/'tools/prepare-level1-intersection.py'
s=script.read_text().replace("D=R/'docs/level1-intersection-phase3a'", "D=R/'docs/intersection-detail-complete'")
exec(compile(s,str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
p=R/'assets/level1-intersection/manifest.json';m=json.loads(p.read_text());m['static_CPU_bytes']-=m['packed_source_bytes'];m['packed_source_storage']='existing-fixed-Jo-heap';m['packed_heap_storage_bytes']=(m['packed_source_bytes']+7)&~3;m['background_heap_bytes']=m['packed_heap_storage_bytes']+m['decode_cache_heap_bytes'];m['heap_capacity_bytes']=393216
p.write_text(json.dumps(m,indent=2)+'\n')
assert m['background_heap_bytes']+16384<393216,'insufficient fixed heap room for load-time map transfer'
