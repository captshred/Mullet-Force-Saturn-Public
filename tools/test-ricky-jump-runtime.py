#!/usr/bin/env python3
"""Production normal-combat capture: input bot only, no NPC/RAM writes."""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,json,struct,subprocess
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__)
for n in ('core','include','out'):p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--frames',type=int,default=18000)
p.add_argument('--analyze-only',action='store_true',help='regenerate previews from an existing completed capture')
p.add_argument('--review-air-frame',type=int,default=0,help='choose a naturally captured jump near this frame for visual clarity')
a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True);assert a.analyze_only or not any(a.out.iterdir())
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
captures=a.out/'captures'
if not a.analyze_only:
 s=symbols(R/'build/game.elf');src=(R/'tests/runtime/playable-frontend.c').read_text();src=src.replace('static unsigned frame,pixel_format;','static FILE *jump_trace;static unsigned capture_gate,bot_frame=~0u,bot_rng=1,bot_mask[2];static unsigned frame,pixel_format;')
 b=src.index(' (void)index;',src.index('static int16_t input('));e=src.index('\nstatic unsigned read32',b)
 src=src[:b]+''' (void)index;if(!controls || port>1 || device!=RETRO_DEVICE_JOYPAD)return 0;
  if(id==RETRO_DEVICE_ID_JOYPAD_START && ((!port && ((frame>=1000 && frame<1004)||(frame>=1020 && frame<1024))) || (port && frame>=1040 && frame<1044)))return 1;
  if(frame<1044)return 0;
  {unsigned t=frame-1044,phase=(t+port*70)%900;
  if(bot_frame!=frame){unsigned p;bot_frame=frame;for(p=0;p<2;p++){bot_rng=bot_rng*1664525u+1013904223u;bot_mask[p]=bot_rng>>28;}}
  if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && phase<300)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_LEFT && phase>=300 && phase<600)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_UP && (t+port*37)%360<32)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_DOWN && (t+port*37)%360>=180 && (t+port*37)%360<212)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_B && ((t+port*13)%400<110 || bot_mask[port]<5))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_A && (t+port*31)%95<2)return 1;
  }return 0;
 }
 '''+src[e:]
 b=src.index(' if(review_only){if(frame!=299',src.index('static void video('));e=src.index(' snprintf(path',b);src=src[:b]+' if(frame<1044 || (!capture_gate && frame%60) || (capture_gate && frame%2))return;\n'+src[e:]
 src=src.replace(' fwrite(&hash,4,1,trace);',''' fwrite(&hash,4,1,trace);
  if(frame>=1044){
   unsigned values[29]={0},i;values[0]=frame;values[1]=read32(ram,ASSET_ERROR);values[2]=read32(ram,game_addr+offsetof(mf_game,camera));values[3]=read32(ram,game_addr+offsetof(mf_game,stage));values[4]=read32(ram,game_addr+offsetof(mf_game,stage_kills));capture_gate=0;
   for(i=0;i<2;i++){
    unsigned e=game_addr+offsetof(mf_game,enemies)+i*sizeof(mf_enemy),j=game_addr+offsetof(mf_game,ricky_jump)+i*sizeof(mf_ricky_jump),k=5+i*12;
    values[k]=read32(ram,game_addr+offsetof(mf_game,enemy_class)+4*i);
    values[k+1]=read32(ram,e+offsetof(mf_enemy,state));values[k+2]=read32(ram,e+offsetof(mf_enemy,timer));
    values[k+3]=read32(ram,e+offsetof(mf_enemy,x));values[k+4]=read32(ram,e+offsetof(mf_enemy,y));values[k+5]=read32(ram,e+offsetof(mf_enemy,facing));
    values[k+6]=read32(ram,j+offsetof(mf_ricky_jump,active));values[k+7]=read32(ram,j+offsetof(mf_ricky_jump,height));values[k+8]=read32(ram,j+offsetof(mf_ricky_jump,last));
    values[k+9]=read32(ram,game_addr+offsetof(mf_game,ricky_punch)+4*i);values[k+10]=read32(ram,e+offsetof(mf_enemy,hp));values[k+11]=read32(ram,game_addr+offsetof(mf_game,players)+i*sizeof(mf_player)+offsetof(mf_player,health));
    if(values[k]==2 && values[k+1]>=3 && values[k+1]<=5)capture_gate=1;
   }
   fwrite(values,sizeof(values),1,jump_trace);
  }
 ''')
 src=src.replace(' for(frame=0;frame<frames;frame++){',''' {char path[512];snprintf(path,sizeof(path),"%s/jump.bin",outdir);jump_trace=fopen(path,"wb");if(!jump_trace)return 3;}
  for(frame=0;frame<frames;frame++){''').replace(' fclose(trace);',' fclose(trace);fclose(jump_trace);')
 unit=a.out/'frontend.c';unit.write_text(src);exe=a.out/'frontend';captures=a.out/'captures';captures.mkdir()
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-include',str(R/'build/build-info.h'),'-I'+str(a.include.resolve()),'-I'+str(R/'src'),f'-DASSET_ERROR={addr(s,"_asset_error")}',str(unit),'-ldl','-o',str(exe)],check=True)
 with (a.out/'run.log').open('w') as log:subprocess.run([str(exe),str(a.core.resolve()),str(R/'build/mullet-force.cue'),str(captures),str(a.frames),'normal-combat',hex(addr(s,'_game')),hex(addr(s,'_idle_ticks'))],stdout=log,stderr=log,check=True)
data=(captures/'jump.bin').read_bytes();rows=[struct.unpack_from('<29I',data,i) for i in range(0,len(data),116)];assert all(r[1]==r[3]==0 for r in rows)
counts={'punch':0,'standing_chain':0,'jump_chain':0};examples={};previous=[None,None];launches=[]
for r in rows:
 for slot in range(2):
  k=5+12*slot;state=r[k+1];kind='jump_chain' if r[k+6] else 'punch' if r[k+9] else 'standing_chain'
  if r[k]==2 and state==3 and previous[slot]!=3:counts[kind]+=1
  if r[k]==2 and state in (3,4,5) and 40<=r[k+3]//256-r[2]<=280:
   key=(kind,state)
   if key not in examples and (captures/f'frame-{r[0]:04}.ppm').exists():examples[key]=r[0]
  previous[slot]=state
assert all(counts.values()),counts
# Find one naturally selected complete jump with launch/air/landing captures.
for r in sorted(rows,key=lambda r:abs(r[0]-(a.review_air_frame-25))) if a.review_air_frame else rows:
 for slot in range(2):
  k=5+12*slot
  if r[k]==2 and r[k+6] and r[k+1]==3:
   seq=[]
   for wanted in (3,4,5):
    hits=[q for q in rows if r[0]<=q[0]<r[0]+90 and q[k]==2 and q[k+6] and q[k+1]==wanted and 0<=q[k+3]//256-q[2]<=320 and (captures/f'frame-{q[0]:04}.ppm').exists()]
    if not hits:break
    seq.append(hits[len(hits)//2][0])
   if len(seq)==3:
    poses={q[0]:q for q in rows if q[0] in seq}
    if abs(poses[seq[1]][k+3]-poses[seq[0]][k+3])>=8*256:launches=seq;break
 if launches:break
assert launches,'no complete naturally selected on-screen jump'
for label,frame in zip(('launch','airborne','landing'),launches):Image.open(captures/f'frame-{frame:04}.ppm').save(a.out/(label+'.png'))
for kind in counts:
 frame=examples.get((kind,4),examples.get((kind,3)));assert frame,kind
 Image.open(captures/f'frame-{frame:04}.ppm').save(a.out/(kind+'.png'))
def gif(name,start,end):
 frames=[]
 for frame in range(start,end+1):
  f=captures/f'frame-{frame:04}.ppm'
  if f.exists():frames.append(Image.open(f).convert('RGB').resize((640,480),Image.Resampling.NEAREST))
 assert frames;frames[0].save(a.out/name,save_all=True,append_images=frames[1:],duration=34,loop=0)
gif('jump-sequence.gif',launches[0]-6,launches[-1]+8)
# Three clips sampled from one continuous unforced production run.
for kind in counts:
 frame=examples.get((kind,4),examples.get((kind,3)));gif(kind+'.gif',frame-12,frame+24)
report=dict(frames=a.frames,attack_commitments=counts,preview_selection="actual unforced footage; requested review-air-frame="+str(a.review_air_frame),jump_phase_frames=dict(zip(('launch','airborne','landing'),launches)),max_kos=max(r[4] for r in rows),scope='production fresh HLE boot; normal two-player patrol/combat inputs; no RAM writes, NPC state forcing, attack forcing or debug skip; screenshots/animations from natural AI selection; hardware review pending')
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
