"""Exact additive enemy pass; the approved night baseline is never rewritten."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def enemy_lock():
 return json.loads((R/'docs/level2-enemy-lock.json').read_text())
def enemy_change(name,before,sha_only=False):
 c=enemy_lock()['changes'].get(name)
 if c is None:return before
 assert c['before']['sha256']==before['sha256'],(name,'enemy baseline')
 if not sha_only:assert c['before']==before,(name,'enemy baseline size')
 return c['after']
