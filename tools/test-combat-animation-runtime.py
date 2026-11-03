#!/usr/bin/env python3
"""Controller-only Yabause comparative test; never writes emulated game RAM."""
from pathlib import Path
import argparse,subprocess,os,re,json,ctypes as C
import numpy as np
from PIL import Image
from playable_runtime_validation import trace,hardware
R=Path(__file__).resolve().parents[1]
class Dash(C.Structure):_fields_=[(n,C.c_int32) for n in ['dir','tap_dir','window','released','ready','anim','previous']]
class DRec(C.Structure):_fields_=[('frame',C.c_uint32),('p',Dash*2)]
class Run(C.Structure):_fields_=[(n,C.c_int32) for n in ['active','carry','dir','pending']]
class RRec(C.Structure):_fields_=[('frame',C.c_uint32),('p',Run*2),('enemy_class',C.c_int32*2)]
def records(path,kind):
 data=path.read_bytes();assert len(data)%C.sizeof(kind)==0;v=[kind.from_buffer_copy(data[i:i+C.sizeof(kind)]) for i in range(0,len(data),C.sizeof(kind))];return {x.frame:x for x in v}
p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--include',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--control-build',type=Path,required=True);p.add_argument('--reuse-control',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
frontend=a.out/'frontend';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime/combat-animation-frontend.c'),'-ldl','-o',str(frontend)],check=True)
def capture(build,out):
 out.mkdir(parents=True,exist_ok=True);txt=subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(build/'game.elf')],text=True);syms={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',txt,re.M)}
 if not os.environ.get('MF_REUSE_CAPTURE') and not (a.reuse_control and out.name=='control' and (out/'trace.bin').exists()):
  with (out/'run.log').open('w') as log:subprocess.run([str(frontend.resolve()),str(a.core.resolve()),str((build/'mullet-force.cue').resolve()),str(out.resolve()),'1400','run',hex(syms['_game']),hex(syms['_idle_ticks']),'1','1'],stdout=log,stderr=subprocess.STDOUT,check=True)
 return trace(out),syms
r,symbols=capture(a.build,a.out/'test');control,_=capture(a.control_build,a.out/'control');r={f:v for f,v in r.items() if f>=695};control={f:v for f,v in control.items() if f>=695};assert set(r)==set(control)
for f in r:assert bytes(r[f].game)==bytes(control[f].game) and bytes(r[f].idle)==bytes(control[f].idle),('gameplay differs',f)
for name,kind in [('dash.bin',DRec),('run.bin',RRec)]:
 left=records(a.out/'test'/name,kind);right=records(a.out/'control'/name,kind)
 assert all(bytes(left[f])==bytes(right[f]) for f in r),name
d=records(a.out/'test/dash.bin',DRec);b=records(a.out/'test/run.bin',RRec);m=json.loads((R/'assets/combat-animation/manifest.json').read_text())
raw=(a.out/'test/frame-0750.wram').read_bytes()
def read32(at):
 v=int.from_bytes(raw[at&0xfffff:(at&0xfffff)+4],'little');return ((v>>16)|(v<<16))&0xffffffff
assert read32(symbols['___jo_sprite_id'])+1==m['slots'];assert m['boot_bytes'] in [read32(v) for n,v in symbols.items() if n.startswith('_texture_bytes')]
assert len({x.texture_hash for f,x in r.items() if f>=730})==1
# Compose exact source-key upper and untouched native lower at the simulation root.
last=[0,0];refs={};coverage={};pixels=0;failures=[];captures={}
for f,rec in r.items():
 g=rec.game
 for j,p in enumerate(g.players):
  visible=not p.health or not p.invulnerable or p.invulnerable>=112 or g.ticks&4
  if p.active and visible and d[f].p[j].dir:last[j]=(d[f].p[j].anim//42)%4
  if not p.active or not visible or not p.health or p.hurt or p.height or p.vz or p.torch or not p.attack:continue
  if p.bat and b[f].p[j].active and p.attack<6:continue
  name=['buck','chuck'][j];kind='running-bat' if b[f].p[j].active else 'bat' if p.bat else 'punch';lower=0
  if p.bat:
   key=2 if p.attack<12 or p.attack>=28 else 3
   if b[f].p[j].active:lower=1+(last[j]+(p.attack-6)//6)%4
  else:key=None if p.attack<3 or p.attack>=16 else 0 if p.attack<6 or p.attack>10 else 1
  im=Image.new('RGBA',(160,112))
  if key is None:im.alpha_composite(Image.open(R/f'assets/animation-polish/{name}-00.png'),(0,16))
  else:
   upper=Image.open(R/f'assets/combat-animation/{name}-key-{key}.png').convert('RGBA');im.alpha_composite(upper.crop((0,0,160,64)))
   low=Image.open(R/(f'assets/running/{name}-{lower-1}.png' if lower else f'assets/animation-polish/{name}-00.png'));im.alpha_composite(low.crop((0,48,128,96)),(0,64))
  path=a.out/'test'/f'frame-{f+3:04}.ppm'
  if not path.exists():continue
  ref=hardware(im)
  if p.facing<0:ref=ref[:,::-1];root=160-64
  else:root=64
  yy,xx=np.where(ref[:,:,3]>0);sx=xx+p.x//256-g.camera-root+1;sy=yy+p.y//256-108+1;keep=(sx>=0)&(sx<320)&(sy>=58)&(sy<221)
  boxes=[]
  for k,other in enumerate(g.players):
   if k!=j and other.active and other.y>=p.y:
    half=112 if other.attack else 64
    boxes.append((other.x//256-g.camera-half,other.y//256-other.height//256-105,half*2,110))
  for e in g.enemies:
   if e.state and e.y>=p.y:boxes.append((e.x//256-g.camera-80,e.y//256-100,160,105))
  for drum in g.drums:
   if drum.hp and drum.y>=p.y:boxes.append((drum.x//256-g.camera-17,drum.y//256-47,34,48))
  if g.spark:boxes.append((g.spark_x-g.camera-17,g.spark_y-g.spark_z-17,34,34))
  for bx,by,bw,bh in boxes:keep&=~((sx>=bx)&(sx<bx+bw)&(sy>=by)&(sy<by+bh))
  if keep.sum()<40:continue
  screen=np.asarray(Image.open(path).convert('RGB'));diff=np.any(screen[sy[keep],sx[keep]]!=ref[yy[keep],xx[keep],:3],axis=1)
  if diff.sum():failures.append([f,j,kind,key,int(keep.sum()),int(diff.sum())]);continue
  pixels+=int(keep.sum());tag=f'{name}:{kind}:{p.facing}:key{key}';coverage[tag]=coverage.get(tag,0)+int(keep.sum());captures.setdefault(tag,str(path))
assert not failures,failures[:12]
assert all(any(k.startswith(n+':punch:') for k in coverage) for n in ['buck','chuck']),coverage
assert all(any(k.startswith(n+':running-bat:') for k in coverage) for n in ['buck','chuck']),coverage
kos=[]
for f,x in r.items():
 if f-1 in r:
  for j,e in enumerate(x.game.enemies):
   if r[f-1].game.enemies[j].hp==6 and e.hp==0 and any(z.active for z in b[f].p):kos.append(f)
assert kos
result=dict(gameplay_states_compared=len(r),gameplay_byte_identical=True,dash_and_bat_state_byte_identical=True,texture_bytes=m['boot_bytes'],free_bytes=m['free_bytes'],texture_slots=m['slots'],stable_texture_hash=True,matched_pixels=pixels,coverage=coverage,ko_frames=kos,hardware_tested=False,webretro_tested=False,limitations=['Two-key prototype only; incomplete bat arc and player-specific styles','Runtime coverage is listed explicitly, not every phase/facing/occlusion combination'],captures=captures)
(a.out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
