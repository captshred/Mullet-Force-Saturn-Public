#!/usr/bin/env python3
"""Independent split PCM/native bank layout, preservation and SND validation."""
from pathlib import Path
import json,hashlib,struct,re
import seq
from level2_audio_scope import audio_source,audio_asset
from level2_sustain_scope import sustain_source
from level2_polyphony_scope import poly_source,lock as poly_lock
from level2_split_scope import split_source,split_file,lock as split_lock
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit';r=json.loads((A/'audio.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
lock=json.loads((R/'docs/level2-audio-bank-lock.json').read_text())
assert lock['base_commit']=='c721fa189043e66ee6292398ef3fcddbb692063a'
for name,c in lock['files'].items():
 b=(A/name).read_bytes();expected=split_file('assets/wingsuit/'+name,c['after'])
 assert len(b)==expected['bytes'] and sha(b)==expected['sha256'] and r['files'][name]==expected,name
for name,c in lock['sources'].items():assert sha((R/name).read_bytes())==audio_source(name,c['before']),name
old=(R/'assets/cd/FX.TON').read_bytes();ton=(A/'WDEATH.TON').read_bytes()
assert struct.unpack_from('>8H',ton)==(16,34,44,54,58,94,130,166)
assert ton[16:58]==old[24:66], 'complete original mixer/velocity/PEG/PLFO tables'
def voice(data,i):
 off=struct.unpack_from('>H',data,8+2*i)[0];v=bytearray(data[off:off+36]);a=((v[7]&15)<<16)|int.from_bytes(v[8:10],'big');n=int.from_bytes(v[12:14],'big')*2
 pcm=data[a:a+n];v[7]&=240;v[8:10]=bytes(2);return v,pcm
assert voice(ton,0)==voice(old,2), 'exact canonical explosion parameters and PCM'
assert sha(voice(ton,1)[0])=='e4ea4af07d15ff278b67b5408588c22116e4addc4cce41a81a3ae9458519f91f','approved Shot tone parameters'
expected=[(31680,'2eca5219e7a0255532d46c6c0a4835dee475781787334da46bfb451363e4fa6b'),(44806,'dc25ce5eead8a8ed620e44c0cdc9ca47dbadb8b647cf9a5a86dc241b74232de2'),(55950,'9e62074cf628c6c4611a488bb2afa0c8e4b29f034cbd2e4a093258a4e6479676'),(25664,'effcb354cef8271d53590c298c5f32b9df29946a29e203582988941d88c0122d')]
for i,(n,digest) in enumerate(expected):
 v,pcm=voice(ton,i);assert len(pcm)==n and sha(pcm)==digest
 assert v[28]==0xe0 and v[17]&31==31 and v[27]==0
 if i:assert v[29]==(61 if i==3 else 60) and v[30]==0
 assert v[7]&0x60==(0x20 if i==3 else 0) and int.from_bytes(v[10:12],'big')==0
s=(A/'WDEATH.SEQ').read_bytes();original=seq.decode((R/'assets/cd/FX.SEQ').read_bytes(),2);a=seq.decode(s,0);original['programs']=[(0,0,0)];assert a==original
shot=seq.decode(s,1);assert shot['programs']==[(0,0,1)] and shot['notes']==[(0,504,0,60,110)] and not shot['loops']
assert struct.unpack_from('>H2I',s)==(2,12,48) and len(s)==84 and sha(s)=='3672e4b1aa681bbe1dec774086fc4f6b8488e6e3be9bec352f869c94246e7c63'
m=(A/'WDEATH.MAP').read_bytes();assert m[:16]==(R/'assets/cd/CUSTOM.MAP').read_bytes()[:16] and m[-8:]==b'\xff'*8
for off,kind,addr,n in [(16,1,148864,84),(24,0,148948,158312)]:
 assert m[off]==kind<<4 and int.from_bytes(m[off+1:off+4],'big')==addr
 assert m[off+4]==128 and int.from_bytes(m[off+5:off+8],'big')==n
assert r['scsp_high_water']==307260 and r['scsp_free']==217028 and len(ton)==158312
last=148948+202
assert len(r['samples'])==4
for i,sample in enumerate(r['samples']):
 v,pcm=voice(ton,i);assert sample['scsp_addr']>=last and sample['scsp_addr']%4==0
 assert sample['frames']*2==sample['bytes']==len(pcm) and sample['sha256']==sha(pcm)
 assert sample['tone_offset']==sample['scsp_addr']-148948 and sample['layer_offset']==sample['voice_offset']+4
 last=sample['scsp_addr']+sample['bytes']+sample['guard_frames']*2;assert last<=307260
assert last==307260
attack=r['sources']['Flame attack.wav'];loop=r['sources']['Flame loop.wav']
assert (attack['frames'],attack['pcm_bytes'],loop['source_frames'],loop['frames'],loop['pcm_bytes'])==(27975,55950,13256,12832,25664)
assert (loop['loop_start'],loop['loop_end'],loop['seam']['trim_start'],loop['seam']['trim_end'],loop['seam']['crossfade_frames'])==(0,12832,114,310,0)
assert (loop['seam']['jump'],loop['seam']['slope_difference'])==(-5,5)
assert attack['source_sha256']=='bfc55dc8ae2e4fed1362cf6ff60402ad42d61d018f704818010baac9c5615866'
assert loop['source_sha256']=='222fd540adb224c11186ac07188957a086c0bc211b93e60916773283425274a5'
assert set(r['sources'])=={'Shot.wav','Flame attack.wav','Flame loop.wav'}
assert r['sources']['Shot.wav']['source_sha256']=='dafa67cc18aa35848d44f166c79481a783f8ebaa38c739ff2a6e992a8031e91c'
for x in r['sources'].values():assert (x['rate'],x['bits'],x['channels'])==(44100,16,1)
h=(R/'src/wingsuit_audio_data.h').read_text()
for name,value in [('SEQ_BYTES',84),('TON_BYTES',158312),('MAP_BYTES',40),('SEQ_ADDR',148864),('TON_ADDR',148948),('FLAME_HANDOFF_TICKS',38),('FLAME_ATTACK_PROGRAM',2),('FLAME_ATTACK_LAYER_ADDR',149082),('FLAME_ATTACK_PCM_ADDR',225640),('FLAME_ATTACK_FRAMES',27975),('FLAME_ATTACK_NOTE',60),('FLAME_LOOP_PROGRAM',3),('FLAME_LOOP_LAYER_ADDR',149118),('FLAME_LOOP_PCM_ADDR',281592),('FLAME_LOOP_FRAMES',12832),('FLAME_LOOP_NOTE',61)]:assert int(re.search(r'#define MF_WS_'+name+r' (\d+)',h)[1])==value
pres=json.loads((R/'docs/level2-audio-preservation.json').read_text());assert pres['base_commit']==lock['base_commit'] and len(pres['files'])==21
for name,info in pres['files'].items():assert sha((A/name).read_bytes())==info['sha256'] and len((A/name).read_bytes())==info['bytes'],name
for name,digest in pres['sources_sha256'].items():assert sha((R/name).read_bytes())==digest,name
source=(R/'src/wingsuit.c').read_text();a=source.index('static uint32_t integer_sqrt');b=source.index('/* One successful tap',a)
assert sha(source[a:b].encode())==pres['aiming_sha256']
transport=(R/'src/wingsuit_audio.c').read_text()
assert 'slSoundRequest(' not in transport
assert 'SND_ChgMap(0)' in transport and 'SND_CtrlDirMidi(' in transport and all(call not in transport for call in ['SND_StartSeq(', 'SND_StopSeq('])
assert 'SND_INI_ARA_SZ(init)=MF_WS_MAP_BYTES/sizeof(Uint16)' in transport
repair=json.loads((R/'docs/level2-audio-e108-source-lock.json').read_text())
for name,c in repair['sources'].items():assert sha((R/name).read_bytes())==split_source(name,sustain_source(name,c['after'])),name
repair_preserved=json.loads((R/'docs/level2-audio-e108-preservation.json').read_text());assert repair_preserved['base_commit']=='4a42eea5ad2f3ee6aa768256e0d31988903f9570'
assert len([p for p in repair_preserved['files'] if p.startswith('assets/wingsuit/')])==26
for name,info in repair_preserved['files'].items():
 b=(R/name).read_bytes()
 if name in split_lock()['sources']:
  assert sha(b)==split_source(name,info['sha256']),name
 else:
  expected=split_file(name,info);assert len(b)==expected['bytes'] and sha(b)==expected['sha256'],name
sustain=json.loads((R/'docs/level2-flame-sustain-source-lock.json').read_text())
for name,c in sustain['sources'].items():assert sha((R/name).read_bytes())==split_source(name,c['after']),name
split=split_lock()
for name,c in split['sources'].items():assert sha((R/name).read_bytes())==poly_source(name,c['after']),name
for name,c in split['files'].items():
 b=(R/name).read_bytes();assert len(b)==c['after']['bytes'] and sha(b)==c['after']['sha256'],name
frozen=json.loads((R/'docs/level2-split-flame-preservation.json').read_text());assert frozen['base_commit']==split['base_commit']
for name,info in frozen['files'].items():
 b=(R/name).read_bytes();assert len(b)==info['bytes'] and sha(b)==info['sha256'],name
# Initializer remains exact. Only the explicitly authorized one-shot transport
# is replaced; additive source hashes and immutable assets remain exhaustive.
a=transport.index('    stage(MF_WS_AUDIO_MAP_READ)');b=transport.index('    /* Submission success',a)
assert sha(transport[a:b].encode())==split['load_sequence_sha256'],'E108 loading sequence changed'
poly=poly_lock()
for name,c in poly['sources'].items():assert sha((R/name).read_bytes())==c['after'],name
for name,info in poly['frozen'].items():
 b=(R/name).read_bytes();assert len(b)==info['bytes'] and sha(b)==info['sha256'],name
for name,begin,end in [
 ('flame_scheduler','    /* Release is latched','    /* SND_SetSeqVl is the'),
 ('flame_observer','static void observe_flame','/* Read only the driver'),
 ('startup_handshake','static void startup(unsigned','int mf_ws_audio_ready')]:
 a=transport.index(begin);b=transport.index(end,a)
 assert sha(transport[a:b].encode())==poly['preserved_sections'][name],name
assert 'midi(first_port+i,1,60,110)' in transport
print('PASS polyphony source-only lock: all Level 1/2 assets unchanged; exact split Flame scheduler/observer, E108 initialization/readiness; no Level 2 sequence start/stop; full approved source chain preserved')
