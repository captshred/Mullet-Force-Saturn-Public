#!/usr/bin/env python3
"""Validate this scoped Level1 upgrade and run unmodified approved-baseline tests."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,tempfile,tarfile,io,re
from level1_audio import BASE,peak,digest
import seq
R=Path(__file__).resolve().parents[1]
ALLOWED={'Makefile','src/music_data.h','assets/cd/STAGE.SEQ','assets/cd/STAGE.TON','assets/cd/CUSTOM.MAP','assets/music/report.json'}
ADDED={'tools/level1_audio.py','tools/import-level1-music.py','tools/validate-level1-custom-audio.py','tests/level1_custom_audio_test.py','assets/music/level1-custom-report.json','docs/level1-custom-audio.md','docs/level1-custom-audio-lock.json','tools/run-level1-audio-emulator.sh','tools/analyze-level1-emulator.py','tests/runtime/level1-audio-frontend.c','docs/level1-custom-emulator.json'}

def validate(disc=False):
 lock=json.loads((R/'docs/level1-custom-audio-lock.json').read_text());assert lock['baseline']==BASE and set(lock['changes'])==ALLOWED
 for name,entry in lock['frozen'].items():assert digest((R/name).read_bytes())==entry,name
 for name,entry in lock['changes'].items():assert digest((R/name).read_bytes())==entry['after'],name
 for name,entry in lock['added'].items():assert digest((R/name).read_bytes())==entry,name
 report=json.loads((R/'assets/music/level1-custom-report.json').read_text());h=(R/'src/music_data.h').read_text();constants={k:int(v,0) for k,v in re.findall(r'#define (MF_\w+) (0x[\da-f]+|\d+)\n',h)}
 decoded=seq.decode((R/'assets/cd/STAGE.SEQ').read_bytes());assert decoded['ppqn']==480 and decoded['end']==279840 and decoded['loops']==[0,279840] and decoded['tempo_loop_offset']==8
 assert decoded['tempos']==[(279840,365854)]
 assert len(decoded['notes'])==report['melodic_events']+report['drums']['retained_hits']
 assert len([n for n in decoded['notes'] if n[2]<12])==5120
 assert all(0<=a<b<=279840 and 0<=c<16 and 0<v<128 for a,b,c,n,v in decoded['notes'])
 assert peak([(a,b) for a,b,c,n,v in decoded['notes'] if c>=12])<=8
 assert peak([(a,b) for a,b,c,n,v in decoded['notes']])==report['music_held_peak']<=22
 tone=(R/'assets/cd/STAGE.TON').read_bytes();count=(int.from_bytes(tone[:2],'big')-8)//2;assert count==13
 for s in report['samples']:
  voice=int.from_bytes(tone[8+s['program']*2:10+s['program']*2],'big');layer=voice+4
  assert tone[voice:voice+4]==bytes([12,0,0,0])
  sa=((tone[layer+3]&15)<<16)|int.from_bytes(tone[layer+4:layer+6],'big');lsa,lea=struct.unpack_from('>HH',tone,layer+6)
  assert sa==s['tone_offset'] and lsa==s['lsa'] and lea==s['frames'] and 0<=lsa<lea<=65535
  assert bool(tone[layer+3]&32)==s['loop'] and (8 if tone[layer+3]&16 else 16)==s['bits']
  assert tone[layer+25]==s['root']+{11025:24,22050:12,44100:0}[s['rate']]
  assert sa+lea*(s['bits']//8)+4<=len(tone)
  if s['loop']:assert tone[sa+lea*(s['bits']//8):][:4]==tone[sa+lsa*(s['bits']//8):][:4]
 mp=(R/'assets/cd/CUSTOM.MAP').read_bytes();assert len(mp)==56
 end=0
 for off,name in [(16,'FX.SEQ'),(24,'FX.TON'),(32,'STAGE.SEQ'),(40,'STAGE.TON')]:
  addr=int.from_bytes(mp[off+1:off+4],'big');size=int.from_bytes(mp[off+5:off+8],'big');data=(R/'assets/cd'/name).read_bytes()
  assert addr%4==size%4==0 and size==len(data) and addr>=end;end=addr+size
  assert addr==constants['MF_'+name.replace('.','_')+'_ADDR'] and size==constants['MF_'+name.replace('.','_')+'_BYTES']
 assert end==report['sound_ram_high_water']<=524288 and 524288-end==report['sound_ram_free']
 if disc:
  from wingsuit_disc import directory_records
  image=(R/'build/mullet-force.bin').read_bytes();assert image[:16]==b'SEGA SEGASATURN ' and len(image)%2048==0
  root=dict(directory_records(image,image[16*2048+156:16*2048+190]))
  for name in ['STAGE.SEQ','STAGE.TON','CUSTOM.MAP','FX.SEQ','FX.TON']:
   rec=root[name];start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0];assert image[start:start+size]==(R/'assets/cd'/name).read_bytes()
  rec=root['ALEVEL2'];records=dict(directory_records(image,rec))
  for name,rec in records.items():
   if name in ('.','..'):continue
   start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0]
   assert image[start:start+size]==(R/'build/cd/ALEVEL2'/name).read_bytes()
  packaged={}
  def scan(records,prefix=''):
   for name,rec in records.items():
    if name in ('.','..'):continue
    start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0]
    if rec[25]&2:scan(dict(directory_records(image,rec)),prefix+name+'/')
    else:packaged[prefix+name]=image[start:start+size]
  scan(root)
  for path in (R/'build/cd').rglob('*'):
   if path.is_file():assert packaged[path.relative_to(R/'build/cd').as_posix().upper()]==path.read_bytes(),path
  fingerprint=(R/'build/SOURCE-SHA256SUMS.txt').read_bytes();assert digest(fingerprint).encode() in packaged['0.BIN']
  subprocess.run(['sha256sum','--check','build/SOURCE-SHA256SUMS.txt'],cwd=R,stdout=subprocess.DEVNULL,check=True)
 print(f"PASS Level1 native audio: 5120 GP notes, {report['drums']['retained_hits']} unshifted drum attacks, 13 custom tones, RAM {end}/524288, held music peak {report['music_held_peak']}; all frozen gameplay/SFX/Level2 files exact",flush=True)

def baseline_tests(tests):
 # Historical validators compare exact source milestones. Run them unchanged
 # in their original tree; current changes and current disc are checked above.
 # Current-disc checks run above in the actual tree. Historical source hashes
 # describe their own immutable revisions and are never asserted for this disc.
 if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
  subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
 with tempfile.TemporaryDirectory(prefix='level1-approved-tests-') as d:
  ref=Path(d)
  with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as archive:archive.extractall(ref,filter='data')
  for name in ('.git','.deps','build'):(ref/name).symlink_to(R/name,target_is_directory=True)
  subprocess.run(['python3','tools/validate-intersection-facade-seal.py', *(['--test'] if tests else [])],cwd=ref,check=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args();validate(a.disc)
 if a.test:subprocess.run([__import__('sys').executable,'tests/level1_custom_audio_test.py'],cwd=R,check=True)
 baseline_tests(a.test)
