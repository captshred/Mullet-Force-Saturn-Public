"""Exact additive 320px refinement scope; all artwork and audio stay frozen."""
from level2_aerial_scope import aerial_change,aerial_source
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def balanced_change(name,before):
 x=json.loads((R/'docs/level2-balanced-lock.json').read_text())
 assert x['base_commit']=='a827c2ec82fddaade0bd8e1c627f75ec9905705c'
 if name not in x['changes']:return aerial_change(name,before)
 c=x['changes'][name];assert c['before']==before,(name,'unexpected balanced-scroll baseline')
 return aerial_change(name,c['after'])
def balanced_source(name,before):
 x=json.loads((R/'docs/level2-balanced-lock.json').read_text())
 if name not in x['changes']:return aerial_source(name,before)
 c=x['changes'][name];assert c['before']['sha256']==before,(name,'unexpected balanced-scroll source baseline')
 return aerial_source(name,c['after']['sha256'])
