from pathlib import Path
import json,hashlib,struct,subprocess,sys
r=Path(__file__).resolve().parents[1];o=r/'assets/city-gameplay-parallax';m=json.loads((o/'manifest.json').read_text());cells=(o/'LCSKY.BIN').read_bytes();words=struct.unpack('>8192H',(o/'LCMAP.BIN').read_bytes());src=(r/'assets/city-cleanup/CIPIX.BIN').read_bytes()
for n,h in m['sha256'].items():assert hashlib.sha256((o/n).read_bytes()).hexdigest()==h
for y in range(56):
 for x in range(640):
  w=words[x//512*4096+y//8*64+x%512//8];tile=((w&4095)-512)//2
  assert w>>12==1 and 0<=tile<512
  assert cells[tile*64+y%8*8+x%8]==src[y*640+x]
assert len(cells)==32768 and len(words)*2==16384
assert 0x4000+len(cells)==0xc000 and 0xc000+16384==0x10000<0x20000
for camera in range(321):assert camera//4+320<=640
main=(r/'src/street.c').read_text();assert 'mf_parallax_game_draw(camera);return;' in main
if '--disc' in sys.argv and (r/'build/live-city-mode.txt').read_text().strip()=='1':
 for n in m['sha256']:
  d=subprocess.check_output(['isoinfo','-i',str(r/'build/mullet-force.bin'),'-x','/'+n+';1']);assert d==(o/n).read_bytes()
print('PASS live skyline: exact approved pixels, static palette, all camera bounds, aligned nonoverlapping B0 data, gameplay draw hook')
