#!/usr/bin/env python3
"""Read-only Yabause checks of the production disc, palette pulse and both views."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess
from PIL import Image
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
for n in ('core','include','out'):p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--build',type=Path,default=R/'build');p.add_argument('--assets',type=Path,default=R/'assets')
a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True);assert not any(a.out.iterdir()),'use a fresh output directory'
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
 matches=[v for k,v in s.items() if k==name or k.startswith(name+'.lto_priv.')];assert len(matches)==1,(name,matches);return matches[0]
s=symbols(a.build/'game.elf');src=(R/'tests/runtime/playable-frontend.c').read_text()
b=src.index(' (void)index;',src.index('static int16_t input('));e=src.index('\nstatic unsigned read32',b)
src=src[:b]+''' (void)index;if(!controls || port || device!=RETRO_DEVICE_JOYPAD)return 0;
 if(id==RETRO_DEVICE_ID_JOYPAD_START && ((frame>=1000 && frame<1004)||(frame>=1020 && frame<1024)||(frame>=1450 && frame<1454)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && frame>=1120 && frame<1440)return 1;
 return 0;
}
'''+src[e:]
b=src.index(' if(review_only){if(frame!=299',src.index('static void video('));e=src.index(' snprintf(path',b)
src=src[:b]+''' if(frame!=1100 && frame!=1320 && frame!=1445 && frame!=1470 && frame!=1500 && frame!=1530)return;
'''+src[e:]
src=src.replace('const unsigned char *ram=NULL,*vram=NULL;','const unsigned char *ram=NULL,*vram=NULL,*vram2=NULL,*cram=NULL;')
src=src.replace('  pos+=12+len;', '''  if(!memcmp(state+pos,"VDP2",4)){
   unsigned registers=len-0x80000-0x1000-4;if(registers!=0x120)exit(5);
   vram2=state+pos+12+registers;cram=vram2+0x80000;
  }
  pos+=12+len;''')
src=src.replace(' fwrite(&hash,4,1,trace);',''' fwrite(&hash,4,1,trace);
 if(frame==1100 || frame==1320 || frame==1445 || frame==1470 || frame==1500 || frame==1530){
  char path[512];FILE *dump;unsigned values[]={frame,read32(ram,game_addr+offsetof(mf_game,camera)),read32(ram,ASSET_ERROR),read32(ram,game_addr+offsetof(mf_game,started)),read32(ram,game_addr+offsetof(mf_game,paused))};
  if(!vram2 || !cram)exit(5);
  snprintf(path,sizeof(path),"%s/state-%04u.bin",outdir,frame);dump=fopen(path,"wb");if(!dump)exit(3);
  fwrite(values,sizeof(values),1,dump);fwrite(vram2,0x80000,1,dump);fwrite(cram,0x1000,1,dump);fclose(dump);
 }
''')
unit=a.out/'frontend.c';unit.write_text(src);exe=a.out/'frontend';captures=a.out/'captures';captures.mkdir()
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-include',str(a.build/'build-info.h'),'-I'+str(a.include.resolve()),'-I'+str(R/'src'),f'-DASSET_ERROR={addr(s,"_asset_error")}',str(unit),'-ldl','-o',str(exe)],check=True)
with (a.out/'run.log').open('w') as log:subprocess.run([str(exe),str(a.core.resolve()),str((a.build/'mullet-force.cue').resolve()),str(captures),'1560','background',hex(addr(s,'_game')),hex(addr(s,'_idle_ticks'))],stdout=log,stderr=log,check=True)
def swapped(b):return b''.join(b[i:i+2][::-1] for i in range(0,len(b),2))
payloads=[(0,a.assets/'city-cleanup/CICELL.BIN'),(0x40000,a.assets/'city-cleanup/CIMAP.BIN'),(0x44000,a.assets/'city-gameplay-parallax/LCSKY.BIN'),(0x4c000,a.assets/'city-gameplay-parallax/LCMAP.BIN')]
phases=set();states=[]
for frame in (1100,1320,1445,1470,1500,1530):
 b=(captures/f'state-{frame:04}.bin').read_bytes();values=struct.unpack_from('<5I',b);states.append(values);assert values[2]==0 and values[3]==1,values
 vram=b[20:20+0x80000];cram=b[20+0x80000:]
 for offset,path in payloads:
  expected=path.read_bytes();actual=vram[offset:offset+len(expected)];assert actual in (expected,swapped(expected)),(frame,path)
 expected=(a.assets/'city-cleanup/CIPAL.BIN').read_bytes();actual=cram[514:514+510]
 # VDP2 save-state words can have host-endian storage. Normalize once against
 # the unchanged static prefix, then verify all static entries and pulse data.
 if actual[:478]!=expected[:478]:actual=swapped(actual)
 assert actual[:478]==expected[:478] and actual[494:]==expected[494:]
 phases.add(actual[478:494]);im=Image.open(captures/f'frame-{frame:04}.ppm');im.save(a.out/f'view-{frame:04}.png')
assert states[0][1]==0 and max(v[1] for v in states[1:])>=300,states
assert len(phases)>1,'neon palette is not pulsing'
report=dict(captures=[dict(frame=v[0],camera=v[1],asset_error=v[2],started=v[3],paused=v[4]) for v in states],verified_payloads=[str(p.relative_to(a.assets)) for off,p in payloads],neon_palette_phases=len(phases),scope='production disc, physical Start/Right/Pause inputs, no RAM writes, exact VDP2 cells/maps/sky and static palette; owner visual review and hardware approval pending')
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
