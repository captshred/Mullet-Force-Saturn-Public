"""Verify the complete approved baseline plus narrow SFX scheduling changes."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
def digest(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def validate():
 x=json.loads((R/'docs/level2-sfx-timing-lock.json').read_text())
 assert x['base_commit']=='8504ddf8c9c04363862cb1e2cd3e068c0199d39e'
 assert set(x['changes'])=={'src/wingsuit_audio.c','src/wingsuit_audio.h','tests/wingsuit_audio_test.c','tools/level2_balanced_scope.py','tools/validate-level2-wide.py','tools/validate-level2-audio.py'}
 for n,e in x['frozen'].items():assert digest((R/n).read_bytes())==e,n
 for n,e in x['changes'].items():assert digest((R/n).read_bytes())==e['after'],n
 for n,e in x['added'].items():assert digest((R/n).read_bytes())==e,n
 s=(R/'src/wingsuit_audio.c').read_text()
 for label,(start,end) in x['preserved_sections'].items():
  a=s.index(start);b=s.index(end,a)
  assert hashlib.sha256(s[a:b].encode()).hexdigest()==x['section_sha256'][label],label
 assert 'SND_StartSeq(' not in s and 'SND_StopSeq(' not in s
 print('PASS SFX timing scope: %d baseline files unchanged; exact scheduler/test exceptions; Flame, E108 loader/readiness, PCM, gameplay, camera and manual-only workflow preserved'%len(x['frozen']))
if __name__=='__main__':validate()
