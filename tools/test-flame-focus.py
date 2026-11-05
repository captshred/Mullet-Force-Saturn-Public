#!/usr/bin/env python3
"""Deterministic flame, canonical death bank, dev/release controls and UBSan."""
from pathlib import Path
import hashlib,json,struct,subprocess,tempfile
import seq
R=Path(__file__).resolve().parents[1]
A=R/'assets/wingsuit'
def sha(b):return hashlib.sha256(b).hexdigest()
m=json.loads((A/'manifest.json').read_text())
lock=json.loads((R/'docs/flame-preservation.json').read_text())
assert lock['base_commit']=='785d2f8c0ea602c1d65f348154c107a4f1c3cd96'
assert len(lock['files'])==13
for n,f in lock['files'].items():assert m['files'][n]==f,(n,'approved asset changed')
new={f'WFL{i}.BIN' for i in range(4)}|{'WDEATH.MAP','WDEATH.SEQ','WDEATH.TON'}
assert set(m['files'])==set(lock['files'])|new
assert sum(f['bytes'] for f in m['files'].values())==91316
old=(R/'assets/cd/FX.TON').read_bytes();newton=(A/'WDEATH.TON').read_bytes()
def voice(data,index):
 off=struct.unpack_from('>H',data,8+2*index)[0];v=bytearray(data[off:off+36])
 addr=((v[7]&15)<<16)|int.from_bytes(v[8:10],'big');n=int.from_bytes(v[12:14],'big')*2
 pcm=data[addr:addr+n];v[7]&=240;v[8:10]=bytes(2);return v,pcm
v,pcm=voice(old,2);assert voice(newton,0)==(v,pcm)
assert len(pcm)==31680 and sha(pcm)=='2eca5219e7a0255532d46c6c0a4835dee475781787334da46bfb451363e4fa6b'
assert struct.unpack_from('>5H',newton)==(10,0,0,0,28) and newton[10:28]==bytes(18)
original=seq.decode((R/'assets/cd/FX.SEQ').read_bytes(),2);compact=seq.decode((A/'WDEATH.SEQ').read_bytes())
assert original['programs']==[(0,0,2)];original['programs']=[(0,0,0)];assert compact==original
assert not compact['loops'] and len(compact['notes'])==1
mp=(A/'WDEATH.MAP').read_bytes();assert mp[:16]==(R/'assets/cd/CUSTOM.MAP').read_bytes()[:16] and mp[-8:]==b'\xff'*8
for offset,typ,addr,n in [(16,1,148864,44),(24,0,148908,31744)]:
 assert mp[offset]==typ<<4 and int.from_bytes(mp[offset+1:offset+4],'big')==addr
 assert mp[offset+4]==128 and int.from_bytes(mp[offset+5:offset+8],'big')==n
assert len(mp)==40 and 148908+31744==180652<524288
frames=[(A/f'WFL{i}.BIN').read_bytes() for i in range(4)]
assert len(set(frames))==4 and all(len(b)==8192 for b in frames)
for b in frames:
 pixels=struct.unpack('>4096H',b);assert 0 in pixels and len(set(pixels))==5
# Exact integration ordering remains guarded, not a second transition path.
s=(R/'src/main.c').read_text()
assert s.index('mf_dev_stage_skip(&game,pressed);')<s.index('mf_game_step_inputs(&game,held,pressed,')
assert s.count('mf_ws_runtime_begin(')==1
s=(R/'src/wingsuit_runtime.c').read_text()
assert s.index('mf_ws_step(&shooter,held,pressed,conn);mf_ws_audio_events(shooter.deaths)')<s.index('mf_ws_audio_step(now)')
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
  ('sim',['tests/wingsuit_test.c','src/wingsuit.c'],['-Isrc']),
  ('weapon',['tests/wingsuit_weapon_test.c','src/wingsuit.c'],['-Isrc']),
  ('flame',['tests/wingsuit_flame_test.c','src/wingsuit.c'],['-Isrc']),
  ('audio',['tests/wingsuit_audio_test.c'],['-Itests/sound_mock','-Isrc']),
  ('runtime',['tests/wingsuit_runtime_test.c','src/wingsuit.c'],['-Itests/wingsuit_mock','-Isrc'])]:
  run(name,sources,includes,['-fsanitize=undefined','-fno-sanitize-recover=all'])
print('PASS flame preservation: thirteen approved payloads unchanged; exact canonical voice/PCM/song/mixer/map; 20 files/91316 bytes; dev/release Saturn Z; simulation/audio/runtime UBSan')
