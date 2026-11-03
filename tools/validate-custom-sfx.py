#!/usr/bin/env python3
"""Source WAV fidelity, original PCM music and unrelated SFX payload invariants."""
from pathlib import Path
import hashlib,json,struct
import custom_sfx
R=Path(__file__).resolve().parents[1]
r=json.loads((R/'assets/music/report.json').read_text())
locked={'assets/music/drop-zone.mid':'69b888385d2733576b7ca31558954d31c39c841afe8998397b89e9f746a80328','assets/cd/STAGE.SEQ':'0858a4a9af303a853ba6aac2df5aa98ec119fbb6d0d22ce8cf4a8cec5fb08eff','assets/cd/STAGE.TON':'35b0552bde242eef8e49fbd16ae2fff991aa4058d34490d0de32eb77258f25b8'}
for n,h in locked.items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
cfg=json.loads((R/'assets/music/config.json').read_text());mix=cfg['linear_mix'];gain=mix['sfx_gain']*mix['master_headroom']
waves,report=custom_sfx.load(R/'assets/sfx/custom-combat',gain)
assert report==r['custom_combat']
old=(R/'tests/combat_sfx_baseline/FX.TON').read_bytes();new=(R/'assets/cd/FX.TON').read_bytes()
def voice(data,i):
 l=struct.unpack_from('>H',data,8+2*i)[0]+4
 sa=((data[l+3]&15)<<16)|struct.unpack_from('>H',data,l+4)[0]
 n=struct.unpack_from('>H',data,l+8)[0];header=bytearray(data[l:l+32]);header[3]&=240;header[4:6]=b'\0\0'
 return bytes(header),data[sa:sa+n*2]
for i in range(5):assert voice(old,i)==voice(new,i),('unrelated sound changed',i)
for i,w in enumerate(waves):
 pcm=voice(new,5+i)[1]
 expected=struct.pack('>'+str(len(w))+'h',*(round(int(v*.9*32767)*gain) for v in w))
 assert pcm==expected,('WAV conversion differs',i)
print('PASS: original MIDI/PCM music exact; original jump/impact/ignition/hiss unchanged; all custom PCM samples derive exactly from supplied WAVs without clipping.')
