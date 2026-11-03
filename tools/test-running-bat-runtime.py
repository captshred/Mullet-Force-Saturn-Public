#!/usr/bin/env python3
"""Real controller input, read-only emulator state and native pixel checks."""
from pathlib import Path
import argparse,subprocess,os,re,ctypes as C,json,hashlib
from PIL import Image
import numpy as np
from playable_runtime_validation import trace,pose,hardware
R=Path(__file__).resolve().parents[1]
class Dash(C.Structure):_fields_=[(n,C.c_int32) for n in ['dir','tap_dir','window','released','ready','anim','previous']]
class DRec(C.Structure):_fields_=[('frame',C.c_uint32),('p',Dash*2)]
class Run(C.Structure):_fields_=[(n,C.c_int32) for n in ['active','carry','dir','pending']]
class RRec(C.Structure):_fields_=[('frame',C.c_uint32),('p',Run*2),('enemy_class',C.c_int32*2)]
def records(path,kind):
 data=path.read_bytes();assert len(data)%C.sizeof(kind)==0;v=[kind.from_buffer_copy(data[i:i+C.sizeof(kind)]) for i in range(0,len(data),C.sizeof(kind))];return {x.frame:x for x in v}
p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--include',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--control-trace',type=Path);p.add_argument('--bat-visuals',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
text=subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(a.build/'game.elf')],text=True);symbols={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',text,re.M)}
if not os.environ.get('MF_REUSE_CAPTURE'):
 frontend=a.out/'frontend';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime/running-bat-frontend.c'),'-ldl','-o',str(frontend)],check=True)
 with (a.out/'run.log').open('w') as log:subprocess.run([str(frontend.resolve()),str(a.core.resolve()),str((a.build/'mullet-force.cue').resolve()),str(a.out.resolve()),'900','run',hex(symbols['_game']),hex(symbols['_idle_ticks']),'1','1'],stdout=log,stderr=subprocess.STDOUT,check=True)
r=trace(a.out);d=records(a.out/'dash.bin',DRec);b=records(a.out/'run.bin',RRec);manifest=json.loads((R/'assets/running/manifest.json').read_text())
compared=0
if a.control_trace:
 control=trace(a.control_trace);assert set(r)==set(control)
 for f in r:
  assert bytes(r[f].game)==bytes(control[f].game) and bytes(r[f].idle)==bytes(control[f].idle),('Gameplay changed',f)
  compared+=1
 for name in ['dash.bin','run.bin']:assert (a.out/name).read_bytes()==(a.control_trace/name).read_bytes(),name
if a.bat_visuals:
 visual=json.loads((R/'assets/running-bat-visual/manifest.json').read_text());manifest.update(boot_vdp1_bytes=visual['boot_bytes'],free_vdp1_bytes=visual['free_bytes'],slots=manifest['slots']+visual['slots'])
assert any(d[f].p[0].dir==1 and d[f].p[1].dir==-1 for f in r)
for j in range(2):assert {x.p[j].dir for x in b.values() if x.p[j].active}=={-1,1}
assert any(b[f].p[0].active for f in range(411,440))
assert any(r[f].game.players[0].bat and not b[f].p[0].active for f in range(605,630)),'Activation-tick A lost planted priority'
assert any(r[f].game.players[0].height for f in range(711,730)),'Dash jump failed'
assert all(not d[f].p[0].dir for f in range(445,470)),'Running bat auto-resumed dash'
kos=[];velocity=0;carry=0
for f,rec in r.items():
 if f-1 not in r:continue
 g=rec.game;old=r[f-1].game
 if g.ticks==old.ticks:continue
 for j,p in enumerate(g.players):
  if d[f].p[j].dir and not p.attack and 35*256<p.x<600*256 and abs(p.x-g.players[1-j].x)<245*256:
   assert p.x-old.players[j].x==d[f].p[j].dir*663;velocity+=1
  if b[f].p[j].active and b[f].p[j].carry:
   assert b[f].p[j].carry<=7
   if 35*256<p.x<600*256 and abs(p.x-g.players[1-j].x)<245*256:assert p.x-old.players[j].x==b[f].p[j].dir*663;carry+=1
 for j,e in enumerate(g.enemies):
  if old.enemies[j].hp==6 and e.hp==0:
   assert any(b[f].p[i].active and g.players[i].hit_mask&(1<<(3+j)) for i in range(2));assert g.score-old.score==250;kos.append(f)
assert kos and velocity>80 and carry>5
raw=(a.out/'frame-0350.wram').read_bytes()
def read32(at):
 v=int.from_bytes(raw[at&0xfffff:(at&0xfffff)+4],'little');return ((v>>16)|(v<<16))&0xffffffff
assert read32(symbols['___jo_sprite_id'])+1==manifest['slots']
assert manifest['boot_vdp1_bytes'] in [read32(v) for n,v in symbols.items() if n.startswith('_texture_bytes')]
assert len({x.texture_hash for f,x in r.items() if f>=330})==1,'Gameplay texture uploads detected'
refs={}
for j,name in enumerate(['buck','chuck']):
 for f in range(4):refs[j,18+f]=hardware(Image.open(R/(f'assets/running-bat-visual/{name}-run-{f}.png' if a.bat_visuals else f'assets/running/{name}-{f}.png')).convert('RGBA'))
checked=0;seen=[set(),set()];faces=[set(),set()]
for path in sorted(a.out.glob('frame-*.ppm')):
 f=int(path.stem.split('-')[1]);rec=r.get(f-3)
 if rec is None:continue
 screen=np.asarray(Image.open(path).convert('RGB'))
 for j,p in enumerate(rec.game.players):
  if not d[f-3].p[j].dir or p.attack or p.hurt or p.height or (p.invulnerable and p.invulnerable<112 and not rec.game.ticks&4):continue
  which=18+d[f-3].p[j].anim//42;ref=refs[j,which]
  if p.facing<0:ref=ref[:,::-1]
  yy,xx=np.where(ref[:,:,3]>0);sx=xx+p.x//256-rec.game.camera-64+1;sy=yy+p.y//256-92+1;keep=(sx>=0)&(sx<320)&(sy>=58)&(sy<221)
  boxes=[]
  for k,other in enumerate(rec.game.players):
   if k!=j and other.active:boxes.append((other.x//256-rec.game.camera-112,other.y//256-other.height//256-96,224,100))
  for e in rec.game.enemies:
   if e.state:boxes.append((e.x//256-rec.game.camera-80,e.y//256-96,160,100))
  for drum in rec.game.drums:
   if drum.hp:boxes.append((drum.x//256-rec.game.camera-17,drum.y//256-47,34,48))
  for bx,by,bw,bh in boxes:keep&=~((sx>=bx)&(sx<bx+bw)&(sy>=by)&(sy<by+bh))
  if keep.sum()<40:continue
  assert np.array_equal(screen[sy[keep],sx[keep]],ref[yy[keep],xx[keep],:3]),('Run pixels differ',f,j,which)
  checked+=int(keep.sum());seen[j].add(which);faces[j].add(p.facing)
carry_pixels=0;carry_cases=set();bridge_pixels=0;bridge_actors=set();metal_pixels=0;metal_cases=set()
if a.bat_visuals:
 last=[18,18];last_by_frame={}
 for f in sorted(r):
  for j in range(2):
   if d[f].p[j].dir:last[j]=18+d[f].p[j].anim//42
  last_by_frame[f]=last[:]
 for path in sorted(a.out.glob('frame-*.ppm')):
  f=int(path.stem.split('-')[1]);rec=r.get(f-3)
  if rec is None:continue
  screen=np.asarray(Image.open(path).convert('RGB'))
  for j,p in enumerate(rec.game.players):
   if not p.active or not p.health or p.hurt or p.height or (p.invulnerable and p.invulnerable<112 and not rec.game.ticks&4):continue
   active=d[f-3].p[j].dir!=0;bridge=b[f-3].p[j].active and 0<p.attack<6
   if not (active or bridge or (b[f-3].p[j].active and p.attack>=6)):continue
   name=['buck','chuck'][j]
   if active or bridge:
    which=18+d[f-3].p[j].anim//42 if active else last_by_frame[f-3][j]
    ref=refs[j,which].copy();body=hardware(Image.open(R/f'assets/running/{name}-{which-18}.png').convert('RGBA'))
    weapon=(ref[:,:,3]>0)&(body[:,:,3]==0)
    if p.facing<0:ref=ref[:,::-1];weapon=weapon[:,::-1]
    yy,xx=np.where(ref[:,:,3]>0);sx=xx+p.x//256-rec.game.camera-64+1;sy=yy+p.y//256-92+1
   else:
    if rec.game.spark:continue
    t=p.attack;bf=1 if t<12 else 2 if t<14 else 3 if t<17 else 4 if t<20 else 5 if t<28 else 6
    ov=hardware(Image.open(R/f'assets/running-bat-visual/{name}-swing-{bf}.png').convert('RGBA'));meta=json.loads((R/'assets/bat-frames.json').read_text())[name][bf];ox,oy=meta['crop_origin'];h,w=ov.shape[:2]
    yy,xx=np.where(ov[:,:,3]>0);ref=ov
    sx=p.x//256-rec.game.camera+(xx+ox-96 if p.facing>0 else -(xx+ox-96))+ (1 if p.facing>0 else 0)
    sy=yy+p.y//256+oy-92+(0 if h%2 else 1)
   keep=(sx>=0)&(sx<320)&(sy>=58)&(sy<221)
   boxes=[]
   for k,other in enumerate(rec.game.players):
    if k!=j and other.active and other.y>=p.y:boxes.append((other.x//256-rec.game.camera-112,other.y//256-other.height//256-96,224,100))
   for e in rec.game.enemies:
    if e.state and e.y>=p.y:boxes.append((e.x//256-rec.game.camera-80,e.y//256-96,160,100))
   for drum in rec.game.drums:
    if drum.hp and drum.y>=p.y:boxes.append((drum.x//256-rec.game.camera-17,drum.y//256-47,34,48))
   for bx,by,bw,bh in boxes:keep&=~((sx>=bx)&(sx<bx+bw)&(sy>=by)&(sy<by+bh))
   if keep.sum()<3:continue
   assert np.array_equal(screen[sy[keep],sx[keep]],ref[yy[keep],xx[keep],:3]),('Bat visual pixel mismatch',f,j,'carry' if active else 'bridge' if bridge else 'metal',int(keep.sum()))
   if active:
    n=int(weapon[yy[keep],xx[keep]].sum());carry_pixels+=n
    if n:carry_cases.add((j,which-18,p.facing))
   elif bridge:bridge_pixels+=int(keep.sum());bridge_actors.add(j)
   else:metal_pixels+=int(keep.sum());metal_cases.add((j,bf,p.facing))
 assert carry_pixels>1000 and len(carry_cases)==16,(carry_pixels,carry_cases)
 assert bridge_pixels>500 and bridge_actors=={0,1},(bridge_pixels,bridge_actors)
 assert metal_pixels>200 and {x[0] for x in metal_cases}=={0,1},(metal_pixels,metal_cases)
ghost_pixels=0;ghost_seen=set();ghost_samples={}
if a.control_trace and 'artifact_correction' in manifest and not a.bat_visuals:
 for path in sorted(a.out.glob('frame-*.ppm')):
  f=int(path.stem.split('-')[1]);rec=r.get(f-3);old_path=a.control_trace/path.name
  if rec is None or not old_path.exists():continue
  screen=np.asarray(Image.open(path).convert('RGB'));oldscreen=np.asarray(Image.open(old_path).convert('RGB'))
  for j,p in enumerate(rec.game.players):
   if not d[f-3].p[j].dir or p.attack or p.hurt or p.height or (p.invulnerable and p.invulnerable<112 and not rec.game.ticks&4):continue
   pose_id=d[f-3].p[j].anim//42
   if pose_id not in [1,3]:continue
   x,y=(81,47) if j==0 else ((79,47) if pose_id==1 else (83,47))
   name=['buck','chuck'][j];before=hardware(Image.open(R/f'assets/leg-artifact-fix/before/{name}-{pose_id}.png').convert('RGBA'))
   oldcolor=before[y,x,:3];x=x if p.facing>0 else 127-x
   sx=x+p.x//256-rec.game.camera-64+1;sy=y+p.y//256-92+1
   if not (0<=sx<320 and 58<=sy<221):continue
   if np.array_equal(oldscreen[sy,sx],oldcolor):
    assert not np.array_equal(screen[sy,sx],oldcolor),('Stale knee still rendered',f,j,pose_id)
    ghost_pixels+=1;ghost_seen.add((j,pose_id,p.facing));ghost_samples.setdefault(f"{j}:{pose_id}:{p.facing}",f)
 assert ghost_pixels>20 and {j for j,_,_ in ghost_seen}=={0,1},(ghost_pixels,ghost_seen)
assert checked>20000 and all(s=={18,19,20,21} for s in seen) and all(s=={-1,1} for s in faces),(checked,seen,faces)
# Real screenshots and capture GIFs, no synthesized gameplay.
for name,f in [('two-player-run',400),('running-bat',420),('running-bat-ko',430),('left-running-bat',530),('planted-bat',615)]:Image.open(a.out/f'frame-{f:04d}.ppm').save(a.out/f'{name}.png')
for name,start,stop in [('running-bat-ko',400,450),('left-running-bat',510,550),('planted-bat',600,645)]:
 frames=[Image.open(a.out/f'frame-{f:04d}.ppm').resize((640,480),Image.Resampling.NEAREST) for f in range(start,stop,5)];frames[0].save(a.out/f'{name}.gif',save_all=True,append_images=frames[1:],duration=[80,80,90]*(len(frames)//3)+[80]*(len(frames)%3),loop=0)
report=dict(frames=900,carry_weapon_pixels=carry_pixels,carry_cases=[list(x) for x in sorted(carry_cases)],windup_bridge_pixels=bridge_pixels,metal_swing_pixels=metal_pixels,metal_swing_cases=[list(x) for x in sorted(metal_cases)],ghost_kneecap_pixels_removed_in_game=ghost_pixels,ghost_sample_frames=ghost_samples,ghost_cases_seen=[list(x) for x in sorted(ghost_seen)],gameplay_states_identical_to_control=compared,velocity_samples=velocity,velocity_24_8=663,carry_velocity_samples=carry,full_health_KO_frames=kos,run_pixels_compared=checked,pixel_mismatches=0,run_poses_seen=[sorted(x) for x in seen],run_facings_seen=[sorted(x) for x in faces],actual_vdp1_bytes=manifest['boot_vdp1_bytes'],free_vdp1_bytes=manifest['free_vdp1_bytes'],texture_slots=manifest['slots'],stable_gameplay_textures=True,method='Controller-only local Yabause HLE/software/interpreter, read-only state tracing, no RAM writes. Physical Saturn/WebRetro not tested.',core_sha256=hashlib.sha256(a.core.read_bytes()).hexdigest())
(a.out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
