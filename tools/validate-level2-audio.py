#!/usr/bin/env python3
"""Independent native PCM, full TON/SEQ/MAP, fixed layout and source validation."""
from pathlib import Path
import json,hashlib,struct,re
import seq
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit';r=json.loads((A/'audio.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
lock=json.loads((R/'docs/level2-audio-bank-lock.json').read_text())
assert lock['base_commit']=='c721fa189043e66ee6292398ef3fcddbb692063a'
for name,c in lock['files'].items():
 b=(A/name).read_bytes();assert len(b)==c['after']['bytes'] and sha(b)==c['after']['sha256']
 assert r['files'][name]==c['after']
for name,c in lock['sources'].items():assert sha((R/name).read_bytes())==c['after'],name
old=(R/'assets/cd/FX.TON').read_bytes();ton=(A/'WDEATH.TON').read_bytes()
assert struct.unpack_from('>7H',ton)==(14,32,42,52,56,92,128)
assert ton[14:56]==old[24:66], 'complete original mixer/velocity/PEG/PLFO tables'
def voice(data,i):
 off=struct.unpack_from('>H',data,8+2*i)[0];v=bytearray(data[off:off+36]);a=((v[7]&15)<<16)|int.from_bytes(v[8:10],'big');n=int.from_bytes(v[12:14],'big')*2
 pcm=data[a:a+n];v[7]&=240;v[8:10]=bytes(2);return v,pcm
assert voice(ton,0)==voice(old,2), 'exact canonical explosion parameters and PCM'
expected=[(31680,'2eca5219e7a0255532d46c6c0a4835dee475781787334da46bfb451363e4fa6b'),(44806,'dc25ce5eead8a8ed620e44c0cdc9ca47dbadb8b647cf9a5a86dc241b74232de2'),(82478,'977588e18e36c230b227f5cf6bf53d242f6ffa2a9b4427475aaefb43b28620d2')]
for i,(n,digest) in enumerate(expected):
 v,pcm=voice(ton,i);assert len(pcm)==n and sha(pcm)==digest
 assert v[28]==0xe0 and v[17]&31==31 and v[27]==0 # dry direct output, fastest release
 if i:assert v[29]==60 and v[30]==0
 if i==2:assert v[7]&0x60==0x20 and int.from_bytes(v[10:12],'big')==27981 and int.from_bytes(v[12:14],'big')==41239
 else:assert v[7]&0x60==0
s=(A/'WDEATH.SEQ').read_bytes();original=seq.decode((R/'assets/cd/FX.SEQ').read_bytes(),2);a=seq.decode(s,0);original['programs']=[(0,0,0)];assert a==original
shot=seq.decode(s,1);assert shot['programs']==[(0,0,1)] and shot['notes']==[(0,504,0,60,110)] and not shot['loops']
assert struct.unpack_from('>H2I',s)==(2,12,48) and len(s)==84
m=(A/'WDEATH.MAP').read_bytes();assert m[:16]==(R/'assets/cd/CUSTOM.MAP').read_bytes()[:16] and m[-8:]==b'\xff'*8
for off,kind,addr,n in [(16,1,148864,84),(24,0,148948,159132)]:
 assert m[off]==kind<<4 and int.from_bytes(m[off+1:off+4],'big')==addr
 assert m[off+4]==128 and int.from_bytes(m[off+5:off+8],'big')==n
assert r['scsp_high_water']==308080 and r['scsp_free']==216208 and len(ton)==159132
last=148948+164
for sample in r['samples']:
 assert sample['scsp_addr']>=last and sample['scsp_addr']%4==0
 last=sample['scsp_addr']+sample['bytes'];assert last<=308080
assert last==308078
flame=r['sources']['Flame.wav'];assert (flame['loop_start'],flame['loop_end'],flame['seam_samples'])==(27981,41239,128)
assert flame['source_sha256']=='e8fc164ba7662e04de7cd772efacf897e8b15ae26a13f1d9e0454cd1c4f08d47'
assert r['sources']['Shot.wav']['source_sha256']=='dafa67cc18aa35848d44f166c79481a783f8ebaa38c739ff2a6e992a8031e91c'
for x in r['sources'].values():assert (x['rate'],x['bits'],x['channels'])==(44100,16,1)
h=(R/'src/wingsuit_audio_data.h').read_text()
for name,value in [('SEQ_BYTES',84),('TON_BYTES',159132),('MAP_BYTES',40),('SEQ_ADDR',148864),('TON_ADDR',148948)]:assert int(re.search(r'#define MF_WS_'+name+r' (\d+)',h)[1])==value
pres=json.loads((R/'docs/level2-audio-preservation.json').read_text());assert pres['base_commit']==lock['base_commit'] and len(pres['files'])==21
for name,info in pres['files'].items():assert sha((A/name).read_bytes())==info['sha256'] and len((A/name).read_bytes())==info['bytes'],name
for name,digest in pres['sources_sha256'].items():assert sha((R/name).read_bytes())==digest,name
source=(R/'src/wingsuit.c').read_text();a=source.index('static uint32_t integer_sqrt');b=source.index('/* One successful tap',a)
assert sha(source[a:b].encode())==pres['aiming_sha256']
transport=(R/'src/wingsuit_audio.c').read_text()
assert 'slSoundRequest("bbbb",SND_MIDI_CTRL_DIR' in transport and 'slSndFlush()' in transport
assert all(call not in transport for call in ['SND_StartSeq(', 'SND_SetSeqVl(', 'SND_CtrlDirMidi(', 'SND_StopSeq(', 'MF_WS_SOUND_BASE[0x4e1]=0'])
print('PASS Level 2 audio: full canonical tables/voice/PCM, approved stereo downmix hashes, 44.1k mono weapons, exact 27981..41239 loop/128-frame seam, aligned nonoverlapping banks, 308080 high-water/216208 free; exact scoped audio changes')
