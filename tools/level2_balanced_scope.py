"""Exact additive 320px refinement scope; all artwork and audio stay frozen."""
from level2_timing_scope import timing_change,timing_source
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def balanced_change(name,before):
 x=json.loads((R/'docs/level2-balanced-lock.json').read_text())
 assert x['base_commit']=='a827c2ec82fddaade0bd8e1c627f75ec9905705c'
 if name not in x['changes']:return timing_change(name,before)
 c=x['changes'][name];assert c['before']==before,(name,'unexpected balanced-scroll baseline')
 return timing_change(name,c['after'])
def balanced_source(name,before):
 x=json.loads((R/'docs/level2-balanced-lock.json').read_text())
 if name not in x['changes']:return timing_source(name,before)
 c=x['changes'][name];assert c['before']['sha256']==before,(name,'unexpected balanced-scroll source baseline')
 return timing_source(name,c['after']['sha256'])
