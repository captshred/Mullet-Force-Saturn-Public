"""Exact palette/material/CRAM corrections after the top-down V2 revision."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def night_lock():
 x=json.loads((R/'docs/level2-night-lock.json').read_text())
 assert x['base_commit']=='ad83025f3558fd11d934367bb74416e70814339c'
 return x
def night_change(name,before):
 x=night_lock()
 if name not in x['changes']:return before
 c=x['changes'][name];assert c['before']==before,(name,'unexpected night palette baseline')
 return c['after']
def night_source(name,before):
 x=night_lock()
 if name not in x['changes']:return before
 c=x['changes'][name];assert c['before']['sha256']==before,(name,'unexpected night source baseline')
 return c['after']['sha256']
