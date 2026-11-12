#!/usr/bin/env python3
"""Optional native VDP1 HUD raster fixtures. Requires built Yabause core/include.
Makes TEST-ONLY binaries in --out with the actual loaders/draw_game and a fixture
update callback. Production source/branch/build remain untouched. No RAM writes.
The normal playable transition test is separate (test-legacy-sprite-runtime.py).
"""
from pathlib import Path
import argparse,io,json,os,re,struct,subprocess,tarfile
R=Path(__file__).resolve().parents[1];BASE='279e33d2f60645b12cf479ba3b096954565a0173'
p=argparse.ArgumentParser(description=__doc__)
for n in ('core','include','out'):p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--resume',action='store_true',help='reuse existing test-only builds and write fresh verified captures')
a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
assert a.resume or not any(a.out.iterdir()),'use a fresh output directory'
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
for label in ('phase3','phase4'):
 root=a.out/label
 if a.resume and (root/'build/game.elf').exists():
  original=subprocess.check_output(['git','show',BASE+':src/main.c'],cwd=R,text=True) if label=='phase3' else (R/'src/main.c').read_text()
  b=original.index('static void update(void)');e=original.index('void jo_main(void)',b)
  expected=original[:b]+(R/'tests/hud_panel/emulator-fixtures.inc').read_text()+'\n'+original[e:]
  assert (root/'src/main.c').read_text()==expected,'cached fixture renderer is stale; use a fresh output directory'
  for n in ('src/arcade_fx_config.h','src/animation_preview.c'):
   expected=subprocess.check_output(['git','show',BASE+':'+n],cwd=R) if label=='phase3' else (R/n).read_bytes()
   assert (root/n).read_bytes()==expected,'cached fixture config/loader is stale'
 if not (a.resume and (root/'build/game.elf').exists()):
  root.mkdir()
  with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as archive:archive.extractall(root,filter='data')
  if label=='phase4':
   # Copy only the reviewed runtime/build/accounting changes, not user scratch.
   for n in ('src/main.c','src/animation_preview.c','src/arcade_fx_config.h','tools/build-native.sh','tools/build-source-complete.sh','tools/audit-sprite-memory.py','assets/hud-panel-memory.json'):
    (root/n).write_bytes((R/n).read_bytes())
  for n in ('.deps','.git'):(root/n).symlink_to(R/n,target_is_directory=True)
  main=(root/'src/main.c').read_text();b=main.index('static void update(void)');e=main.index('void jo_main(void)',b)
  (root/'src/main.c').write_text(main[:b]+(R/'tests/hud_panel/emulator-fixtures.inc').read_text()+'\n'+main[e:])
  with (root/'native.log').open('w') as log:subprocess.run(['bash','tools/build-stage.sh','--native'],cwd=root,stdout=log,stderr=log,check=True)
 s=symbols(root/'build/game.elf');exe=root/'frontend';folder=root/('captures-verified' if a.resume else 'captures');folder.mkdir()
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-include',str(R/'build/build-info.h'),'-I'+str(inc),'-I'+str(R/'src'),f'-DHUD_CASE={addr(s,"_mf_hud_fixture_case")}',f'-DHUD_CLOCK={addr(s,"_mf_hud_fixture_clock")}',str(unit),'-ldl','-o',str(exe)],check=True)
 with (root/'emulator.log').open('w') as log:subprocess.run([str(exe),str(core),str(root/'build/mullet-force.cue'),str(folder),'3000','fixtures',hex(addr(s,'_game')),'0'],stdout=log,stderr=log,check=True)
 data=(folder/'fixture.bin').read_bytes();rows=[struct.unpack_from('<III',data,i) for i in range(0,len(data),12)]
 images={};cmds={}
 for frame,case,clock in rows:
  if frame%4 or not 6<=clock%12<=10 or case in images:continue
  path=folder/f'frame-{frame:04}.ppm'
  if not path.exists():continue
  images[case]=path.read_bytes();cmds[case]=(folder/f'commands-{frame:04}.bin').read_bytes()
 assert set(images)==set(range(180)),(label,len(images))
 captures[label]=images;commands[label]=cmds
mismatches=[case for case in range(180) if captures['phase3'][case]!=captures['phase4'][case]]
# Check real SGL command geometry for every unscaled overlay and health bar.
# VDP1 sprite table payload address is unchanged up to this panel registration.
def panel_commands(data):
 out=[];offset=0;seen=set()
 while offset not in seen:
  assert 0<=offset<=len(data)-32
  seen.add(offset);w=struct.unpack_from('>16H',data,offset)
  if w[0]&0x8000:return out
  if w[4]==0x3d00 and w[5] in (0x2028,0x0128):out.append(w)
  jump=(w[0]>>12)&7
  assert jump in (0,1),'unexpected command-list flow; inspect rather than count stale table entries'
  offset=w[1]*8 if jump else offset+32
 raise AssertionError('cyclic command chain')
overlays=0;bars=0
for case in range(180):
 old=panel_commands(commands['phase3'][case]);new=panel_commands(commands['phase4'][case]);assert len(old)==len(new)
 for x,y in zip(old,new):
  assert x[2:5]==y[2:5] and x[5]==0x2028 and y[5]==0x128
  if x[0]&15==1:
   assert x[0]==0xa01 and x[6:10]==(0,64,255,39)
   assert y[0]&15==3 and y[6:14]==(0xff81,45,128,45,128,84,0xff81,84)
   overlays+=1
  else:
   assert x[:5]==y[:5] and x[6:]==y[6:],'health bar destination commands differ'
   bars+=1
report=dict(command_scope='active VDP1 chains: follow ASSIGN, stop at END, ignore stale slots',cases=180,full_screen_mismatches=mismatches,overlay_command_pairs=overlays,health_bar_command_pairs=bars,scope='test-only native render fixtures: real loader/draw_game/SGL/VDP1/fonts/background; full screens for 1/2 players, all 5 modes, six health values, 3 score/kill cases; not a playable build or hardware claim')
(a.out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
assert not mismatches,'actual HUD raster mismatch'
