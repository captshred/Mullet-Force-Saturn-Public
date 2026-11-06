"""Exact additive camera/map scope; original audio and preservation locks stay frozen."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def change(name,before):
 x=json.loads((R/'docs/level2-wide-lock.json').read_text())
 assert x['base_commit']=='78cc4dfa4fac6dcde3d8d21ac9e78ca8337ee75e'
 if name not in x['changes']:return before
 c=x['changes'][name];assert c['before']==before,(name,'unexpected wide-camera baseline')
 return c['after']
def wide_source(name,before):
 x=json.loads((R/'docs/level2-wide-lock.json').read_text())
 if name not in x['changes']:return before
 c=x['changes'][name];assert c['before']['sha256']==before,(name,'unexpected wide-camera source baseline')
 return c['after']['sha256']
