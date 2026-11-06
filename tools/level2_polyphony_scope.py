"""Exact additive source-only authorization from a5e524d; no asset exceptions."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
BASE='a5e524dbd774cdb502f38f36c9ab12149c9498c1'
BEFORE={
 'src/wingsuit_audio.c':'979537d985238335f46b7fba58444ec977635eb2c81d88f84a98216c21fce6d2',
 'src/wingsuit_audio.h':'819bda78e1cc7c891f90e4fbb1bdd3c9d032d887baa101e74c8a66e1f376a5fc',
 'src/wingsuit_runtime.c':'b2f02febc0ccd8562bb59f4d0bbd3c4e0be1d55597da4082fc8899cde9d9e65f'}
def lock():
 x=json.loads((R/'docs/level2-polyphony-lock.json').read_text())
 assert x['base_commit']==BASE and set(x['sources'])==set(BEFORE)
 assert {n:c['before'] for n,c in x['sources'].items()}==BEFORE
 assert not x.get('asset_exceptions')
 return x
def poly_source(name,before):
 if name not in BEFORE:return before
 c=lock()['sources'][name];assert c['before']==before,(name,'unexpected polyphony baseline')
 return c['after']
