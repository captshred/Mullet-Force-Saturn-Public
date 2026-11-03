#!/usr/bin/env python3
from pathlib import Path
import argparse,subprocess,re,json,ctypes as C,os
from PIL import Image
import numpy as np
from playable_runtime_validation import trace,hardware
from corporate_hq_previews import render as enemy_render,pose as enemy_pose
from player_hurt_previews import hurt
from player_death_previews import run,transition,render as death,M
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
for n in ['core','include','build','control','out']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--side-by-side',action='store_true');p.add_argument('--mirror',action='store_true');p.add_argument('--frames',type=int,default=3000);p.add_argument('--mode',choices=['hurt','run','death'],default='hurt');p.add_argument('--player2',action='store_true');p.add_argument('--reuse',action='store_true');p.add_argument('--reuse-control',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
denim='Chuck denim cleanup: 1' in (a.build/'BUILD-INFO.txt').read_text()
if denim:
 from chuck_denim_previews import run,transition
waist='Player running waist seam: 1' in (a.build/'BUILD-INFO.txt').read_text()
if waist:
 from run_waist_previews import run,transition
front=a.out/'frontend';source='player-death-frontend.c' if a.mode=='death' else 'corporate-hq-frontend.c' if a.mode=='hurt' else 'custom-sfx-frontend.c';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-DMF_JAB_COHESION=1','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime'/source),'-ldl','-o',str(front)],check=True)
def capture(build,label):
 folder=a.out/label;folder.mkdir(exist_ok=True);text=subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(build/'game.elf')],text=True);s={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',text,re.M)}
 if not a.reuse and not(label=='control' and a.reuse_control):
  env=dict(os.environ)
  if a.player2:env['MF_CPHQ_P2']='1';env['MF_CPHQ_P2_FRONT']='1'
  if a.mode=='run':env['MF_CUSTOM_COMBAT_SCENARIO']='1'
  if a.side_by_side:env['MF_RUN_WAIST_SIDE_BY_SIDE']='1'
  if a.mode=='death':env['MF_PLAYER_DEATH_SCENARIO']='1'
  if a.mirror:env['MF_CPHQ_MIRROR']='1'
  with (folder/'run.log').open('w') as log:subprocess.run([str(front.resolve()),str(a.core.resolve()),str((build/'mullet-force.cue').resolve()),str(folder.resolve()),str(a.frames if a.mode=='death' else 1400),'run',hex(s['_game']),hex(s['_idle_ticks']),'1','1'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 return trace(folder),s
r,s=capture(a.build,'new');control,_=capture(a.control,'control');assert all(bytes(v.game)==bytes(control[k].game) and bytes(v.idle)==bytes(control[k].idle) for k,v in r.items() if k>=695)
class Dash(C.Structure):_fields_=[(n,C.c_int32) for n in ['dir','tap_dir','window','released','ready','anim','previous']]
class DR(C.Structure):_fields_=[('frame',C.c_uint32),('p',Dash*2)]
class RB(C.Structure):_fields_=[(n,C.c_int32) for n in ['active','carry','dir','pending']]
class BR(C.Structure):_fields_=[('frame',C.c_uint32),('p',RB*2),('enemy_class',C.c_int32*2)]
def records(name,cls):
 b=(a.out/'new'/name).read_bytes();assert len(b)%C.sizeof(cls)==0;rows=[cls.from_buffer_copy(b[i:i+C.sizeof(cls)]) for i in range(0,len(b),C.sizeof(cls))];return {v.frame:v for v in rows}
d=records('dash.bin',DR);b=records('run.bin',BR)
for name in ['dash.bin','jab.bin','run.bin']:assert (a.out/'new'/name).read_bytes()==(a.out/'control'/name).read_bytes(),name
mem=(a.out/'new/frame-0750.wram').read_bytes()
def read(at):
 v=int.from_bytes(mem[at&0xfffff:(at&0xfffff)+4],'little');return ((v>>16)|(v<<16))&0xffffffff
assert read(s['___jo_sprite_id'])+1==M['slots'];assert read(s['_ph_loaded'])==1 and read(s['_pd_loaded'])==1;assert M['boot_bytes'] in [read(v) for k,v in s.items() if k.startswith('_texture_bytes')]
assert (a.out/'new/cram.bin').read_bytes()==(a.out/'control/cram.bin').read_bytes();assert len({v.texture_hash for k,v in r.items() if k>=750})==1
last=[0,0];poses={};coverage={};bad=[];pixels=0;outside=0;examples={};runframes=set();hframes={0:[],1:[]};transitions=[]
for k,v in r.items():
 for j in [0,1]:
  if d[k].p[j].dir and not(v.game.players[j].invulnerable and v.game.players[j].invulnerable<112 and not v.game.ticks&4):last[j]=d[k].p[j].anim//42
  pp=v.game.players[j];key=None
  if pp.active and pp.health==0 and pp.defeated>0:key=('death',0 if pp.defeated>112 else 1 if pp.defeated>96 else 2)
  elif pp.active and pp.health>0 and pp.hurt:key=('hurt',0 if pp.hurt>8 else 1 if pp.hurt>4 else 2)
  elif not(pp.invulnerable and pp.invulnerable<112 and not v.game.ticks&4) and pp.active and pp.health>0 and not(pp.hurt or pp.height or pp.vz or pp.torch or pp.landing):
   if d[k].p[j].dir and not pp.attack:key=('run',d[k].p[j].anim//42)
   elif b[k].p[j].active and 0<pp.attack<7:key=('transition',last[j]);transitions.append((k,j,last[j]))
  poses[k,j]=key
for path in sorted((a.out/'new').glob('frame-*.ppm')):
 k=int(path.stem.split('-')[1]);v=r.get(k-3)
 if v is None or k<750:continue
 screen=np.asarray(Image.open(path).convert('RGB'));old=np.asarray(Image.open(a.out/'control'/path.name).convert('RGB'));allowed=np.zeros((240,320),bool)
 for j,pp in enumerate(v.game.players):
  key=poses[k-3,j]
  if key is None:continue
  typ,f=key;ref=hardware(death(j,f,pp.facing<0) if typ=='death' else hurt(j,f,pp.facing<0) if typ=='hurt' else transition(j,f,pp.attack,pp.facing<0) if typ=='transition' else run(j,f,pp.facing<0));arr=np.asarray(ref);yy,xx=np.where(arr[:,:,3]>0);sx=xx+pp.x//256-v.game.camera-(96 if typ=='transition' and pp.facing<0 else 64)+1;sy=yy+pp.y//256-pp.height//256-(108 if typ=='transition' else 92)+1
  if typ in ['hurt','death'] or (waist and f in [1,3]) or (j==1 and (f==2 or (denim and f==3))):
   x=pp.x//256-v.game.camera;y=pp.y//256-pp.height//256;allowed[max(0,y-96):min(240,y+5),max(0,x-80):min(320,x+80)]=True
  if typ=='death':sy+=pp.height//256-((pp.height//256)*(24-(120-pp.defeated))//24 if pp.defeated>96 else 0)
  keep=(sx>=0)&(sx<320)&(sy>=59)&(sy<221)
  for jj,other in enumerate(v.game.players):
   if jj!=j and other.active and other.y>=pp.y-4*256:keep &= ~((sx>=other.x//256-v.game.camera-(125 if other.bat else 85 if other.attack else 64))&(sx<=other.x//256-v.game.camera+(125 if other.bat else 85 if other.attack else 64))&(sy>=other.y//256-other.height//256-(110 if other.bat else 90))&(sy<=other.y//256+4))
  for ei,e in enumerate(v.game.enemies):
   if e.state and e.y>=pp.y:
    # Exact opaque enemy coverage avoids discarding the entire low kneeling pose.
    keys=range(3) if e.state==1 else [enemy_pose(e,actor=ei)]
    for ek in keys:
     mask=np.asarray(enemy_render(ek,e.facing<0))[:,:,3]>0
     ex=sx-(e.x//256-v.game.camera-64+1);ey=sy-(e.y//256-108+1);inside=(ex>=0)&(ex<144)&(ey>=0)&(ey<112);occ=np.zeros(len(sx),bool);occ[inside]=mask[ey[inside],ex[inside]];keep &= ~occ
  for drum in v.game.drums:
   if drum.hp and drum.y>=pp.y:keep &= ~((sx>=drum.x//256-v.game.camera-20)&(sx<=drum.x//256-v.game.camera+20)&(sy>=drum.y//256-52)&(sy<=drum.y//256+5))
  if v.game.spark:keep &= ~((sx>=v.game.spark_x-v.game.camera-18)&(sx<=v.game.spark_x-v.game.camera+18)&(sy>=v.game.spark_y-v.game.spark_z-18)&(sy<=v.game.spark_y-v.game.spark_z+18))
  if keep.sum()<20:continue
  diff=np.any(screen[sy[keep],sx[keep]]!=arr[yy[keep],xx[keep],:3],axis=1)
  if diff.any():bad.append((k,j,typ,f,int(diff.sum())))
  n=int(keep.sum());pixels+=n;tag=f'{j}:{typ}{f}:face{pp.facing}';coverage[tag]=coverage.get(tag,0)+n;examples.setdefault(tag,path.name)
  if typ=='run':runframes.add((j,f,pp.facing))
  elif typ in ['hurt','death']:hframes[j].append(k)
 delta=np.any(screen!=old,axis=2);assert not (delta&~allowed).any(),('Unrelated screen pixels changed',k,int((delta&~allowed).sum()));outside+=int((~allowed).sum())
assert not bad,bad[:20]
if a.mode=='run':assert len(runframes)==16,(len(runframes),sorted(runframes));assert transitions
elif a.mode=='hurt':
 actor=1 if a.player2 else 0
 assert all(any(t.startswith(f'{actor}:hurt{f}:') for t in coverage) for f in range(3)),coverage
if a.mode=='death':
 actor=1 if a.player2 else 0
 assert all(any(t.startswith(f'{actor}:death{f}:') for t in coverage) for f in range(3)),coverage
 events=[(k,v.game.players[actor]) for k,v in r.items() if k>=750]
 assert any(p.health==0 and p.defeated>0 for k,p in events),'No natural zero-HP defeat'
 assert any(events[i-1][1].health==0 and p.health==100 for i,(k,p) in enumerate(events) if i),'No automatic recovery observed'
for tag,file in examples.items():Image.open(a.out/'new'/file).save(a.out/('actual-'+tag.replace(':','-')+'.png'))
# Actual screenshots only; no manually assembled animation or injected damage.
if a.mode in ['hurt','death']:
 actor=1 if a.player2 else 0;start=min(hframes[actor])-6;end=start+(145 if a.mode=='death' else 64);name=['buck','chuck'][actor]+'-'+a.mode+'-actual'
else:start=750;end=860;name='both-running-side-by-side-actual' if a.side_by_side else 'run-to-bat-actual'
frames=[Image.open(a.out/'new'/f'frame-{f:04}.ppm').convert('RGB') for f in range(start,end+1,2) if (a.out/'new'/f'frame-{f:04}.ppm').exists()]
for z in [1,4]:
 ims=[im.quantize(colors=256,dither=Image.Dither.NONE).resize((320*z,240*z),Image.Resampling.NEAREST) for im in frames];ims[0].save(a.out/f'{name}-{z}x.gif',save_all=True,append_images=ims[1:],duration=[40 if i%3==0 else 30 for i in range(len(ims))],loop=0)
result=dict(side_by_side=a.side_by_side,mode=a.mode,mirrored=a.mirror,automatic_recovery_verified=a.mode=='death',gameplay_states_identical=sum(k>=695 for k in r),matched_native_pixels=pixels,unchanged_outside_pixels=outside,coverage=coverage,run_poses_seen=sorted(runframes),carry_to_swing_samples=len(transitions),texture_bytes=M['boot_bytes'],free_bytes=M['free_bytes'],definitions=M['slots'],unchanged_cram=True,stable_texture_vram=True,physical_saturn_tested=False,webretro_tested=False,no_ram_writes=True)
(a.out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
