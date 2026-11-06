#!/usr/bin/env python3
"""Exact enemy-only changes from the approved night palette commit."""
from pathlib import Path
import hashlib,json
from level2_enemy_scope import enemy_lock
R=Path(__file__).resolve().parents[1];x=enemy_lock()
assert x['base_commit']=='42307e1e4b8946443349bc443c8aeec31a267385'
for group in ['frozen','changes','added']:
 for n,e in x[group].items():
  if group=='changes':e=e['after']
  b=(R/n).read_bytes();assert {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}==e,n
assert all(n in x['frozen'] for n in ['src/game.c','src/main.c','src/wingsuit_audio.c','src/wingsuit_audio.h','src/wingsuit_audio_data.h','.github/workflows/build.yml'])
assert all(n in x['frozen'] for n in ('assets/wingsuit/'+n for n in json.loads((R/'assets/wingsuit/manifest.json').read_text())['files']))
for section in x['preserved_sections']:
 s=(R/section['file']).read_text();a=s.index(section['begin']);b=s.index(section['end'],a)
 assert hashlib.sha256(s[a:b].encode()).hexdigest()==section['sha256'],section['file']
print('PASS exact approved-night preservation: %d frozen files; scoped enemy source/test/budget updates; Level 1, all runtime assets, camera constants, audio and workflow preserved'%len(x['frozen']))
