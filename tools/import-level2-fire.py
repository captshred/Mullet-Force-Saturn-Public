#!/usr/bin/env python3
"""Deterministic runtime-only import; authoring WAV stays private per AGENTS.md."""
from pathlib import Path
import wave,struct,hashlib,json,argparse
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit'
def sha(b):return hashlib.sha256(b).hexdigest()
def build(path):
 raw=path.read_bytes()
 with wave.open(str(path)) as w:
  assert (w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes(),w.getcomptype())==(44100,2,2,19066,'NONE')
  v=struct.unpack('<38132h',w.readframes(19066))
 def rounded(n):return (n+1)//2 if n>=0 else -((-n+1)//2)
 mono=[rounded(v[i]+v[i+1]) for i in range(0,len(v),2)]
 pcm=struct.pack('>19066h',*mono)
 old=(A/'WDEATH.TON').read_bytes();off=struct.unpack_from('>H',old,10)[0];voice=bytearray(old[off:off+36])
 # Keep original Shot envelope/pitch/velocity tables. Single program in bank2.
 voice[7]&=240;voice[8:10]=(88).to_bytes(2,'big');voice[10:12]=bytes(2);voice[12:14]=(19066).to_bytes(2,'big')
 tone=struct.pack('>5H',10,28,38,48,52)+old[16:58]+voice+pcm+bytes(4)
 assert len(tone)==38224
 addr=447588
 mp=(A/'WMUSIC.MAP').read_bytes()[:-8]+bytes([2])+addr.to_bytes(3,'big')+b'\x80'+len(tone).to_bytes(3,'big')+b'\xff'*8
 assert len(mp)==64
 for n,b in [('WFIRE.TON',tone),('WFIRE.MAP',mp)]: (A/n).write_bytes(b)
 report={'source':{'name':'New Shot.wav','sha256':sha(raw),'rate':44100,'channels':2,'bits':16,'frames':19066},'conversion':'nearest integer (L+R)/2; symmetric ties away from zero; mono signed big-endian PCM16; no resample/gain/trim/compression','pcm_bytes':len(pcm),'pcm_sha256':sha(pcm),'pcm_frames':19066,'pcm_rate':44100,'pcm_channels':1,'peak':max(map(abs,mono)),'tone_addr':addr,'pcm_addr':addr+88,'scsp_high_water':addr+len(tone),'scsp_free':524288-addr-len(tone),'files':{n:{'bytes':len(b),'sha256':sha(b)} for n,b in [('WFIRE.TON',tone),('WFIRE.MAP',mp)]}}
 (A/'fire-hit.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('wav',type=Path);build(p.parse_args().wav)
