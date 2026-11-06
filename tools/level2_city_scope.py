"""Exact additive background-only exceptions after approved balanced camera."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def city_lock():
 x=json.loads((R/'docs/level2-city-lock.json').read_text())
 assert x['base_commit']=='8504ddf8c9c04363862cb1e2cd3e068c0199d39e'
 return x
def city_change(name,before):
 x=city_lock()
 if name not in x['changes']:return before
 c=x['changes'][name];assert c['before']==before,(name,'unexpected city-art baseline')
 return c['after']
def city_source(name,before):
 x=city_lock()
 if name not in x['changes']:return before
 c=x['changes'][name];assert c['before']['sha256']==before,(name,'unexpected city-art source baseline')
 return c['after']['sha256']
