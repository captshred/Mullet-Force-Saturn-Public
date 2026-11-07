#!/usr/bin/env python3
"""Replace only bank0/program1 PCM in-place; runtime bank is committed."""
from pathlib import Path
import wave,struct,hashlib,json,argparse
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit'
def sha(b):return hashlib.sha256(b).hexdigest()
def convert(path):
 raw=path.read_bytes();assert sha(raw)=='601f85a59b5284cb4cb09fc37be29396ec573b1b9bb194201962d55e1b584b4d'
 with wave.open(str(path)) as w:
  assert (w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes(),w.getcomptype())==(44100,2,2,18798,'NONE')
  v=struct.unpack('<37596h',w.readframes(18798))
 def rounded(x):return (x+1)//2 if x>=0 else -((-x+1)//2)
 pcm=struct.pack('>18798h',*(rounded(v[i]+v[i+1]) for i in range(0,len(v),2)))
 bank=bytearray((A/'WDEATH.TON').read_bytes());off=struct.unpack_from('>H',bank,10)[0];start=int.from_bytes(bank[off+6:off+10],'big')&0xfffff
 assert off==94 and start==31884 and len(bank)==158312
 bank[off+12:off+14]=(18798).to_bytes(2,'big')
 bank[start:start+44806]=pcm+bytes(44806-len(pcm));(A/'WDEATH.TON').write_bytes(bank)
 r={'source_sha256':sha(raw),'rate':44100,'source_channels':2,'bits':16,'frames':18798,'runtime_channels':1,'runtime_endian':'big','conversion':'mean L/R, symmetric ties away from zero; no gain/resample/trim','pcm_bytes':len(pcm),'pcm_sha256':sha(pcm),'tone_sha256':sha(bank),'pcm_offset':start,'pcm_address':148948+start,'old_pcm_bytes':44806,'zero_tail_bytes':44806-len(pcm),'bank_bytes':len(bank),'scsp_high_water':485812,'scsp_free':38476}
 (A/'new-hit.json').write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('wav',type=Path);convert(p.parse_args().wav)
