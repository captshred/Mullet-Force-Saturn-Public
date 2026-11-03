#!/usr/bin/env python3
"""Input-driven Yabause jump/kick/air-bat validation; no emulated RAM writes."""
from pathlib import Path
import argparse,subprocess,os,re,json
import numpy as np
from PIL import Image
from playable_runtime_validation import trace,hardware
from hq_jump_previews import render,phase
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--include',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--control-build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--reuse',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
frontend=a.out/'frontend';subprocess.run(['cc','-std=c99','-O2','-DMF_JAB_COHESION=1','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime/hq-jump-frontend.c'),'-ldl','-o',str(frontend)],check=True)
def capture(build,out):
 out.mkdir(exist_ok=True);txt=subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(build/'game.elf')],text=True);s={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',txt,re.M)}
 if not a.reuse:
  with (out/'run.log').open('w') as log:subprocess.run([str(frontend.resolve()),str(a.core.resolve()),str((build/'mullet-force.cue').resolve()),str(out.resolve()),'1400','run',hex(s['_game']),hex(s['_idle_ticks']),'1','1'],stdout=log,stderr=subprocess.STDOUT,check=True)
 return trace(out),s
r,s=capture(a.build,a.out/'test');control,_=capture(a.control_build,a.out/'control');r={f:v for f,v in r.items() if f>=695}
assert all(bytes(x.game)==bytes(control[f].game) and bytes(x.idle)==bytes(control[f].idle) for f,x in r.items())
for file in ['dash.bin','run.bin','jab.bin','pad.bin']:assert (a.out/'test'/file).read_bytes()==(a.out/'control'/file).read_bytes(),file
assert len({x.texture_hash for f,x in r.items()})==1
mem=(a.out/'test/frame-0750.wram').read_bytes()
def read32(at):
 v=int.from_bytes(mem[at&0xfffff:(at&0xfffff)+4],'little');return ((v>>16)|(v<<16))&0xffffffff
from runtime_texture_profile import texture_profile
m=texture_profile(R,a.build);assert read32(s['___jo_sprite_id'])+1==m['slots'];assert m['boot_bytes'] in [read32(v) for n,v in s.items() if n.startswith('_texture_bytes')]
coverage={};pixels=0;bad=[]
for f,rec in r.items():
 path=a.out/'test'/f'frame-{f+3:04}.ppm'
 if not path.exists():continue
 screen=np.asarray(Image.open(path).convert('RGB'));g=rec.game
 for j,q in enumerate(g.players):
  key=phase(q)
  if not key or (q.invulnerable and q.invulnerable<112 and not g.ticks&4):continue
  ref=hardware(render(j,key,q.landing));root=64
  if q.facing<0:ref=ref[:,::-1];root=160-64
  yy,xx=np.where(ref[:,:,3]>0);sx=xx+q.x//256-g.camera-root+1;sy=yy+q.y//256-q.height//256-108+1;keep=(sx>=0)&(sx<320)&(sy>=59)&(sy<221)
  for k,other in enumerate(g.players):
   if k!=j and other.active and other.y>=q.y:
    bx=other.x//256-g.camera-80;by=other.y//256-other.height//256-105;keep&=~((sx>=bx)&(sx<bx+160)&(sy>=by)&(sy<by+110))
  for e in g.enemies:
   if e.state and e.y>=q.y:
    bx=e.x//256-g.camera-80;by=e.y//256-100;keep&=~((sx>=bx)&(sx<bx+160)&(sy>=by)&(sy<by+105))
  for d in g.drums:
   if d.hp and d.y>=q.y:keep&=~((sx>=d.x//256-g.camera-18)&(sx<d.x//256-g.camera+18)&(sy>=d.y//256-50)&(sy<d.y//256+3))
  if g.spark:keep&=~((sx>=g.spark_x-g.camera-18)&(sx<g.spark_x-g.camera+18)&(sy>=g.spark_y-g.spark_z-18)&(sy<g.spark_y-g.spark_z+18))
  if keep.sum()<30:continue
  diff=np.any(screen[sy[keep],sx[keep]]!=ref[yy[keep],xx[keep],:3],axis=1)
  if diff.any():bad.append([f,j,key,q.facing,int(diff.sum()),int(keep.sum())]);continue
  pixels+=int(keep.sum());tag=f'{j}:phase{key}:face{q.facing}';coverage[tag]=coverage.get(tag,0)+int(keep.sum())
assert not bad,bad[:20]
for j in [0,1]:
 for k in [1,2,3,4,5,6]:assert any(t.startswith(f'{j}:phase{k}:') for t in coverage),(j,k,coverage)
 assert any(x.game.players[j].attack_air and x.game.players[j].bat and x.game.players[j].height for x in r.values()),('No actual air bat',j)
# Measure the untouched complete first flight and six-tick landing per player.
flights=[]
for j in [0,1]:
 start=min(f for f,x in r.items() if f>=780 and x.game.players[j].height>0)
 end=min(f for f,x in r.items() if f>start and not x.game.players[j].height)
 ticks=r[end].game.ticks-r[start-1].game.ticks
 assert ticks==42 and r[start].game.players[j].height==1510 and r[start].game.players[j].vz==1436
 landing=[r[end+k].game.players[j].landing for k in range(7)]
 assert landing==[6,5,4,3,2,1,0],landing
 flights.append(dict(player=j,start_frame=start,ground_frame=end,simulation_ticks=ticks,landing_counters=landing))
# Original unmodified aerial bat command path: compare complete screen regions
# with the control where no changed jumping fighter can cover the same pixels.
bat_pixels=0
for f,x in r.items():
 path=a.out/'test'/f'frame-{f+3:04}.ppm';cp=a.out/'control'/f'frame-{f+3:04}.ppm'
 if not path.exists() or not cp.exists():continue
 for j,q in enumerate(x.game.players):
  if not(q.bat and q.attack_air and q.height and not q.hurt):continue
  y=q.y//256-q.height//256;cx=q.x//256-x.game.camera;box=(max(0,cx-110),max(58,y-100),min(320,cx+110),min(221,y+2));test=np.asarray(Image.open(path).crop(box));old=np.asarray(Image.open(cp).crop(box));mask=np.ones(test.shape[:2],bool)
  for other in x.game.players:
   if other.active and phase(other):
    ox=other.x//256-x.game.camera-box[0];oy=other.y//256-other.height//256-box[1];yy,xx=np.indices(mask.shape);mask&=~((xx>=ox-80)&(xx<ox+80)&(yy>=oy-105)&(yy<oy+3))
  # This integration deliberately changes enemy combat pixels inside the broad
  # comparison rectangle; exclude those bounds, not any player-art differences.
  if 'Corporate Punk HQ combat: 1' in (a.build/'BUILD-INFO.txt').read_text():
   yy,xx=np.indices(mask.shape)
   for e in x.game.enemies:
    if not e.state:continue
    ox=e.x//256-x.game.camera-box[0];oy=e.y//256-box[1]
    mask&=~((xx>=ox-80)&(xx<ox+80)&(yy>=oy-100)&(yy<oy+5))
  assert np.array_equal(test[mask],old[mask]),('air bat regression',f,j);bat_pixels+=int(mask.sum())
assert bat_pixels>1000
for j in [0,1]:
 transition=[]
 for f in range(845,910):
  k=phase(r[f].game.players[j])
  if not transition or transition[-1]!=k:transition.append(k)
 assert transition[0]==transition[-1]==0 and transition.index(6)<transition.index(5)<len(transition)-1,transition
# Crops of actual frames: fixed ground-relative window shows rise, shadow, fall.
for j,n in enumerate(['buck','chuck']):
 for label,start,end in [('full-jump',786,850),('aerial-attack',860,888),('jump-attack-landing',846,916),('aerial-bat',926,987)]:
  frames=[]
  for f in range(start,end):
   path=a.out/'test'/f'frame-{f:04}.ppm'
   if not path.exists():continue
   g=r[f-3].game;q=g.players[j];cx=q.x//256-g.camera;frames.append(Image.open(path).convert('RGB').crop((cx-80,q.y//256-182,cx+80,q.y//256+10)))
  for z in [1,4]:
   ims=[im.resize((160*z,192*z),Image.Resampling.NEAREST) for im in frames];ims[0].save(a.out/f'{n}-actual-{label}-{z}x.gif',save_all=True,append_images=ims[1:],duration=[20 if i%3 else 10 for i in range(len(ims))],loop=0)
for f in [810,816,865,875,895,955]:Image.open(a.out/'test'/f'frame-{f:04}.ppm').save(a.out/f'actual-gameplay-{f}.png')
result=dict(gameplay_states_identical=len(r),all_physics_input_jab_dash_bat_states_identical=True,matched_native_pixels=pixels,coverage=coverage,aerial_bat_control_pixels=bat_pixels,flights=flights,peak_jump_height_fixed=max(x.game.players[0].height for f,x in r.items() if 790<=f<=840),texture_bytes=m['boot_bytes'],free_bytes=m['free_bytes'],texture_slots=m['slots'],stable_texture_vram=True,no_ram_writes=True,real_input_transition_gifs=True,physical_saturn_tested=False,webretro_tested=False,limitations=['Aerial bat retains exact legacy complete assembly; AL0..2 are used only by that path','Crowd occlusion is masked in pixel checks; coverage is listed explicitly','No physical Saturn performance or audio audition claim'])
(a.out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
