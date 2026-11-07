"""Exact additive scheduling exceptions; retain every prior preservation lock."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def timing_change(name,before):
 x=json.loads((R/'docs/level2-sfx-timing-lock.json').read_text())
 assert x['base_commit']=='8504ddf8c9c04363862cb1e2cd3e068c0199d39e'
 if name not in x['changes']:return before
 c=x['changes'][name];assert c['before']==before,(name,'unexpected timing baseline')
 return c['after']
def timing_source(name,before):
 x=json.loads((R/'docs/level2-sfx-timing-lock.json').read_text())
 if name not in x['changes']:return before
 c=x['changes'][name];assert c['before']['sha256']==before,(name,'unexpected timing source baseline')
 return c['after']['sha256']
