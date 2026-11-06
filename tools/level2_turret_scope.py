"""Exact additive changes from approved Chrome Eye build; prior locks stay frozen."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def turret_lock():
 return json.loads((R/'docs/level2-turret-lock.json').read_text())
def turret_change(name,before,sha_only=False):
 c=turret_lock()['changes'].get(name)
 if c is None:return before
 assert c['before']['sha256']==before['sha256'],(name,'turret baseline')
 if not sha_only:assert c['before']==before,(name,'turret baseline size')
 return c['after']
def turret_hash(before):
 return turret_lock()['section_updates'].get(before,before)
