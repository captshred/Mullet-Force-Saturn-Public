#!/usr/bin/env python3
"""Deterministic flame, canonical death bank, dev/release controls and UBSan."""
from pathlib import Path
import hashlib,json,struct,subprocess,tempfile
import seq
from level2_audio_scope import audio_asset,audio_source
R=Path(__file__).resolve().parents[1]
A=R/'assets/wingsuit'
def sha(b):return hashlib.sha256(b).hexdigest()
m=json.loads((A/'manifest.json').read_text())
lock=json.loads((R/'docs/flame-preservation.json').read_text())
assert lock['base_commit']=='785d2f8c0ea602c1d65f348154c107a4f1c3cd96'
assert len(lock['files'])==13
for n,f in lock['files'].items():assert m['files'][n]==f,(n,'approved asset changed')
new={f'WFL{i}.BIN' for i in range(4)}|{f'WFO{i}.BIN' for i in range(4)}|{'WDEATH.MAP','WDEATH.SEQ','WDEATH.TON'}
assert set(m['files'])==set(lock['files'])|new
assert sum(f['bytes'] for f in m['files'].values())==198264
subprocess.run(['python3','tools/validate-level2-audio.py'],cwd=R,check=True)
frames=[(A/f'WFL{i}.BIN').read_bytes() for i in range(4)]
assert len(set(frames))==4 and all(len(b)==2048 for b in frames)
for b in frames:
 pixels=struct.unpack('>1024H',b);assert 0 in pixels and len(set(pixels))==5
# Narrow tuning changes only the four flame payloads, input and geometry.
tuning=json.loads((R/'docs/flame-tuning-preservation.json').read_text())
assert tuning['base_commit']=='5b07fe92676d4f3cc8c431be057ae6bbb6efa1fe'
assert len(tuning['files'])==16
for name,info in tuning['files'].items():
 assert m['files'][name]==audio_asset(name,info) and sha((A/name).read_bytes())==audio_asset(name,info)['sha256'],name
for name,digest in tuning['sources_sha256'].items():assert sha((R/name).read_bytes())==audio_source(name,digest),name
widths=[]
for b in frames:
 rows=[struct.unpack('>32H',b[y*64:(y+1)*64]) for y in range(32)]
 widths.extend(sum(bool(v) for v in row) for row in rows)
 assert b[:64]==b[-64:], 'first/last rows must meet exactly in every frame'
 for row in rows:
  occupied=[x for x,v in enumerate(row) if v]
  assert occupied==list(range(occupied[0],occupied[-1]+1)), 'no holes in flame body'
  assert all(row[x] for x in range(7,26)), 'continuous wide core, no terminal point'
assert min(widths)==21 and max(widths)==25 and sum(widths)/len(widths)==23
old_width=tuning['old_flame_body_width'];assert old_width['width_sum']/old_width['row_count']==27.40625
ratio=(sum(widths)/len(widths))/old_width['mean_pixels'];assert .82<=ratio<=.88
for i,b in enumerate(frames):
 offset=i*8*64;assert b==frames[0][offset:]+frames[0][:offset], 'upward-flowing cyclic animation'
assert m['max_sprite_commands']==72 < tuning['sdk']['max_polygons']==1761
assert tuning['sdk']['sgl_x']==64 and tuning['sdk']['sgl_z']==16
s=(R/'src/input.c').read_text();assert 'READ_BUTTON(MF_X, JO_KEY_X)' in s and 'JO_KEY_Z' not in s
print('PASS flame geometry/art: 27.40625 -> 23 mean body pixels (16.08% narrower); 21..25 solid pixels on every row, exact tile seams and four upward-flowing phases; sixteen stage payloads/protected sources match exact scoped locks')
# Origin-only art additions preserve every parent stage payload and beam hitbox.
origin=json.loads((R/'docs/aimed-drone-preservation.json').read_text())
assert origin['base_commit']=='f94c7721ef0d846ee618d44b006040477d063328' and len(origin['files'])==20
for name,info in origin['files'].items():assert m['files'][name]==audio_asset(name,info) and sha((A/name).read_bytes())==audio_asset(name,info)['sha256'],name
for name,digest in origin['sources_sha256'].items():assert sha((R/name).read_bytes())==audio_source(name,digest),name
s=(R/'src/wingsuit.c').read_text();a=s.index('    for(i=0;i<2;i++)if(pulse[i])');b=s.index('    for(i=0;i<MF_WS_SHOTS;i++)',a)
assert sha(s[a:b].encode())==origin['beam_collision_sha256']
caps=[(A/f'WFO{i}.BIN').read_bytes() for i in range(4)]
assert len(set(caps))==4 and all(len(b)==1024 for b in caps)
for phase,b in enumerate(caps):
 assert b[:64]==frames[phase][-64:], 'origin must meet the phase-matched body exactly'
 rows=[struct.unpack('>32H',b[y*64:(y+1)*64]) for y in range(16)]
 widths=[sum(bool(v) for v in row) for row in rows]
 assert widths[-1]==3 and widths[0]>=21
 assert all(0<=widths[y]-widths[y+1]<=4 for y in range(15)), 'smooth rounded bloom, no abrupt width jump'
 for row in rows:
  occupied=[x for x,v in enumerate(row) if v]
  assert occupied==list(range(occupied[0],occupied[-1]+1)) and row[16]
 assert [x for x,v in enumerate(rows[-1]) if v]==[15,16,17], 'stable centered emitter in all phases'
 assert rows[-1][16]==struct.unpack_from('>H',frames[0],32)[0], 'hot core retained'
assert m['textures']==18 and m['vdp1_bytes']==28032 and m['max_sprite_commands']==72
print('PASS flame origin: four native 32x16 phases, stable three-pixel hot emitter, smooth 21..25-pixel bloom, exact body/cap seams; all parent non-audio payloads and beam collision byte-for-byte unchanged')
# Exact integration ordering remains guarded, not a second transition path.
s=(R/'src/main.c').read_text()
assert s.index('mf_dev_stage_skip(&game,pressed);')<s.index('mf_game_step_inputs(&game,held,pressed,')
assert s.count('mf_ws_runtime_begin(')==1
s=(R/'src/wingsuit_runtime.c').read_text()
assert s.index('mf_ws_step(&shooter,held,pressed,conn);mf_ws_audio_events(shooter.deaths,shooter.shots_fired)')<s.index('mf_ws_audio_step(now,focus)')
assert s.index('slSoundOffWait();wipe(MF_WS_SOUND_RAM,0x80000)')<s.index('mf_ws_audio_load(read_asset)')<s.index('restore_sprite_state())')
flags=json.loads((R/'assets/full-gameplay-sfx2/preservation.json').read_text())['profile_flags']
defines=[f'-D{k}={17 if v=="B" else v}' for k,v in flags.items()]
with tempfile.TemporaryDirectory(prefix='mf-flame-') as tmp:
 def run(name,sources,includes,extra=()):
  exe=str(Path(tmp)/name)
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',*includes,*extra,*sources,'-o',exe],cwd=R,check=True)
  subprocess.run([exe],cwd=R,check=True)
 for enabled in [0,1]:
  dev=[f'-DMF_DEV_STAGE_SKIP={enabled}']
  run('stage'+str(enabled),['tests/dev_stage_skip_test.c'],['-Isrc'],[*defines,'-DMF_LEVEL1_STAGE_CLEAR=1','-DMF_LEVEL2_WINGSUIT=1',*dev])
  run('input'+str(enabled),['tests/dev_input_test.c','src/input.c'],['-Itests/dev_input_mock','-Isrc'],dev)
 for name,sources,includes in [
  ('aim',['tests/wingsuit_aim_test.c'],['-Isrc']),
  ('sim',['tests/wingsuit_test.c','src/wingsuit.c'],['-Isrc']),
  ('weapon',['tests/wingsuit_weapon_test.c','src/wingsuit.c'],['-Isrc']),
  ('flame',['tests/wingsuit_flame_test.c','src/wingsuit.c'],['-Isrc']),
  ('audio',['tests/wingsuit_audio_test.c'],['-Itests/wingsuit_audio_mock','-Itests/sound_mock','-Isrc']),
  ('runtime',['tests/wingsuit_runtime_test.c','src/wingsuit.c'],['-Itests/wingsuit_mock','-Isrc'])]:
  run(name,sources,includes,['-fsanitize=undefined','-fno-sanitize-recover=all'])
print('PASS flame preservation: thirteen approved payloads unchanged; exact canonical explosion/approved weapons and full tables/map; 24 files/198264 bytes; dev/release Saturn X; simulation/audio/runtime UBSan')
