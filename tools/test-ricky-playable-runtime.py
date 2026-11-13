#!/usr/bin/env python3
"""Optional read-only Yabause repeated cold-start determinism check.
Pass the same production CUE and program as phase1 and phase2.
Requires an independently built libretro core and both matching native BIN/CUE
and SH COFF programs. No emulator RAM writes or readiness bypasses.
"""
from pathlib import Path
import argparse,json,re,struct,subprocess
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
for name in ('core','phase1-cue','phase1-program','phase2-cue','phase2-program','out'):p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--include',type=Path,required=True,help='directory containing libretro.h')
p.add_argument('--frames',type=int,default=2400)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
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
def address(s,name):
 values=[v for k,v in s.items() if k==name or k.startswith(name+'.lto_priv.')]
 assert len(values)==1,(name,values)
 return values[0]
# Saturn A/B/X map to libretro B/A/Y in this core.
controller=r'''
 unsigned clock=frame;
 if(ws_phase==3)clock=1800+ws_ticks;
 (void)index;if(!controls || port>1 || device!=RETRO_DEVICE_JOYPAD)return 0;
 if(id==RETRO_DEVICE_ID_JOYPAD_START && ((!port && ((frame>=1000 && frame<1004)||(frame>=1020 && frame<1024))) || (port==1 && frame>=1040 && frame<1044)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_Y && !port && frame>=1500 && frame<1504)return 1; /* approved development stage-skip input */
 if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && ((frame>=1100 && frame<1140)||(frame>=1160 && frame<1164)||(frame>=1170 && frame<1178)||(clock>=1900 && clock<1960)))return !port;
 if(id==RETRO_DEVICE_ID_JOYPAD_LEFT && ((frame>=1100 && frame<1140)||(frame>=1180 && frame<1210)||(clock>=2020 && clock<2080)))return port || frame>=1180;
 if(id==RETRO_DEVICE_ID_JOYPAD_UP && clock>=1900 && clock<1960)return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_DOWN && clock>=2020 && clock<2080)return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_A && frame>=1220 && frame<1224)return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_B && ((frame>=1172 && frame<1176)||(frame>=1230 && frame<1234)||(frame>=1260 && frame<1340)||(frame>=1360 && frame<1364)||(frame>=1380 && frame<1384)||(frame>=1400 && frame<1404)||(clock>=1800 && clock<1880)||(clock>=1980 && clock<2100)))return 1;
 return 0;
'''
source=(R/'tests/runtime/playable-frontend.c').read_text()
begin=source.index(' (void)index;',source.index('static int16_t input('));end=source.index('\nstatic unsigned read32',begin)
source=source[:begin]+controller+'}\n'+source[end:]
source=source.replace('#include "game.h"','#include "game.h"\n#include "wingsuit.h"\nstatic FILE *full_trace;\nstatic unsigned ws_phase,ws_ticks;')
begin=source.index(' if(review_only){if(frame!=299',source.index('static void video('));end=source.index(' snprintf(path',begin)
source=source[:begin]+' if(frame<1100 || (frame<1800 && frame%20))return;\n'+source[end:]
source=source.replace(' fwrite(&hash,4,1,trace);', ''' fwrite(&hash,4,1,trace);
 fwrite(&frame,4,1,full_trace);
 for(i=0;i<sizeof(mf_game);i+=4){v=read32(ram,game_addr+i);fwrite(&v,4,1,full_trace);}
 for(i=0;i<sizeof(mf_wingsuit);i+=4){v=read32(ram,MF_WS_ADDRESS+i);fwrite(&v,4,1,full_trace);}
 ws_ticks=read32(ram,MF_WS_ADDRESS+offsetof(mf_wingsuit,ticks));\n ws_phase=read32(ram,MF_WS_PHASE);\n v=ws_phase;fwrite(&v,4,1,full_trace);
 v=read32(ram,MF_WS_ERROR);fwrite(&v,4,1,full_trace);
 v=read32(ram,MF_SPRITE_COUNT);fwrite(&v,4,1,full_trace);
''')
source=source.replace(' for(frame=0;frame<frames;frame++){',''' {char path[512];snprintf(path,sizeof(path),"%s/full-trace.bin",outdir);full_trace=fopen(path,"wb");if(!full_trace)return 3;}
 fprintf(stderr,"LAYOUT|%zu|%zu|%zu|%zu\\n",sizeof(mf_game),sizeof(mf_wingsuit),offsetof(mf_game,stage),offsetof(mf_wingsuit,ticks));
 for(frame=0;frame<frames;frame++){''').replace(' fclose(trace);',' fclose(trace);fclose(full_trace);')
unit=a.out/'frontend.c';unit.write_text(source)
records={};images={};summaries={}
for label in ('phase1','phase2'):
 folder=a.out/label;folder.mkdir(exist_ok=True)
 # Refuse warm save directories so a rerun cannot silently become a warm boot.
 assert not (folder/'mullet-force.srm').exists(), 'use a fresh --out directory'
 s=symbols(getattr(a,label+'_program'));ws=address(s,'_shooter')
 phase=[v for k,v in s.items() if k.startswith('_phase.lto_priv.') and ws-256<v<ws];assert len(phase)==1
 error=address(s,'_error');exe=a.out/('frontend-'+label)
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-include',str(R/'build/build-info.h'),'-I'+str(a.include),'-I'+str(R/'src'),f'-DMF_WS_ADDRESS={ws}',f'-DMF_WS_PHASE={phase[0]}',f'-DMF_WS_ERROR={error}',f'-DMF_SPRITE_COUNT={address(s,"___jo_sprite_id")}',str(unit),'-ldl','-o',str(exe)],check=True)
 with (folder/'run.log').open('w') as log:
  subprocess.run([str(exe.resolve()),str(a.core.resolve()),str(getattr(a,label+'_cue').resolve()),str(folder.resolve()),str(a.frames),'run',hex(address(s,'_game')),hex(address(s,'_idle_ticks'))],stdout=log,stderr=log,check=True)
 layout=re.search(r'LAYOUT\|(\d+)\|(\d+)\|(\d+)\|(\d+)',(folder/'run.log').read_text());assert layout
 ng,nw,stage_at,ticks_at=map(int,layout.groups());size=4+ng+nw+12;data=(folder/'full-trace.bin').read_bytes();assert len(data)%size==0
 rows={struct.unpack_from('<I',data,i)[0]:data[i+4:i+size] for i in range(0,len(data),size)}
 records[label]=rows;images[label]={int(p.stem.split('-')[1]):p.read_bytes() for p in folder.glob('frame-*.ppm')}
 states=[(f,struct.unpack_from('<i',r,stage_at)[0],*struct.unpack_from('<iii',r,ng+nw)) for f,r in rows.items()]
 summaries[label]=dict(stages=sorted({v[1] for v in states}),runtime_phases=sorted({v[2] for v in states}),errors=sorted({v[3] for v in states}),first_level2_gameplay=next((v[0] for v in states if v[2]==3),None),last_stage=states[-1][1],last_phase=states[-1][2],last_sprite_id=states[-1][4],last_wingsuit_ticks=struct.unpack_from('<I',rows[max(rows)],ng+ticks_at)[0])
 summaries[label]['level2_gameplay']=any(v[2]==3 for v in states)
 records[label]={f:r[:-4] for f,r in rows.items() if f>=1100}
ng,nw,stage_at,ticks_at=map(int,layout.groups())
state_diffs=[f for f,r in records['phase1'].items() if r!=records['phase2'][f]]
image_diffs=sorted(f for f,r in images['phase1'].items() if r!=images['phase2'][f])
# Loading completes one frame earlier with fewer retired definitions. Compare
# Level 2 simulation at equal tick numbers with stage-local controller schedules.
def stage_states(label):
 return {struct.unpack_from('<I',r,ng+ticks_at)[0]:r for r in records[label].values() if struct.unpack_from('<i',r,ng+nw)[0]==3 and struct.unpack_from('<I',r,ng+ticks_at)[0]>0}
b1,b2=stage_states('phase1'),stage_states('phase2');common=sorted(b1.keys()&b2.keys())
ws_diffs=[t for t in common if b1[t]!=b2[t]]
# Sample every frame in Level 2 so both runs have matching tick images.
def stage_images(label):
 return {struct.unpack_from('<I',records[label][f],ng+ticks_at)[0]:pixels for f,pixels in images[label].items() if struct.unpack_from('<i',records[label][f],ng+nw)[0]==3 and struct.unpack_from('<I',records[label][f],ng+ticks_at)[0]>10}
i1,i2=stage_images('phase1'),stage_images('phase2');iticks=sorted(i1.keys()&i2.keys());image_tick_diffs=[t for t in iticks if i1[t]!=i2[t]]
# Level 1 and stage clear are strictly wall-frame aligned; no tolerance there.
level1_diffs=[f for f in state_diffs if f<1700]
level1_images=[f for f in image_diffs if f<1700]
report=dict(builds=summaries,level1_state_snapshots=600,level1_state_mismatches=level1_diffs,level1_image_count=sum(f<1700 for f in images['phase1']),level1_image_mismatches=level1_images,wall_frame_state_mismatches=state_diffs,wall_frame_image_mismatches=image_diffs,level2_common_ticks=len(common),level2_state_mismatches=ws_diffs,level2_common_images=len(iticks),level2_image_mismatches=image_tick_diffs,scope='fresh HLE boots; physical controller inputs; approved development X stage skip at 1500; real settling/clear/load/readiness; Level2 inputs relative to gameplay ticks; no RAM writes; no natural 40-KO run or hardware/audio-listening claim')
(a.out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
assert not level1_diffs and not level1_images and not ws_diffs and not image_tick_diffs and len(iticks)>100, 'emulator mismatch: inspect comparison.json and captures'
assert all(v['level2_gameplay'] and v['errors']==[0] and v['last_wingsuit_ticks']>0 for v in summaries.values()), 'Level 2 did not reach healthy gameplay'
