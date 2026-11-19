#!/usr/bin/env python3
"""Native production co-op traversal/hold/combat/backstop with read-only traces."""
from pathlib import Path
import argparse,json,struct,subprocess
from PIL import Image
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
for n in ('core','include','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True);assert not any(a.out.iterdir())
# Use the approved COFF parser without executing its command-line runner.
helper=(R/'tools/test-coop-balance-runtime.py').read_text();scope={'struct':struct};exec(helper[helper.index('def symbols('):helper.index('s=symbols(')],scope);symbols=scope['symbols'];addr=scope['addr']
manifest=json.loads((R/'assets/level1-intersection/manifest.json').read_text())
camera_max=manifest['width']-320
frames=4600
s=symbols(R/'build/game.elf');src=(R/'tests/runtime/playable-frontend.c').read_text()
src=src.replace('static unsigned frame,pixel_format;','static unsigned seen_camera,travel_phase,hold_steps;static unsigned frame,pixel_format;')
b=src.index(' (void)index;',src.index('static int16_t input('));e=src.index('\nstatic unsigned read32',b)
src=src[:b]+''' (void)index;if(!controls || port>1 || device!=RETRO_DEVICE_JOYPAD)return 0;
 if(id==RETRO_DEVICE_ID_JOYPAD_START && ((!port && ((frame>=1000 && frame<1004)||(frame>=1020 && frame<1024))) || (port && frame>=1040 && frame<1044)))return 1;
 if(frame<1100)return 0;
 if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && (travel_phase==0 || travel_phase==2))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_LEFT && travel_phase==4)return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_B && (travel_phase==1 || travel_phase==3 || travel_phase==5 || (frame+port*17)%60<3))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_A && travel_phase!=1 && travel_phase!=3 && travel_phase!=5 && (frame+port*17)%60>=6 && (frame+port*17)%60<9)return 1;
 return 0;
}
'''+src[e:]
b=src.index(' if(review_only){if(frame!=299',src.index('static void video('));e=src.index(' snprintf(path',b);src=src[:b]+' if(frame<1100 || frame%4)return;\n'+src[e:]
b=src.index(' fwrite(&frame,4,1,trace);');e=src.index('\n}',b)
src=src[:b]+''' fwrite(&frame,4,1,trace);
 #define FIELD(at) do{v=read32(ram,game_addr+(at));fwrite(&v,4,1,trace);}while(0)
 FIELD(offsetof(mf_game,camera));seen_camera=v;
 FIELD(offsetof(mf_game,camera_floor));FIELD(offsetof(mf_game,stage));
 v=read32(ram,ASSET_ERROR);fwrite(&v,4,1,trace);
 v=read32(ram,PARALLAX_ERROR);fwrite(&v,4,1,trace);
 for(i=0;i<MF_PLAYERS;i++) {
  unsigned at=offsetof(mf_game,players)+i*sizeof(mf_player);
  FIELD(at+offsetof(mf_player,active));FIELD(at+offsetof(mf_player,attack));FIELD(at+offsetof(mf_player,height));FIELD(at+offsetof(mf_player,health));FIELD(at+offsetof(mf_player,x));FIELD(at+offsetof(mf_player,y));
 }
 for(i=0;i<MF_ENEMIES;i++) {
  unsigned at=offsetof(mf_game,enemies)+i*sizeof(mf_enemy);
  FIELD(at+offsetof(mf_enemy,state));FIELD(at+offsetof(mf_enemy,hp));FIELD(at+offsetof(mf_enemy,x));FIELD(at+offsetof(mf_enemy,y));FIELD(offsetof(mf_game,enemy_class)+i*sizeof(int));
 }
 if(travel_phase==0 && seen_camera>=1400){travel_phase=1;hold_steps=0;}
 if(travel_phase==1 && ++hold_steps>=360)travel_phase=2;
 if(travel_phase==2 && seen_camera==MF_WORLD_CAMERA_MAX){travel_phase=3;hold_steps=0;}
 if(travel_phase==3 && ++hold_steps>=120)travel_phase=4;
 if(travel_phase==4 && seen_camera==1280)travel_phase=5;
 FIELD(offsetof(mf_game,ticks));
 v=read32(ram,WORLD_CACHE_POINTER);fwrite(&v,4,1,trace);
 v=v?read32(ram,v-4):0;fwrite(&v,4,1,trace);
 #undef FIELD
'''+src[e:]
unit=a.out/'frontend.c';unit.write_text(src);exe=a.out/'frontend';captures=a.out/'captures';captures.mkdir()
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Wno-unused-variable','-include',str(R/'build/build-info.h'),'-I'+str(a.include.resolve()),'-I'+str(R/'src'),f'-DASSET_ERROR={addr(s,"_asset_error")}',f'-DPARALLAX_ERROR={addr(s,"_live_error")}',f'-DWORLD_CACHE_POINTER={addr(s,"_world_block_cache")}',str(unit),'-ldl','-o',str(exe)],check=True)
with (a.out/'run.log').open('w') as log:subprocess.run([str(exe),str(a.core.resolve()),str(R/'build/mullet-force.cue'),str(captures),str(frames),'traverse',hex(addr(s,'_game')),hex(addr(s,'_idle_ticks'))],stdout=log,stderr=log,check=True)
data=(captures/'trace.bin').read_bytes();rows=[struct.unpack_from('<36I',data,i) for i in range(0,len(data),144)]
rows=[r for r in rows if r[0]>=1100]
assert all(r[3]==r[4]==r[5]==0 for r in rows),'stage/asset/parallax error'
assert max(r[1] for r in rows)==camera_max and max(r[2] for r in rows)==1280,'endpoint not reached'
assert any(r[1]==1280 and r[0]>2800 for r in rows) and all(abs(b[1]-c[1])<=2*max(1,c[33]-b[33]) for b,c in zip(rows,rows[1:])),'camera speed/backstop'
def count(r):return sum(r[18+j*5]!=0 for j in range(3))
assert max(map(count,rows))==3 and all(count(r)<=3 for r in rows)
lot=[r for r in rows if r[6] and r[12] and r[9]>0 and r[15]>0 and
     r[10]>2240*256 and r[16]>2240*256]
assert lot,'both players must reach the parking lot alive together'
assert any(0<r[18+j*5]<7 and 2240<r[20+j*5]//256<r[1]+320
           for r in lot for j in range(3)),'no active enemy in the parking lot'
visible=[r for r in rows if r[0]%4==0 and 1380<=r[1]<=1460 and r[6] and r[12] and r[9]>0 and r[15]>0 and count(r)==3 and sum(0<r[18+j*5]<7 and -10<=r[20+j*5]//256-r[1]<=330 for j in range(3))>=2]
assert visible,'no mixed combat capture at intersection'
def quality(r):return sum(r[22+j*5]==2 and r[19+j*5]>0 for j in range(3))*10+sum(10<r[20+j*5]//256-r[1]<310 for j in range(3))
chosen=max(visible,key=quality);Image.open(captures/f'frame-{chosen[0]:04}.ppm').save(a.out/'intersection-gameplay.png')
for name,predicate in [('transition',lambda r:1000<=r[1]<=1040),('diagonal',lambda r:1750<=r[1]<=1800),('parking-lot',lambda r:2060<=r[1]<=2120),('endpoint',lambda r:r[1]==camera_max),('checkpoint-backstop',lambda r:r[1]==1280 and r[0]>2800)]:
 matches=[r for r in rows if r[0]%4==0 and predicate(r)];assert matches,name
 r=matches[0];Image.open(captures/f'frame-{r[0]:04}.ppm').save(a.out/(name+'.png'))
# Uninterrupted native combat excerpt around the selected intersection frame.
first=max(1100,chosen[0]-40);first=(first//4)*4;last=min(frames-4,first+120)
ims=[Image.open(captures/f'frame-{f:04}.ppm').convert('RGB') for f in range(first,last+1,4)]
ims[0].save(a.out/'intersection-combat.gif',save_all=True,append_images=ims[1:],duration=67,loop=0,optimize=True)
payload=manifest['background_heap_bytes']
offset=payload-manifest['decode_cache_heap_bytes']
assert all(r[34]>offset and r[34]-offset+payload<=0x060c0000 for r in rows),'CPU background placement'
assert all(r[34]==rows[0][34] for r in rows),'background ownership changed during Level 1'
report=dict(cpu_background_address=hex(rows[-1][34]-offset),cpu_background_requested_bytes=payload,max_camera=max(r[1] for r in rows),max_checkpoint=max(r[2] for r in rows),last_camera=rows[-1][1],max_enemies=max(map(count,rows)),capture_frame=chosen[0],capture_camera=chosen[1],capture_enemy_classes=[chosen[22+j*5] for j in range(3)],asset_errors=sorted({r[4] for r in rows}),parallax_errors=sorted({r[5] for r in rows}),camera_max_trace_delta=max(abs(b[1]-c[1]) for b,c in zip(rows,rows[1:])),scope='production native disc; fresh unmodified Yabause HLE core; physical two-player controller input only; read-only camera feedback chooses a 360-tick combat stop then endpoint/reverse; no RAM writes, healing, teleport or save-state loading; hardware approval pending')
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
