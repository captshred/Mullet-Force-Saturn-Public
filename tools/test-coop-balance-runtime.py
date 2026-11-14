#!/usr/bin/env python3
"""Read-only Yabause production cold boot, input-only co-op/jump evidence."""
from pathlib import Path
import argparse,json,struct,subprocess
from PIL import Image
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
for n in ('core','include','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True);assert not any(a.out.iterdir())
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
 v=[v for k,v in s.items() if k==name or k.startswith(name+'.lto_priv.')];assert len(v)==1,(name,v);return v[0]
s=symbols(R/'build/game.elf');src=(R/'tests/runtime/playable-frontend.c').read_text()
b=src.index(' (void)index;',src.index('static int16_t input('));e=src.index('\nstatic unsigned read32',b)
src=src[:b]+''' (void)index;if(!controls || port>1 || device!=RETRO_DEVICE_JOYPAD)return 0;
 if(id==RETRO_DEVICE_ID_JOYPAD_START && ((!port && ((frame>=1000 && frame<1004)||(frame>=1020 && frame<1024))) || (port && frame>=1350 && frame<1354)))return 1;
 /* Saturn A = libretro B, Saturn B = libretro A. */
 if(id==RETRO_DEVICE_ID_JOYPAD_B && ((frame>=1100 && frame<1102)||(frame>=1400 && frame<1402)||(frame>=1700 && frame<1790)||(frame>=1850 && frame<1940)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_A && ((frame>=1106 && frame<1108)||(frame>=1406 && frame<1408)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && !port && frame>=1500 && frame<1540)return 1;
 return 0;
}
'''+src[e:]
b=src.index(' if(review_only){if(frame!=299',src.index('static void video('));e=src.index(' snprintf(path',b);src=src[:b]+' if(frame<1090 || frame>2000 || frame%2)return;\n'+src[e:]
b=src.index(' fwrite(&frame,4,1,trace);');e=src.index('\n}',b)
src=src[:b]+''' fwrite(&frame,4,1,trace);
 #define FIELD(at) do{v=read32(ram,game_addr+(at));fwrite(&v,4,1,trace);}while(0)
 FIELD(offsetof(mf_game,camera));FIELD(offsetof(mf_game,stage));
 for(i=0;i<MF_PLAYERS;i++) {
  unsigned at=offsetof(mf_game,players)+i*sizeof(mf_player);
  FIELD(at+offsetof(mf_player,active));FIELD(at+offsetof(mf_player,attack));FIELD(at+offsetof(mf_player,height));FIELD(at+offsetof(mf_player,health));FIELD(at+offsetof(mf_player,x));FIELD(at+offsetof(mf_player,y));
 }
 for(i=0;i<MF_ENEMIES;i++) {
  unsigned at=offsetof(mf_game,enemies)+i*sizeof(mf_enemy);
  FIELD(at+offsetof(mf_enemy,state));FIELD(at+offsetof(mf_enemy,hp));FIELD(at+offsetof(mf_enemy,x));FIELD(at+offsetof(mf_enemy,y));FIELD(offsetof(mf_game,enemy_class)+i*sizeof(int));
 }
 v=read32(ram,ASSET_ERROR);fwrite(&v,4,1,trace);
 #undef FIELD
'''+src[e:]
unit=a.out/'frontend.c';unit.write_text(src);exe=a.out/'frontend';captures=a.out/'captures';captures.mkdir()
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Wno-unused-variable','-include',str(R/'build/build-info.h'),'-I'+str(a.include.resolve()),'-I'+str(R/'src'),f'-DASSET_ERROR={addr(s,"_asset_error")}',str(unit),'-ldl','-o',str(exe)],check=True)
with (a.out/'run.log').open('w') as log:subprocess.run([str(exe),str(a.core.resolve()),str(R/'build/mullet-force.cue'),str(captures),'2050','coop',hex(addr(s,'_game')),hex(addr(s,'_idle_ticks'))],stdout=log,stderr=log,check=True)
data=(captures/'trace.bin').read_bytes();rows=[struct.unpack_from('<31I',data,i) for i in range(0,len(data),124)]
assert all(r[-1]==0 for r in rows),'asset failure'
def count(r):return sum(r[15+j*5]!=0 for j in range(3))
solo=[r for r in rows if 1040<=r[0]<1350];coop=[r for r in rows if r[0]>1400]
assert max(map(count,solo))==2 and max(map(count,coop))==3
jumps=[]
for who in range(2):
 at=3+who*6
 pairs=[(b,c) for b,c in zip(rows,rows[1:]) if b[at+1]>0 and b[at+2]==0 and c[at+1]==0 and c[at+2]>0]
 assert pairs,('no punch jump',who)
 b,c=pairs[0];jumps.append(dict(player=who+1,before_frame=b[0],after_frame=c[0],punch_tick=b[at+1],height=c[at+2]))
 for label,r in [('punch',b),('jump',c)]:
  f=r[0] if r[0]%2==0 else r[0]+1
  Image.open(captures/f'frame-{f:04}.ppm').save(a.out/f'p{who+1}-{label}.png')
visible=[r for r in coop if r[0]%2==0 and count(r)==3 and all(0<r[15+j*5]<7 and r[16+j*5]>0 and 10<=r[17+j*5]//256-r[1]<=310 for j in range(3))]
assert visible,'no three enemies onscreen'
r=visible[0];Image.open(captures/f'frame-{r[0]:04}.ppm').save(a.out/'three-enemies.png')
report=dict(solo_max=max(map(count,solo)),coop_max=max(map(count,coop)),three_visible_frame=r[0],jump_cancels=jumps,asset_errors=sorted({r[-1] for r in rows}),scope='production native disc; fresh Yabause HLE boot, physical controller input only, no memory writes or save-state loading; hardware approval pending')
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
