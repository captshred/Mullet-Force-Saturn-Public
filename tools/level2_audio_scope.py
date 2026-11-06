"""Exact before/after exceptions for the authorized three-file Level 2 audio bank."""
from pathlib import Path
import json
from level2_sustain_scope import sustain_source
from level2_split_scope import split_source,split_file
R=Path(__file__).resolve().parents[1]
def audio_asset(name,before):
 lock=json.loads((R/'docs/level2-audio-bank-lock.json').read_text())
 assert lock['base_commit']=='c721fa189043e66ee6292398ef3fcddbb692063a'
 assert set(lock['files'])=={'WDEATH.MAP','WDEATH.SEQ','WDEATH.TON'}
 if name not in lock['files']:return before
 change=lock['files'][name];assert change['before']==before,(name,'unexpected audio baseline')
 return split_file('assets/wingsuit/'+name,change['after'])
def audio_source(name,before):
 lock=json.loads((R/'docs/level2-audio-bank-lock.json').read_text())
 assert lock['base_commit']=='c721fa189043e66ee6292398ef3fcddbb692063a'
 assert set(lock['sources'])=={'src/wingsuit_audio.c','src/wingsuit_audio.h','src/wingsuit_audio_data.h'}
 if name not in lock['sources']:return before
 change=lock['sources'][name];assert change['before']==before,(name,'unexpected audio source baseline')
 value=change['after']
 repair=json.loads((R/'docs/level2-audio-e108-source-lock.json').read_text())
 assert repair['base_commit']=='4a42eea5ad2f3ee6aa768256e0d31988903f9570'
 assert set(repair['sources'])=={'src/wingsuit_audio.c','src/wingsuit_audio.h','src/wingsuit_runtime.c'}
 if name in repair['sources']:
  c=repair['sources'][name];assert c['before']==value,(name,'unexpected repair baseline');value=c['after']
 return split_source(name,sustain_source(name,value))
