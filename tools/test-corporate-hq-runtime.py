#!/usr/bin/env python3
"""Actual controller-driven enemy sequence, baseline simulation and native pixel checks."""
from pathlib import Path
import argparse,subprocess,re,json,os
import numpy as np
from PIL import Image
from playable_runtime_validation import trace,hardware
from corporate_hq_previews import render,pose,M
from runtime_texture_profile import texture_profile
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();
for n in ['core','include','build','control','out']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--reuse',action='store_true');p.add_argument('--reuse-control',action='store_true');p.add_argument('--mirror',action='store_true');p.add_argument('--no-gifs',action='store_true');p.add_argument('--player2',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
f=a.out/'frontend';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-DMF_JAB_COHESION=1','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime/corporate-hq-frontend.c'),'-ldl','-o',str(f)],check=True)
def run(build,label):
 out=a.out/label;out.mkdir(exist_ok=True);txt=subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(build/'game.elf')],text=True);s={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',txt,re.M)}
 if not a.reuse and not(label=='control' and a.reuse_control):
  env=dict(os.environ)
  if a.mirror:env['MF_CPHQ_MIRROR']='1'
  if a.player2:env['MF_CPHQ_P2']='1'
  with (out/'run.log').open('w') as log:subprocess.run([str(f.resolve()),str(a.core.resolve()),str((build/'mullet-force.cue').resolve()),str(out.resolve()),'2400','run',hex(s['_game']),hex(s['_idle_ticks']),'1','1'],stdout=log,stderr=subprocess.STDOUT,check=True,env=env)
 return trace(out),s
r,s=run(a.build,'new');budget=texture_profile(R,a.build);c,_=run(a.control,'control');assert all(bytes(v.game)==bytes(c[k].game) and bytes(v.idle)==bytes(c[k].idle) for k,v in r.items() if k>=695)
for n in ['pad.bin','jab.bin','dash.bin','run.bin']:
 def active_records(folder):
  data=(a.out/folder/n).read_bytes();count=2400 if n=='pad.bin' else 2105;size=len(data)//count;assert size*count==len(data)
  return b''.join(data[i:i+size] for i in range(0,len(data),size) if int.from_bytes(data[i:i+4],'little')>=695)
 assert active_records('new')==active_records('control'),n
b=(a.out/'new/frame-0750.wram').read_bytes()
def read(at):
 v=int.from_bytes(b[at&0xfffff:(at&0xfffff)+4],'little');return ((v>>16)|(v<<16))&0xffffffff
assert read(s['___jo_sprite_id'])+1==budget['slots'];assert budget['boot_bytes'] in [read(v) for k,v in s.items() if k.startswith('_texture_bytes')]
assert (a.out/'new/cram.bin').read_bytes()==(a.out/'control/cram.bin').read_bytes(),'Palette changed'
ids=[read(s['_cp_ids']+4*i) for i in range(10)]+[read(s['_cphq_ids']+4*i) for i in range(4)]
assert len(set(ids))==14,'Duplicate enemy textures'
assert len({v.texture_hash for k,v in r.items() if k>=750})==1
# Idle presentation clocks follow simulation ticks, not renderer calls.
clocks={};idle=[0,0];last=[0,0];tick=None
for k,v in r.items():
 if v.game.ticks!=tick:
  for j,e in enumerate(v.game.enemies):idle[j]=(idle[j]+1)%54 if e.state==1 and last[j]==1 else 0;last[j]=e.state
 tick=v.game.ticks;clocks[k]=idle.copy()
coverage={};bad=[];pixels=0;captures={}
for path in sorted((a.out/'new').glob('frame-*.ppm')):
 k=int(path.stem.split('-')[1]);v=r.get(k-3)
 if v is None or k<750:continue
 screen=np.asarray(Image.open(path).convert('RGB'))
 for j,e in enumerate(v.game.enemies):
  key=pose(e,clocks[k-3][j],j);
  if key<0 or e.fire_flash:continue
  ref=hardware(render(key,e.facing<0));rgba=np.asarray(ref);mask=rgba[:,:,3]>0
  yy,xx=np.where(mask);sx=xx+e.x//256-v.game.camera-64+1;sy=yy+e.y//256-108+1
  keep=(sx>=0)&(sx<320)&(sy>=59)&(sy<240)
  # Mask actors closer to camera, including other enemies and players.
  for pp in list(v.game.players):
   if pp.active and pp.health and pp.y>=e.y-4*256:keep &= ~((sx>=pp.x//256-v.game.camera-(85 if pp.attack else 64))&(sx<=pp.x//256-v.game.camera+(85 if pp.attack else 64))&(sy>=pp.y//256-(110 if pp.bat else 90)-pp.height//256)&(sy<=pp.y//256+4))
  for ii,other in enumerate(v.game.enemies):
   if ii!=j and other.state and other.y>=e.y:keep &= ~((sx>=other.x//256-v.game.camera-80)&(sx<=other.x//256-v.game.camera+80)&(sy>=other.y//256-95)&(sy<=other.y//256+3))
  for drum in v.game.drums:
   if drum.hp and drum.y>=e.y:keep &= ~((sx>=drum.x//256-v.game.camera-20)&(sx<=drum.x//256-v.game.camera+20)&(sy>=drum.y//256-55)&(sy<=drum.y//256+3))
  if v.game.spark:keep &= ~((sx>=v.game.spark_x-v.game.camera-17)&(sx<=v.game.spark_x-v.game.camera+18)&(sy>=v.game.spark_y-v.game.spark_z-17)&(sy<=v.game.spark_y-v.game.spark_z+18))
  if not keep.any():continue
  expected=rgba[yy[keep],xx[keep],:3];actual=screen[sy[keep],sx[keep]];diff=np.any(actual!=expected,axis=1)
  if diff.any():bad.append((k,j,key,int(diff.sum())))
  n=int(keep.sum());pixels+=n;name=f'{j}:pose{key}:face{e.facing}';coverage[name]=coverage.get(name,0)+n;captures.setdefault(str(key),path.name)
assert not bad,bad[:15]
states=sorted({e.state for v in r.values() for e in v.game.enemies});assert set(range(8))<=set(states),states
seen={pose(e,clocks[k][j],j) for k,v in r.items() for j,e in enumerate(v.game.enemies)};assert {6,7,8,9,10}<=seen,seen
# Confirm exact defeat -> absent duration and normal 480-tick respawn.
transitions=[];laststate=[None,None]
for k,v in r.items():
 for j,e in enumerate(v.game.enemies):
  if e.state!=laststate[j]:transitions.append(dict(frame=k,tick=v.game.ticks,enemy=j,state=e.state,timer=e.timer,hp=e.hp));laststate[j]=e.state
for j in [0,1]:
 seq=[x for x in transitions if x['enemy']==j]
 for i,x in enumerate(seq):
  if x['state']==7:
   assert seq[i+1]['state']==0 and seq[i+1]['tick']-x['tick']==x['timer']
   if i+2<len(seq):assert seq[i+2]['tick']-seq[i+1]['tick']==480
# Real presentation sequences retain screen/UI, no manually assembled body animation.
hitframe=next(k for k,v in r.items() if k>=750 and v.game.enemies[0].state==6)
for name,start,end in ([] if a.no_gifs else [('combat-demo',1000,1550),('full-story',750,2050),('hurt-knockback',hitframe-6,hitframe+40)]):
 paths=[a.out/'new'/f'frame-{k:04}.ppm' for k in range(start,end+1,2) if (a.out/'new'/f'frame-{k:04}.ppm').exists()];frames=[Image.open(p).convert('RGB') for p in paths]
 for z in [1,4]:
  ims=[q.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).resize((320*z,240*z),Image.Resampling.NEAREST) for q in frames];ims[0].save(a.out/f'{name}-actual-{z}x.gif',save_all=True,append_images=ims[1:],duration=[30 if i%3 else 40 for i in range(len(ims))],loop=0)
for key,file in captures.items():Image.open(a.out/'new'/file).save(a.out/f'actual-pose-{key}.png')
result=dict(gameplay_states_identical=sum(k>=695 for k in r),input_dash_jab_bat_traces_identical=True,matched_native_pixels=pixels,coverage=coverage,states_seen=states,poses_seen=sorted(seen),transitions=transitions,texture_bytes=budget['boot_bytes'],free_bytes=budget['free_bytes'],texture_definitions=budget['slots'],stable_texture_vram=True,physical_saturn_tested=False,webretro_tested=False,no_emulated_ram_writes=True,limitations=['Pixel coverage excludes HUD and nearer actor occlusion','Native libretro Yabause HLE/software core only; no hardware performance claim'])
(a.out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
