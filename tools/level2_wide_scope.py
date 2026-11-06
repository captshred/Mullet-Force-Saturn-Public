"""Exact additive camera/map scope; original audio and preservation locks stay frozen."""
from level2_balanced_scope import balanced_change,balanced_source
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def change(name,before):
 x=json.loads((R/'docs/level2-wide-lock.json').read_text())
 assert x['base_commit']=='78cc4dfa4fac6dcde3d8d21ac9e78ca8337ee75e'
 if name not in x['changes']:return balanced_change(name,before)
 c=x['changes'][name];assert c['before']==before,(name,'unexpected wide-camera baseline')
 return balanced_change(name,c['after'])
def wide_source(name,before):
 x=json.loads((R/'docs/level2-wide-lock.json').read_text())
 if name not in x['changes']:return balanced_source(name,before)
 c=x['changes'][name];assert c['before']['sha256']==before,(name,'unexpected wide-camera source baseline')
 return balanced_source(name,c['after']['sha256'])
