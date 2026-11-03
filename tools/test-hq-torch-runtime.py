#!/usr/bin/env python3
"""Real two-pad torch playback compared to the published jab build. Read-only RAM."""
from pathlib import Path
import argparse,subprocess,os,re,json,ctypes as C
import numpy as np
from PIL import Image
from playable_runtime_validation import trace,hardware
from hq_torch_previews import render
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--include',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--control-build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--reuse',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
frontend=a.out/'frontend';subprocess.run(['cc','-std=c99','-O2','-DMF_JAB_COHESION=1','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime/hq-torch-frontend.c'),'-ldl','-o',str(frontend)],check=True)
def capture(build,out):
 out.mkdir(exist_ok=True);txt=subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(build/'game.elf')],text=True);s={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',txt,re.M)}
 if not a.reuse:
  with (out/'run.log').open('w') as log:subprocess.run([str(frontend.resolve()),str(a.core.resolve()),str((build/'mullet-force.cue').resolve()),str(out.resolve()),'1400','run',hex(s['_game']),hex(s['_idle_ticks']),'1','1'],stdout=log,stderr=subprocess.STDOUT,check=True)
 return trace(out),s
r,s=capture(a.build,a.out/'test');control,_=capture(a.control_build,a.out/'control');r={f:v for f,v in r.items() if f>=695}
assert all(bytes(x.game)==bytes(control[f].game) and bytes(x.idle)==bytes(control[f].idle) for f,x in r.items())
for file in ['dash.bin','run.bin','jab.bin','pad.bin']:
 stride={'dash.bin':60,'run.bin':44,'jab.bin':20,'pad.bin':12}[file]
 b=(a.out/'test'/file).read_bytes();c=(a.out/'control'/file).read_bytes()
 assert b==c,file
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
 for j,p in enumerate(g.players):
  if not p.active or not p.health or p.hurt or not p.torch or (p.invulnerable and p.invulnerable<112 and not g.ticks&4):continue
  pose=0 if p.torch==1 else 1 if p.torch==2 else 2;walk=p.walk//10%3 if p.moving else -1
  ref=hardware(render(j,pose,walk,(g.ticks//3+j)%4));root=64
  if p.facing<0:ref=ref[:,::-1];root=192-64
  yy,xx=np.where(ref[:,:,3]>0);sx=xx+p.x//256-g.camera-root+1;sy=yy+p.y//256-108+1;keep=(sx>=0)&(sx<320)&(sy>=58)&(sy<221)
  for k,q in enumerate(g.players):
   if k!=j and q.active and q.y>=p.y:
    bx=q.x//256-g.camera-80;by=q.y//256-q.height//256-105;keep&=~((sx>=bx)&(sx<bx+160)&(sy>=by)&(sy<by+110))
  for e in g.enemies:
   if e.state and e.y>=p.y:
    bx=e.x//256-g.camera-80;by=e.y//256-100;keep&=~((sx>=bx)&(sx<bx+160)&(sy>=by)&(sy<by+105))
  for d in g.drums:
   if d.hp and d.y>=p.y:keep&=~((sx>=d.x//256-g.camera-18)&(sx<d.x//256-g.camera+18)&(sy>=d.y//256-50)&(sy<d.y//256+3))
  if g.spark:keep&=~((sx>=g.spark_x-g.camera-18)&(sx<g.spark_x-g.camera+18)&(sy>=g.spark_y-g.spark_z-18)&(sy<g.spark_y-g.spark_z+18))
  if keep.sum()<30:continue
  diff=np.any(screen[sy[keep],sx[keep]]!=ref[yy[keep],xx[keep],:3],axis=1)
  if diff.any():bad.append([f,j,pose,walk,int(diff.sum()),int(keep.sum())]);continue
  pixels+=int(keep.sum());key=f'{j}:pose{pose}:walk{walk}:face{p.facing}';coverage[key]=coverage.get(key,0)+int(keep.sum())
assert not bad,bad[:20]
for j in [0,1]:
 assert any(k.startswith(f'{j}:pose1:walk-1:') for k in coverage)
 assert all(any(k.startswith(f'{j}:pose1:walk{w}:') for k in coverage) for w in range(3)),coverage
assert any(all(p.torch==2 for p in x.game.players) for x in r.values())
starts=[]
for j,begin in [(0,800),(1,780)]:
 samples=[f for f,x in r.items() if x.game.players[j].torch==2];starts.append(min(samples));assert min(samples)-begin in [60,61,62,63]
ims=[Image.open(a.out/'test'/f'frame-{f:04}.ppm').convert('RGB') for f in range(840,921) if (a.out/'test'/f'frame-{f:04}.ppm').exists()]
for z in [1,4]:
 frames=[im.resize((320*z,240*z),Image.Resampling.NEAREST) for im in ims];frames[0].save(a.out/f'actual-coop-torch-{z}x.gif',save_all=True,append_images=frames[1:],duration=[20 if i%3 else 10 for i in range(len(frames))],loop=0)
for f in [850,865,885,905,1065]:Image.open(a.out/'test'/f'frame-{f:04}.ppm').save(a.out/f'actual-gameplay-{f}.png')
result=dict(gameplay_states_identical=len(r),all_input_dash_bat_jab_state_identical=True,matched_native_pixels=pixels,coverage=coverage,torch_first_fire_frames=starts,texture_bytes=m['boot_bytes'],free_bytes=m['free_bytes'],texture_slots=m['slots'],stable_texture_vram=True,no_ram_writes=True,physical_saturn_tested=False,webretro_tested=False,limitations=['Equip is not a separate live dwell: original 60-tick transition goes straight to fire','Runtime covers Buck right/Chuck left; other mirrors are native/mocked tests','No hardware performance or audio audition claim'])
(a.out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
