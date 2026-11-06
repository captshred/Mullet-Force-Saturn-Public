"""Exact, additive source exception for live sustain diagnostics; no asset exception."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def sustain_source(name,before):
    lock=json.loads((R/'docs/level2-flame-sustain-source-lock.json').read_text())
    assert lock['base_commit']=='2cae6ea6e496be85ecaa3253081a251e0a6ac9cc'
    assert set(lock['sources'])=={'src/wingsuit_audio.c','src/wingsuit_audio.h','src/wingsuit_runtime.c'}
    if name not in lock['sources']:return before
    c=lock['sources'][name];assert c['before']==before,(name,'unexpected sustain baseline')
    return c['after']
