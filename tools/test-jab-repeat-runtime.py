#!/usr/bin/env python3
"""Real pad-driven three-jab captures. No save-state loads or emulated RAM writes."""
from pathlib import Path
import argparse,subprocess,os,re,json,struct
import numpy as np
from PIL import Image
from playable_runtime_validation import trace,hardware
from jab_cohesion_previews import render
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--include',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
txt=subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(a.build/'game.elf')],text=True);symbols={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',txt,re.M)}
frontend=a.out/'frontend';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-DMF_JAB_COHESION=1','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime/jab-repeat-frontend.c'),'-ldl','-o',str(frontend)],check=True)
if not os.environ.get('MF_REUSE_CAPTURE'):
 with (a.out/'run.log').open('w') as log:subprocess.run([str(frontend.resolve()),str(a.core.resolve()),str((a.build/'mullet-force.cue').resolve()),str(a.out.resolve()),'1400','run',hex(symbols['_game']),hex(symbols['_idle_ticks']),'1','1'],stdout=log,stderr=subprocess.STDOUT,check=True)
r=trace(a.out);pad={x[0]:x[1:] for x in struct.iter_unpack('<III',(a.out/'pad.bin').read_bytes())};queue={x[0]:x[1:] for x in struct.iter_unpack('<IIIII',(a.out/'jab.bin').read_bytes())};starts=[[],[]]
for f,rec in r.items():
 if f-1 not in r:continue
 for j,p in enumerate(rec.game.players):
  old=r[f-1].game.players[j]
  if not p.bat and p.attack and (not old.attack or p.attack<old.attack):starts[j].append(f)
rapid=[];edges=[];intervals=[]
for j,expected in enumerate([[800,809,821],[804,813,825]]):
 e=[f for f in pad if 795<=f<=850 and pad[f][j] and not pad[f-1][j]];assert e==expected,e;edges.append(e)
 s=[f for f in starts[j] if 795<=f<=850];assert len(s)==3,(j,starts[j]);rapid.append(s);dt=[r[s[k]].game.ticks-r[s[k-1]].game.ticks for k in [1,2]];assert dt==[12,12],dt;intervals.append(dt)
 assert any(queue[f][j*2]>0 for f in range(s[0]+1,s[2])),('No actual queued edge',j)
 assert all(not r[f].game.players[j].bat for f in range(s[0],s[2]+1))
 assert all(r[f].game.players[j].attack for f in range(s[0],s[2]+1)),('Idle gap',j)
assert rapid[0]!=rapid[1]
assert len([f for f in starts[0] if 870<=f<=935])==1,starts[0]
assert len([f for f in starts[0] if 950<=f<=1000])==1,starts[0]
assert all(queue[f][0]==0 for f in range(875,920)), 'Held A filled repeat buffer'
# Compare rendered native poses during all three actual jabs, excluding only
# foreground actor bounds and effects. No offline animation loop supplies evidence.
coverage={};pixels=0;failures=[]
for path in sorted(a.out.glob('frame-*.ppm')):
 f=int(path.stem.split('-')[1]);rec=r.get(f-3)
 if rec is None or not 795<=f-3<=868:continue
 screen=np.asarray(Image.open(path).convert('RGB'));g=rec.game
 for j,p in enumerate(g.players):
  if not p.attack or p.bat or p.hurt or not p.health or p.height or (p.invulnerable and p.invulnerable<112 and not g.ticks&4):continue
  im=render(j,p.attack);ref=hardware(im);root=64
  if p.facing<0:ref=ref[:,::-1];root=96
  yy,xx=np.where(ref[:,:,3]>0);sx=xx+p.x//256-g.camera-root+1;sy=yy+p.y//256-108+1;keep=(sx>=0)&(sx<320)&(sy>=58)&(sy<221)
  for k,q in enumerate(g.players):
   if k!=j and q.active and q.y>=p.y:
    half=112 if q.attack else 64;bx=q.x//256-g.camera-half;by=q.y//256-q.height//256-105;keep&=~((sx>=bx)&(sx<bx+half*2)&(sy>=by)&(sy<by+110))
  for e in g.enemies:
   if e.state and e.y>=p.y:
    bx=e.x//256-g.camera-80;by=e.y//256-100;keep&=~((sx>=bx)&(sx<bx+160)&(sy>=by)&(sy<by+105))
  if keep.sum()<30:continue
  diff=np.any(screen[sy[keep],sx[keep]]!=ref[yy[keep],xx[keep],:3],axis=1)
  if diff.any():failures.append([f,j,p.attack,int(diff.sum()),int(keep.sum())]);continue
  pixels+=int(keep.sum());key=f'{j}:{"extension" if p.attack<=5 else "impact" if p.attack<=10 else "recovery" if p.attack<=16 else "guard"}:{p.facing}';coverage[key]=coverage.get(key,0)+int(keep.sum())
assert not failures,failures[:10]
assert all(any(k.startswith(str(j)+':extension') for k in coverage) and any(k.startswith(str(j)+':impact') for k in coverage) for j in [0,1]),coverage
assert len({x.texture_hash for f,x in r.items() if f>=730})==1
# These GIFs are unmodified native emulator frames, with real controller edges
# and distinct attack restarts verified above. Enlargements use nearest sampling.
raw_frames=[(f,Image.open(a.out/f'frame-{f:04}.ppm').convert('RGB')) for f in range(797,869) if (a.out/f'frame-{f:04}.ppm').exists()]
full=[im for f,im in raw_frames];full[0].save(a.out/'actual-two-player-three-jabs-native.gif',save_all=True,append_images=full[1:],duration=[20 if k%3 else 10 for k in range(len(full))],loop=0)
for j,name in enumerate(['buck','chuck']):
 frames=[]
 for f,im in raw_frames:
  p=r[f-3].game.players[j];cx=p.x//256-r[f-3].game.camera;top=p.y//256-116
  frames.append(im.crop((cx-80,top,cx+80,top+128)))
 for z in [1,4]:
  ims=[im.resize((160*z,128*z),Image.Resampling.NEAREST) for im in frames];ims[0].save(a.out/f'{name}-real-input-three-jabs-{z}x.gif',save_all=True,append_images=ims[1:],duration=[20 if k%3 else 10 for k in range(len(ims))],loop=0)
result=dict(controller_edges=edges,actual_attack_start_frames=rapid,elapsed_simulation_intervals=intervals,hold_A_starts=[f for f in starts[0] if 870<=f<=935],too_early_second_press_starts=[f for f in starts[0] if 950<=f<=1000],matched_pixels=pixels,coverage=coverage,stable_texture_hash=True,ram_written=False,offline_repeat_loop=False,physical_saturn_tested=False,webretro_tested=False)
(a.out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
