#!/usr/bin/env python3
"""Production world traversal, endpoint and checkpoint footage with normal inputs."""
from pathlib import Path
from PIL import Image
import argparse,json,struct,subprocess
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__)
for n in ('core','include','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True);assert not any(a.out.iterdir())
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
s=symbols(R/'build/game.elf');src=(R/'tests/runtime/playable-frontend.c').read_text();src=src.replace('static unsigned frame,pixel_format;','static FILE *world_trace;static unsigned frame,pixel_format;')
b=src.index(' (void)index;',src.index('static int16_t input('));e=src.index('\nstatic unsigned read32',b)
src=src[:b]+''' (void)index;if(!controls || port || device!=RETRO_DEVICE_JOYPAD)return 0;
 if(id==RETRO_DEVICE_ID_JOYPAD_START && ((frame>=1000 && frame<1004)||(frame>=1020 && frame<1024)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && ((frame>=1120 && frame<2300)||(frame>=2900 && frame<3650)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_LEFT && frame>=2300 && frame<2900)return 1;
 return 0;
}
'''+src[e:]
b=src.index(' if(review_only){if(frame!=299',src.index('static void video('));e=src.index(' snprintf(path',b);src=src[:b]+' if(frame<1100 || frame%20)return;\n'+src[e:]
src=src.replace(' fwrite(&hash,4,1,trace);',''' fwrite(&hash,4,1,trace);
 if(frame>=1100){
  unsigned values[]={frame,read32(ram,game_addr+offsetof(mf_game,camera)),read32(ram,game_addr+offsetof(mf_game,camera_floor)),read32(ram,game_addr+offsetof(mf_game,stage)),read32(ram,ASSET_ERROR),read32(ram,game_addr+offsetof(mf_game,players)+offsetof(mf_player,x)),read32(ram,game_addr+offsetof(mf_game,players)+offsetof(mf_player,health)),read32(ram,game_addr+offsetof(mf_game,enemies)+offsetof(mf_enemy,x)),read32(ram,game_addr+offsetof(mf_game,enemies)+offsetof(mf_enemy,hp)),read32(ram,game_addr+offsetof(mf_game,enemies)+sizeof(mf_enemy)+offsetof(mf_enemy,x)),read32(ram,game_addr+offsetof(mf_game,enemies)+sizeof(mf_enemy)+offsetof(mf_enemy,hp))};
  fwrite(values,sizeof(values),1,world_trace);
 }
''')
src=src.replace(' for(frame=0;frame<frames;frame++){',''' {char path[512];snprintf(path,sizeof(path),"%s/world.bin",outdir);world_trace=fopen(path,"wb");if(!world_trace)return 3;}
 for(frame=0;frame<frames;frame++){''').replace(' fclose(trace);',' fclose(trace);fclose(world_trace);')
unit=a.out/'frontend.c';unit.write_text(src);exe=a.out/'frontend';captures=a.out/'captures';captures.mkdir()
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-include',str(R/'build/build-info.h'),'-I'+str(a.include.resolve()),'-I'+str(R/'src'),f'-DASSET_ERROR={addr(s,"_asset_error")}',str(unit),'-ldl','-o',str(exe)],check=True)
with (a.out/'run.log').open('w') as log:subprocess.run([str(exe),str(a.core.resolve()),str(R/'build/mullet-force.cue'),str(captures),'3700','world',hex(addr(s,'_game')),hex(addr(s,'_idle_ticks'))],stdout=log,stderr=log,check=True)
data=(captures/'world.bin').read_bytes();rows=[struct.unpack_from('<11I',data,i) for i in range(0,len(data),44)];assert all(r[3]==r[4]==0 for r in rows),'stage or asset error'
assert max(r[1] for r in rows)==960 and max(r[2] for r in rows)==640
assert all(abs(a[1]-b[1])<=2 for a,b in zip(rows,rows[1:])), 'camera jump'
assert all(r[1]>=r[2] for r in rows)
frames=[r for r in rows if r[0]%20==0];chosen={}
conditions={
 '01-opening':lambda r:r[1]==0 and r[0]<1120,
 '02-past-original-boundary':lambda r:340<=r[1]<=500,
 '03-extended-active-enemies':lambda r:r[1]>640 and any(hp>0 and -32<=x//256-r[1]<=340 for x,hp in [(r[7],r[8]),(r[9],r[10])]),
 '04-temporary-endpoint':lambda r:r[1]==960 and r[5]//256>=1250 and r[6]>0,
 '05-checkpoint-backstop':lambda r:2300<r[0]<2900 and r[1]==r[2]==640 and r[5]//256<=670 and r[6]>0}
for name,condition in conditions.items():
 matches=[r for r in frames if condition(r)];assert matches,name
 r=matches[0];im=Image.open(captures/f'frame-{r[0]:04}.ppm');im.save(a.out/(name+'.png'));chosen[name]=dict(frame=r[0],camera=r[1],checkpoint=r[2],player_x=r[5]//256,health=r[6])
report=dict(max_camera=max(r[1] for r in rows),max_checkpoint=max(r[2] for r in rows),captures=chosen,scope='fresh production HLE boot, physical Start/Right/Left input only; no state writes, no world-skip/debug teleport; camera endpoint/backstop and live enemies; hardware approval pending')
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
