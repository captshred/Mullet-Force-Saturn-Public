#!/usr/bin/env python3
"""Independent runtime-bank checks; private WAVs are not needed for public builds."""
from pathlib import Path
import hashlib,json,re,struct
R=Path(__file__).resolve().parents[1];cd=R/'assets/cd';r=json.loads((R/'assets/music/report.json').read_text());u=r['sfx_update_2'];ton=(cd/'FX.TON').read_bytes();seq=(cd/'FX.SEQ').read_bytes();mp=(cd/'CUSTOM.MAP').read_bytes()
def voices(data):
 out=[]
 for i in range((struct.unpack_from('>H',data)[0]-8)//2):
  off=struct.unpack_from('>H',data,8+2*i)[0];v=bytearray(data[off:off+36]);assert len(v)==36 and v[2]==0
  sa=((v[7]&15)<<16)|struct.unpack_from('>H',v,8)[0];n=struct.unpack_from('>H',v,12)[0];assert sa+n*2<=len(data)
  pcm=data[sa:sa+n*2];v[7]&=240;v[8:10]=b'\0\0';out.append((bytes(v),pcm))
 return out
v=voices(ton);assert len(v)==8
for i,lock in u['original_voice_locks'].items():
 voice,pcm=v[int(i)];assert hashlib.sha256(voice).hexdigest()==lock['voice_sha256'];assert hashlib.sha256(pcm).hexdigest()==lock['pcm_sha256']
for sample in u['samples']:
 i=sample['voice'];voice,pcm=v[i];assert voice[29]==72 and voice[20]==0 and voice[17]&31==31
 assert len(pcm)==sample['frames']*2 and hashlib.sha256(pcm).hexdigest()==sample['pcm_sha256']
 assert pcm[:2]==pcm[-2:]==b'\0\0';assert max(map(abs,struct.unpack('>'+str(len(pcm)//2)+'h',pcm)))==sample['peak']<32767
 # Decode actual Sega note gates and time deltas, including extension events.
 off=struct.unpack_from('>I',seq,2+4*i)[0];p=off+16;extension=0;delta=0;gate=None
 while seq[p]!=0x83:
  ctl=seq[p];p+=1
  if ctl==0x88:extension+=512;continue
  if ctl==0x8c:delta+=256;continue
  if ctl==0xb0:p+=2;delta+=seq[p];p+=1;continue
  if ctl==0xc0:p+=1;delta+=seq[p];p+=1;continue
  assert ctl in (0,0x40),hex(ctl);assert seq[p:p+2]==bytes([60,110]);p+=2
  gate=extension+(256 if ctl&64 else 0)+seq[p];p+=1;delta+=seq[p];p+=1
 assert gate/960>=sample['duration_seconds']+1/60 and delta>=gate
for off,name in [(16,'FX.SEQ'),(24,'FX.TON'),(32,'STAGE.SEQ'),(40,'STAGE.TON')]:
 addr=int.from_bytes(mp[off+1:off+4],'big');size=int.from_bytes(mp[off+5:off+8],'big');assert size==len((cd/name).read_bytes())
 region=next(x for x in r['sound_ram_regions'] if x['name']==name);assert addr==region['start'] and size==region['size']
regions=r['sound_ram_regions'];assert all(a['end']<=b['start'] for a,b in zip(regions,regions[1:]));assert regions[-1]['end']==u['after_high_water']<=524288
h=(R/'src/music_data.h').read_text()
for key,value in [('MF_FX_SEQ_BYTES',len(seq)),('MF_FX_TON_BYTES',len(ton)),('MF_FX_TON_ADDR',regions[6]['start']),('MF_STAGE_SEQ_ADDR',regions[7]['start']),('MF_STAGE_TON_ADDR',regions[8]['start'])]:assert int(re.search(r'#define '+key+r' (\S+)',h)[1],0)==value
print('PASS SFX2 PCM hashes, mono half-clock tuning, no sample clipping, full one-shot gates, map/header consistency and 512 KiB RAM bounds')
