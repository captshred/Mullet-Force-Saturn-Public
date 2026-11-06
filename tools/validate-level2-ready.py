#!/usr/bin/env python3
"""Readiness-only changes relative to the turret build; zero art/gameplay changes."""
from pathlib import Path
import hashlib
from level2_ready_scope import ready_lock
R=Path(__file__).resolve().parents[1];x=ready_lock()
assert x['base_commit']=='c69713001222729012649aeea1e4f1fd98c5b19b'
assert set(x['changes'])=={'src/wingsuit_audio.c','tests/wingsuit_audio_test.c','tools/level2_turret_scope.py','tools/validate-rooftop-turrets.py','tools/test-wingsuit.py','tools/validate-level2-audio.py'}
for group in ['frozen','changes','added']:
 for n,e in x[group].items():
  if group=='changes':e=e['after']
  b=(R/n).read_bytes();assert {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}==e,n
for n in ['src/wingsuit.c','src/wingsuit.h','src/wingsuit_runtime.c','src/rooftop_turret_data.h','src/chrome_eye_data.h','src/game.c','src/main.c','src/music.c','assets/wingsuit/manifest.json','.github/workflows/build.yml']:
 assert n in x['frozen'],n
assert all(n in x['frozen'] for n in ['docs/level2-turret-lock.json','docs/level2-enemy-lock.json'])
print('PASS readiness-only preservation: %d frozen turret-build files; exact six source/test integrations; enemy behavior/art/capacities, camera, city, Level1, audio payloads/parameters and workflow unchanged'%len(x['frozen']))
