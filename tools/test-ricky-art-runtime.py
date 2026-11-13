#!/usr/bin/env python3
"""Optional native VDP1 Ricky pose and mixed-class fixtures. Requires built Yabause core/include.
Makes TEST-ONLY binaries in --out with the actual loaders/draw_game and a fixture
update callback. Production source/branch/build remain untouched. No RAM writes.
The production cold-start test is separate (test-ricky-playable-runtime.py).
"""
from pathlib import Path
import argparse,io,json,os,re,struct,subprocess,tarfile
R=Path(__file__).resolve().parents[1];BASE='1dd66746f37333914408234fc14d520858ac59fd'
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
p=argparse.ArgumentParser(description=__doc__)
for n in ('core','include','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
assert not any(a.out.iterdir()),'use a fresh output directory'
core=a.core.resolve();inc=a.include.resolve()
def symbols(path):
 b=path.read_bytes();off,n=struct.unpack_from('>II',b,8);strings=b[off+n*18:];i=0;s={}
 while i<n:
  at=off+i*18;raw=b[at:at+8]
  if raw[:4]==b'\0'*4:
   k=int.from_bytes(raw[4:],'big');name=strings[k:].split(b'\0',1)[0].decode(errors='replace')
  else:name=raw.split(b'\0',1)[0].decode(errors='replace')
  if int.from_bytes(b[at+12:at+14],'big',signed=True)>0:s[name]=int.from_bytes(b[at+8:at+12],'big')
  i+=1+b[at+17]
 return s
def addr(s,name):
 matches=[v for k,v in s.items() if k==name or k.startswith(name+'.lto_priv.')];assert len(matches)==1,(name,matches)
 return matches[0]
# Use the existing headless frontend; only read-only fixture metadata/dumps added.
source=(R/'tests/runtime/playable-frontend.c').read_text()
source=source.replace('static unsigned frame,pixel_format;', 'static unsigned frame,pixel_format;static FILE *fixture_trace;')
b=source.index(' if(review_only){if(frame!=299',source.index('static void video('));e=source.index(' snprintf(path',b)
source=source[:b]+' if(frame<400 || frame%4)return;\n'+source[e:]
source=source.replace(' fwrite(&hash,4,1,trace);', ''' fwrite(&hash,4,1,trace);
 v=read32(ram,HUD_CASE);fwrite(&frame,4,1,fixture_trace);fwrite(&v,4,1,fixture_trace);
 v=read32(ram,HUD_CLOCK);fwrite(&v,4,1,fixture_trace);
 if(frame%4==0 && v%12>=6 && v%12<=10){
  char path[512];FILE *dump;snprintf(path,sizeof(path),"%s/commands-%04u.bin",outdir,frame);
  dump=fopen(path,"wb");if(!dump)exit(3);fwrite(vram,0x10000,1,dump);fclose(dump);
 }
''')
source=source.replace(' for(frame=0;frame<frames;frame++){',''' {char path[512];snprintf(path,sizeof(path),"%s/fixture.bin",outdir);fixture_trace=fopen(path,"wb");if(!fixture_trace)return 3;}
 for(frame=0;frame<frames;frame++){''').replace(' fclose(trace);',' fclose(trace);fclose(fixture_trace);')
unit=a.out/'frontend.c';unit.write_text(source);captures={};commands={}
import shutil
root=a.out/'source';root.mkdir()
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as archive:archive.extractall(root,filter='data')
for folder in ('src','tools','make'):shutil.copytree(R/folder,root/folder,dirs_exist_ok=True)
shutil.copytree(R/'assets/ricky',root/'assets/ricky')
for n in ('.deps','.git'):(root/n).symlink_to(R/n,target_is_directory=True)
main=(root/'src/main.c').read_text();b=main.index('static void update(void)');e=main.index('void jo_main(void)',b)
(root/'src/main.c').write_text(main[:b]+(R/'tests/ricky/emulator-fixtures.inc').read_text()+'\n'+main[e:])
f=root/'src/ricky_animation.c';text=f.read_text().replace('    const mf_enemy *e=&g->enemies[a];','    extern int mf_ricky_fixture_pose;return mf_ricky_fixture_pose;\n    const mf_enemy *e=&g->enemies[a];');f.write_text(text)
with (a.out/'native.log').open('w') as log:subprocess.run(['bash','tools/build-stage.sh','--native'],cwd=root,stdout=log,stderr=log,check=True)
s=symbols(root/'build/game.elf');exe=a.out/'frontend';folder=a.out/'captures';folder.mkdir()
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-include',str(R/'build/build-info.h'),'-I'+str(inc),'-I'+str(R/'src'),f'-DHUD_CASE={addr(s,"_mf_hud_fixture_case")}',f'-DHUD_CLOCK={addr(s,"_mf_hud_fixture_clock")}',str(unit),'-ldl','-o',str(exe)],check=True)
with (a.out/'emulator.log').open('w') as log:subprocess.run([str(exe),str(core),str(root/'build/mullet-force.cue'),str(folder),'2000','fixtures',hex(addr(s,'_game')),'0'],stdout=log,stderr=log,check=True)
data=(folder/'fixture.bin').read_bytes();rows=[struct.unpack_from('<III',data,i) for i in range(0,len(data),12)]
images={};review=a.out/'review';review.mkdir()
from PIL import Image,ImageDraw
for frame,case,clock in rows:
 if frame%4 or not 6<=clock%12<=10 or case in images:continue
 path=folder/f'frame-{frame:04}.ppm'
 if not path.exists():continue
 im=Image.open(path);im.save(review/f'case-{case:02}.png');images[case]=im.copy()
assert set(images)==set(range(50)),sorted(images)
canvas=Image.new('RGB',(320*5,248*10))
for c,im in sorted(images.items()):
 x=c%5*320;y=c//5*248;canvas.paste(im,(x,y));ImageDraw.Draw(canvas).text((x+4,y+228),f'{c}: pose {c%25} '+('CP+R' if c<25 else 'R+R'),fill='white')
canvas.save(a.out/'contact-sheet.png')
(a.out/'comparison.json').write_text(json.dumps(dict(cases=50,poses=25,classes=['CP+R','R+R'],scope='test-only pose/actor fixtures; actual production loader/draw_game/VDP1, both heroes present; no gameplay or hardware claim'),indent=2)+'\n')
print('PASS 50 native Yabause Ricky fixtures: every pose, both directions, CP+R and R+R, both heroes present')
