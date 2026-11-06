"""Exact additive enemy pass; the approved night baseline is never rewritten."""
from pathlib import Path
import json
from level2_turret_scope import turret_change,turret_hash
R=Path(__file__).resolve().parents[1]
def enemy_lock():
 x=json.loads((R/'docs/level2-enemy-lock.json').read_text())
 x['runtime_sections']={k:turret_hash(v) for k,v in x['runtime_sections'].items()}
 return x
def enemy_change(name,before,sha_only=False):
 c=enemy_lock()['changes'].get(name)
 if c is None:return turret_change(name,before,sha_only)
 assert c['before']['sha256']==before['sha256'],(name,'enemy baseline')
 if not sha_only:assert c['before']==before,(name,'enemy baseline size')
 return turret_change(name,c['after'],sha_only)
