"""Exact additive exceptions for the authorized split Flame bank and transport."""
from level2_wide_scope import change
from pathlib import Path
import json
from level2_polyphony_scope import poly_source
R=Path(__file__).resolve().parents[1]
def lock():
    x=json.loads((R/'docs/level2-split-flame-lock.json').read_text())
    assert x['base_commit']=='b0bd392faec051785c33d794a15efb49805da6e7'
    assert set(x['sources'])=={'src/wingsuit_audio.c','src/wingsuit_audio.h','src/wingsuit_audio_data.h','src/wingsuit_runtime.c'}
    assert set(x['files'])=={'assets/wingsuit/'+n for n in ['WDEATH.MAP','WDEATH.TON','audio.json','flame-audio.json','manifest.json']}
    return x

def split_source(name,before):
    x=lock()
    if name not in x['sources']:return before
    c=x['sources'][name];assert c['before']==before,(name,'unexpected split source baseline')
    return poly_source(name,c['after'])

def split_file(name,before):
    x=lock()
    if name not in x['files']:return change(name,before)
    c=x['files'][name];assert c['before']==before,(name,'unexpected split asset baseline')
    return change(name,c['after'])
