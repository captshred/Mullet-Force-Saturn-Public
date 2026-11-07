#!/usr/bin/env python3
"""Exact v3 preservation, recovered assets, source policy and real ISO validation."""
from pathlib import Path
import hashlib,json,argparse,zipfile,struct
from wingsuit_disc import directory_records,validate_disc
R=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def info(b):return {'bytes':len(b),'sha256':sha(b)}
def payloads(b):
 root=dict(directory_records(b,b[16*2048+156:16*2048+190]));records=dict(directory_records(b,root['ALEVEL2']))
 return {n:b[struct.unpack_from('<I',r,2)[0]*2048:struct.unpack_from('<I',r,2)[0]*2048+struct.unpack_from('<I',r,10)[0]] for n,r in records.items() if n not in ('.','..')}
def validate(disc=False):
 x=json.loads((R/'docs/source-recovery-lock.json').read_text())
 assert x['base_commit']=='5ca590d774cc91d0ac1bb4ce6b325aa647b3dd59'
 feature=json.loads((R/'docs/sfx-scheduling-lock.json').read_text())
 assert feature['base_commit']=='6596c96d30569bdfc0fdaa0b72e6da4bab0a32e0'
 def expected(n,e):
  c=feature['changes'].get(n)
  if c is None:return e
  assert c['before']==e,(n,'unexpected SFX baseline')
  return c['after']
 for n,e in feature['frozen'].items():assert info((R/n).read_bytes())==e,n
 for n,e in feature['changes'].items():assert info((R/n).read_bytes())==e['after'],n
 for n,e in x['frozen'].items():assert info((R/n).read_bytes())==expected(n,e),n
 for n,e in x.get('added',{}).items():assert info((R/n).read_bytes())==expected(n,e),n
 for n,e in x['changes'].items():assert info((R/n).read_bytes())==expected(n,e['after']),n
 s=(R/'src/wingsuit_audio.c').read_text()
 assert 'boot_counter=sound_word(0x41a);' in s and 'if(sound_word(0x41a)==boot_counter || !commands_empty())return;' in s
 assert s.index('boot_counter=sound_word(0x41a);')<s.index('stage(MF_WS_AUDIO_DSP_STOP);if(!result(SND_StopDsp()))')
 assert '0x8838' in s # Historical explanatory comment retained, never polled.
 assert 'sound_word(0x8838)' not in s and 'SND_StopSeq(' not in s
 assert 'SND_StartSeq(0,1,0,0)' in s and 'SND_SetSeqVl(0,127,0)' in s
 with zipfile.ZipFile(R/'downloads/mullet-force-level2-audio-engine-review.zip') as z:b=z.read('mullet-force.bin')
 assert sha(b)=='a3e3a75834a28a1b6c9e562f54fd5f6ca29e95a6664940f50c34603cbfe0121e'
 expected=payloads(b)
 for n in expected:
  asset=R/'assets/wingsuit'/n
  assert asset.exists() and asset.read_bytes()==expected[n],n
 for n in ('WCELL.BIN','WROOF.BIN','WPAL.BIN'):expected[n]=(R/'assets/level2-neon-city'/n).read_bytes()
 # Music map decodes to the exact documented, nonoverlapping SCSP extents.
 m=expected['WMUSIC.MAP'];assert len(m)==56
 for off,addr,size in [(16,148864,84),(24,148948,158312),(32,307260,69652),(40,376912,70676)]:
  assert int.from_bytes(m[off+1:off+4],'big')==addr and int.from_bytes(m[off+5:off+8],'big')==size
 assert 376912+70676==447588 and 524288-447588==76700
 # Development path compiles source; archive patcher is reference-only.
 path=(R/'tools/build-source-complete.sh').read_text()
 assert 'bash tools/build.sh --native' in path and 'zip' not in path and 'neon-city.py' not in path
 if disc:
  image=(R/'build/mullet-force.bin').read_bytes();validate_disc(image,expected)
  root=dict(directory_records(image,image[16*2048+156:16*2048+190]));r=root['0.BIN'];o=struct.unpack_from('<I',r,2)[0]*2048;n=struct.unpack_from('<I',r,10)[0]
  assert image[o:o+n]==(R/'build/cd/0.bin').read_bytes()
  assert (R/'build/game.elf').exists()
  print('PASS recovered source ISO: newly compiled executable; all 29 Level2 resources equal golden, with exactly approved three neon replacements; SCSP447588/free76700')
 print('PASS v3 recovery preservation: %d original files frozen, %d exact changes; current gameplay/camera/Level1/maps/music PCM/Flame parameters preserved'%(len(x['frozen']),len(x['changes'])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');validate(p.parse_args().disc)
