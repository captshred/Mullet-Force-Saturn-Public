"""Exact source-only readiness fix; all prior gameplay/audio asset locks stay intact."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def ready_lock():return json.loads((R/'docs/level2-ready-lock.json').read_text())
def ready_change(name,before,sha_only=False):
 c=ready_lock()['changes'].get(name)
 if c is None:return before
 assert c['before']['sha256']==before['sha256'],(name,'ready-fix baseline')
 if not sha_only:assert c['before']==before,(name,'ready-fix baseline size')
 return c['after']

def ready_hash(before):return ready_lock()['section_updates'].get(before,before)
