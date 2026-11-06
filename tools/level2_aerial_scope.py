"""Exact top-down art exceptions from the approved camera, not the rejected art."""
from level2_night_scope import night_change,night_source
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def aerial_lock():
 x=json.loads((R/'docs/level2-topdown-v2-lock.json').read_text())
 assert x['base_commit']=='8504ddf8c9c04363862cb1e2cd3e068c0199d39e'
 return x
def aerial_change(name,before):
 x=aerial_lock()
 if name not in x['changes']:return night_change(name,before)
 c=x['changes'][name];assert c['before']==before,(name,'unexpected aerial-art baseline')
 return night_change(name,c['after'])
def aerial_source(name,before):
 x=aerial_lock()
 if name not in x['changes']:return night_source(name,before)
 c=x['changes'][name];assert c['before']['sha256']==before,(name,'unexpected aerial-art source baseline')
 return night_source(name,c['after']['sha256'])
