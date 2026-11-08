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
 audio=json.loads((R/'docs/duplicate-shot-lock.json').read_text())
 assert audio['base_commit']=='bb7b6b61af79ccddd9994a9623456d3f10ad6613'
 def approved(n):
  actual=info((R/n).read_bytes());c=audio['changes'].get(n)
  if c is None:return actual
  assert actual==c['after'],(n,'unexpected duplicate-shot change')
  return c['before']
 for n in audio['changes']:approved(n)
 bat=json.loads((R/'docs/bat-command-lock.json').read_text())
 assert bat['base_commit']=='1e7077616f7da57436500b3d9cddda2e61e6a727'
 for n,e in bat['frozen'].items():assert approved(n)==e,n
 for n,e in bat['changes'].items():assert approved(n)==e['after'],n
 def observed(n):
  value=approved(n);c=bat['changes'].get(n)
  if c is None:return value
  assert value==c['after'],n
  return c['before']
 new=json.loads((R/'docs/new-hit-lock.json').read_text())
 assert new['base_commit']=='f27333b1422c0a24cb5fe0f52f9557649b820941'
 for n,e in new['frozen'].items():assert observed(n)==e,n
 for n,e in new['changes'].items():assert observed(n)==e['after'],n
 def prior(n):
  actual=observed(n);c=new['changes'].get(n)
  if c is None:return actual
  assert actual==c['after'],n
  return c['before']
 x=json.loads((R/'docs/source-recovery-lock.json').read_text())
 assert x['base_commit']=='5ca590d774cc91d0ac1bb4ce6b325aa647b3dd59'
 repair=json.loads((R/'docs/fire-hit-startup-lock.json').read_text())
 assert repair['base_commit']=='0f0ef24873a3e3c91b573d32fd26f725328c4353'
 def repaired(n,e):
  c=repair['changes'].get(n)
  if c is None:return e
  assert c['before']==e,(n,'unexpected startup-repair baseline')
  return c['after']
 for n,e in repair['frozen'].items():assert prior(n)==e,n
 for n,e in repair['changes'].items():assert prior(n)==e['after'],n
 swap=json.loads((R/'docs/fire-hit-lock.json').read_text())
 assert swap['base_commit']=='6e5c8d9eb9b83e4cf3ebb278939b02b8787a0b1e'
 def swapped(n,e):
  c=swap['changes'].get(n)
  if c is None:return repaired(n,e)
  assert c['before']==e,(n,'unexpected Fire/Hit baseline')
  return repaired(n,c['after'])
 for n,e in swap['frozen'].items():assert prior(n)==repaired(n,e),n
 for n,e in swap['changes'].items():assert prior(n)==repaired(n,e['after']),n
 feature=json.loads((R/'docs/sfx-scheduling-lock.json').read_text())
 assert feature['base_commit']=='6596c96d30569bdfc0fdaa0b72e6da4bab0a32e0'
 def expected(n,e):
  c=feature['changes'].get(n)
  if c is None:return swapped(n,e)
  assert c['before']==e,(n,'unexpected SFX baseline')
  return swapped(n,c['after'])
 for n,e in feature['frozen'].items():assert prior(n)==swapped(n,e),n
 for n,e in feature['changes'].items():assert prior(n)==swapped(n,e['after']),n
 for n,e in x['frozen'].items():assert prior(n)==expected(n,e),n
 for n,e in x.get('added',{}).items():assert prior(n)==expected(n,e),n
 for n,e in x['changes'].items():assert prior(n)==expected(n,e['after']),n
 s=(R/'src/wingsuit_audio.c').read_text()
 assert 'boot_counter=sound_word(0x41a);' in s and 'if(sound_word(0x41a)==boot_counter || !commands_empty())return;' in s
 assert s.index('boot_counter=sound_word(0x41a);')<s.index('stage(MF_WS_AUDIO_DSP_STOP);if(!result(SND_StopDsp()))')
 assert '0x8838' in s # Historical explanatory comment retained, never polled.
 assert 'sound_word(0x8838)' not in s and 'SND_StopSeq(' not in s
 assert 'SND_StartSeq(0,1,0,0)' in s and 'SND_SetSeqVl(0,127,0)' in s
 with zipfile.ZipFile(R/'downloads/mullet-force-level2-audio-engine-review.zip') as z:b=z.read('mullet-force.bin')
 assert sha(b)=='a3e3a75834a28a1b6c9e562f54fd5f6ca29e95a6664940f50c34603cbfe0121e'
 expected=payloads(b)
 from importlib.machinery import SourceFileLoader
 hit=SourceFileLoader('hit_sample',str(R/'tools/validate-new-hit.py')).load_module()
 expected['WDEATH.TON']=hit.validate_hit(expected['WDEATH.TON'])
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
  fire=json.loads((R/'assets/wingsuit/fire-hit.json').read_text())
  for n,e in fire['files'].items():
   b=(R/'assets/wingsuit'/n).read_bytes();assert info(b)==e;expected[n]=b
  assert len(expected['WFIRE.TON'])==38224 and len(expected['WFIRE.MAP'])==64
  assert expected['WFIRE.MAP'][:-16]==expected['WMUSIC.MAP'][:-8]
  image=(R/'build/mullet-force.bin').read_bytes();validate_disc(image,expected)
  root=dict(directory_records(image,image[16*2048+156:16*2048+190]));r=root['0.BIN'];o=struct.unpack_from('<I',r,2)[0]*2048;n=struct.unpack_from('<I',r,10)[0]
  assert image[o:o+n]==(R/'build/cd/0.bin').read_bytes()
  assert (R/'build/game.elf').exists()
  print('PASS recovered source ISO: newly compiled executable; 29 preserved Level2 resources plus isolated bank2 Fire resources; SCSP485812/free38476')
 print('PASS v3 recovery preservation: %d original files frozen, %d exact changes; current gameplay/camera/Level1/maps/music PCM/Flame parameters preserved'%(len(x['frozen']),len(x['changes'])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');validate(p.parse_args().disc)
