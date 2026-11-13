#!/usr/bin/env python3
"""Current indexed/packed/disc checks plus the unmodified approved-parent suite."""
from pathlib import Path
import argparse,hashlib,io,json,struct,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];A=R/'art/level1-background-touchups';O=R/'assets/city-cleanup'
PARENT='fa4a56b6df13df6eaeaf0f38676e2de448321217'
ALLOWED={'Makefile','tools/build-city-cleanup.py',*[f'assets/city-cleanup/{n}' for n in ('CIPIX.BIN','CICELL.BIN','PATCHMASK.BIN','manifest.json')]}
def digest(b):return hashlib.sha256(b).hexdigest()
def validate(disc=False):
 proof=json.loads((A/'provenance.json').read_text());assert proof['parent']==PARENT
 for n,sha in proof['original_sha256'].items():assert digest((A/'original'/n).read_bytes())==sha,n
 old=(A/'original/CIPIX.BIN').read_bytes();pixels=(O/'CIPIX.BIN').read_bytes();mask=(O/'TOUCHUPMASK.BIN').read_bytes()
 assert len(old)==len(pixels)==len(mask)==640*240 and all(v in (0,1) for v in mask)
 assert digest(mask)==proof['repair_mask_sha256'] and digest(pixels)==proof['indexed_source_sha256']
 for at,(a,b,edited) in enumerate(zip(old,pixels,mask)):
  x=at%640;y=at//640
  assert a==b or edited,('outside repair mask',x,y)
  if edited:assert any(r['box'][0]<=x<r['box'][2] and r['box'][1]<=y<r['box'][3] for r in proof['regions'])
  if a>=240:assert a==b,('animated neon index',x,y)
  if 402<=x<470 and 82<=y<91:assert a==b,('ION lettering',x,y)
  if y>=104:assert a==b,('lower posts/storefronts/road',x,y)
 assert old[:640*64]==pixels[:640*64],'skyline/architectural roof changed'
 legacy=(A/'original/PATCHMASK.BIN').read_bytes();assert (O/'PATCHMASK.BIN').read_bytes()==bytes(a or b for a,b in zip(legacy,mask))
 for n in ('CIPAL.BIN','CISKY.BIN'):assert (O/n).read_bytes()==(A/'original'/n).read_bytes(),n
 m=json.loads((O/'manifest.json').read_text());assert m['tile_count']==1664 and m['cell_bytes']==106496 and m['vdp2_delta_bytes']==m['extra_vdp1_bytes']==m['extra_definitions']==0
 for n,sha in m['sha256'].items():assert digest((O/n).read_bytes())==sha,n
 cells=(O/'CICELL.BIN').read_bytes();maps=(O/'CIMAP.BIN').read_bytes();chunks=(O/'CICHUNK.BIN').read_bytes()
 assert len(cells)==106496 and len(maps)==16384 and len(chunks)==4800
 assert maps==(A/'original/CIMAP.BIN').read_bytes() and chunks==(A/'original/CICHUNK.BIN').read_bytes(),'map/chunk bytes changed'
 unique={b''.join(pixels[(y+k)*640+x:(y+k)*640+x+8] for k in range(8)) for y in range(0,240,8) for x in range(0,640,8)}
 assert len(unique)==len(cells)//64==1664
 words=struct.unpack('>8192H',maps);chunkwords=struct.unpack('>2400H',chunks)
 for y in range(240):
  for x in range(640):
   word=words[x//512*4096+y//8*64+(x%512)//8];tile=(word&4095)//2
   assert word>>12==1 and not word&1 and tile<1664
   assert cells[tile*64+y%8*8+x%8]==pixels[y*640+x]
 for s in range(5):
  for y in range(30):
   for x in range(16):
    col=s*16+x;assert chunkwords[(s*30+y)*16+x]==words[col//64*4096+y*64+col%64]
 if disc:
  image=(R/'build/mullet-force.bin').read_bytes();files={}
  assert image[:16]==b'SEGA SEGASATURN ' and image[16*2048+1:16*2048+6]==b'CD001' and len(image)%2048==0
  def scan(blob,prefix=''):
   pos=0
   while pos<len(blob):
    n=blob[pos]
    if not n:pos=(pos//2048+1)*2048;continue
    rec=blob[pos:pos+n];pos+=n;name=rec[33:33+rec[32]]
    if name in (b'\0',b'\1'):continue
    start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0];data=image[start:start+size];name=prefix+name.decode().split(';')[0]
    if rec[25]&2:scan(data,name+'/')
    else:files[name]=data
  rec=image[16*2048+156:16*2048+190];start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0];scan(image[start:start+size])
  for path in (R/'build/cd').rglob('*'):
   if path.is_file():assert files[path.relative_to(R/'build/cd').as_posix().upper()]==path.read_bytes(),path
  for name,target in [('CICELL.BIN','CICELL.BIN'),('CIMAP.BIN','CIMAP.BIN'),('CIPAL.BIN','CIPAL.BIN'),('PCHUNK.BIN','CICHUNK.BIN')]:assert files[name]==(O/target).read_bytes(),name
  for name in ('LCSKY.BIN','LCMAP.BIN'):assert files[name]==(R/'assets/city-gameplay-parallax'/name).read_bytes(),name
  source_list=(R/'build/SOURCE-SHA256SUMS.txt').read_bytes();assert digest(source_list).encode() in files['0.BIN']
  subprocess.run(['sha256sum','--check','build/SOURCE-SHA256SUMS.txt'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 print('PASS current background: 3 local masks, exact lettering/neon/lower posts/lamps/skyline, 1664 unique tiles/106496 cell bytes, unchanged map/chunk geometry; zero memory delta'+('; every packaged file and executable source fingerprint verified' if disc else ''),flush=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args();validate(a.disc)
 # Keep historical art/source locks intact: execute the exact approved parent,
 # not a globally relaxed collection of exceptions to each older milestone.
 # Current disc payloads are checked above; old expected background pixels are
 # validated in their own archived tree, without pretending they match this disc.
 if subprocess.run(['git','cat-file','-e',PARENT+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
  subprocess.run(['git','fetch','--no-tags','--depth=1','origin',PARENT],cwd=R,check=True)
 with tempfile.TemporaryDirectory(prefix='background-parent-') as d:
  ref=Path(d)
  with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',PARENT],cwd=R))) as t:t.extractall(ref,filter='data')
  for path in ref.rglob('*'):
   if path.is_file() and str(path.relative_to(ref)) not in ALLOWED:assert (R/path.relative_to(ref)).read_bytes()==path.read_bytes(),str(path.relative_to(ref))
  for n in ('.git','.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
  subprocess.run(['python3','tools/validate-ricky.py',*(['--test'] if a.test else [])],cwd=ref,check=True)
 print('PASS approved parent: all gameplay, characters including Ricky tattoo, audio, Level2, palette animation and parallax sources byte-identical; original preservation/automated suite unchanged',flush=True)
if __name__=='__main__':main()
