#!/usr/bin/env python3
"""Controller-driven native Yabause combo trace and exact artwork validation."""
from pathlib import Path
import argparse,subprocess,os,re,json,ctypes as C
from PIL import Image
import numpy as np
from playable_runtime_validation import trace,hardware
from punch_combo_previews import cross
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
for n in ['core','include','build','out']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--reuse',action='store_true');p.add_argument('--export',type=Path,default=R/'docs/punch-combo-captures');a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True);a.export.mkdir(exist_ok=True,parents=True)
front=a.out/'frontend';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-DMF_FAST_RUNNING_BAT=1','-DMF_RUN_BAT=1','-DMF_DASH_ENABLED=1','-DMF_PUNCH_COMBO=1','-DMF_JAB_COHESION=1','-DMF_COMBO_RUNTIME=1','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime/custom-sfx-frontend.c'),'-ldl','-o',str(front)],check=True)
info=(a.build/'BUILD-INFO.txt').read_text();assert 'Jab jab cross combo: 1' in info
s={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(a.build/'game.elf')],text=True),re.M)}
class Combo(C.Structure):_fields_=[('next',C.c_int32),('phase',C.c_int32),('timeout',C.c_int32)]
class CR(C.Structure):_fields_=[('frame',C.c_uint32),('p',Combo*2)]
report={'commit':re.search(r'^Commit: (.+)$',info,re.M).group(1),'source_sha256':re.search(r'^Source SHA256: (.+)$',info,re.M).group(1),'method':'Real two-pad libretro input; read-only save-state traces; Yabause HLE/no cartridge','webretro_tested':False,'physical_saturn_tested':False,'no_ram_writes':True,'texture_bytes':453344,'free_bytes':5144,'definitions':255,'scenarios':[]}
for mirror in [0,1]:
 out=a.out/str(mirror);out.mkdir(exist_ok=True)
 if not a.reuse:
  with (out/'run.log').open('w') as log:subprocess.run([str(front.resolve()),str(a.core.resolve()),str((a.build/'mullet-force.cue').resolve()),str(out.resolve()),'1300','run',hex(s['_game']),hex(s['_idle_ticks']),'1','1'],env=dict(os.environ,MF_COMBO_SCENARIO=str(mirror)),stdout=log,stderr=subprocess.STDOUT,check=True)
 b=(out/'combo.bin').read_bytes();assert len(b)%C.sizeof(CR)==0;combos={q.frame:q for q in [CR.from_buffer_copy(b[i:i+C.sizeof(CR)]) for i in range(0,len(b),C.sizeof(CR))]};rows=trace(out)
 mem=(out/'frame-0750.wram').read_bytes()
 def read(addr):
  v=int.from_bytes(mem[addr&0xfffff:(addr&0xfffff)+4],'little');return ((v>>16)|(v<<16))&0xffffffff
 assert read(s['___jo_sprite_id'])+1==255
 assert 453344 in [read(v) for n,v in s.items() if n.startswith('_texture_bytes')]
 assert len({v.texture_hash for k,v in rows.items() if k>=750})==1
 starts=[[],[]];samples=[0,0];pixels=[0,0]
 for k,v in rows.items():
  prev=rows.get(k-1)
  if not prev:continue
  for actor,p in enumerate(v.game.players):
   if p.attack and (not prev.game.players[actor].attack or p.attack<prev.game.players[actor].attack):
    if 790<k<910:starts[actor].append([k,combos[k].p[actor].phase]);assert v.game.events&(1<<(5+actor*3))
 for actor in [0,1]:
  assert [q[1] for q in starts[actor]]==[0,1,2,0,1,2],starts[actor]
  assert [q[0]-p[0] for p,q in zip(starts[actor],starts[actor][1:])]==[12,12,16,12,12]
  assert combos[1002+4*actor].p[actor].phase==0
 for path in sorted(out.glob('frame-*.ppm')):
  k=int(path.stem.split('-')[1]);v=rows.get(k-3)
  if v is None:continue
  g=v.game;screen=np.asarray(Image.open(path).convert('RGB'))
  for actor,p in enumerate(g.players):
   if combos[k-3].p[actor].phase!=2 or not p.attack or p.attack>11 or p.hurt or p.bat:continue
   if p.invulnerable and p.invulnerable<112 and not g.ticks&4:continue
   ref=hardware(cross(actor,p.attack,p.facing<0));yy,xx=np.where(ref[:,:,3]>0);sx=xx+p.x//256-g.camera-(96 if p.facing<0 else 64)+1;sy=yy+p.y//256-108+1
   keep=(sx>=0)&(sx<320)&(sy>=58)&(sy<221);boxes=[]
   for j,q in enumerate(g.players):
    if j!=actor and q.active:boxes.append((q.x//256-g.camera-64,q.y//256-110,128,114))
   for e in g.enemies:
    if e.state:boxes.append((e.x//256-g.camera-70,e.y//256-96,140,100))
   for d in g.drums:
    if d.hp or d.flash:boxes.append((d.x//256-g.camera-18,d.y//256-48,36,50))
   if g.spark:boxes.append((g.spark_x-g.camera-18,g.spark_y-g.spark_z-18,36,36))
   for x,y,w,h in boxes:keep&=~((sx>=x)&(sx<x+w)&(sy>=y)&(sy<y+h))
   assert np.array_equal(screen[sy[keep],sx[keep]],ref[yy[keep],xx[keep],:3]),(mirror,actor,k,'native cross mismatch')
   samples[actor]+=1;pixels[actor]+=int(keep.sum())
 # Occlusion masks can hide the far actor; exact visible pixels are counted honestly.
 assert sum(pixels)>1000 and all(n>0 for n in pixels),(mirror,pixels,samples)
 frames=[Image.open(out/f'frame-{k:04}.ppm').convert('RGB') for k in range(795,905)]
 for z in [1,4]:
  ims=[im.resize((320*z,240*z),Image.Resampling.NEAREST) for im in frames];ims[0].save(a.export/f'two-player-combo-{("left" if mirror else "right")}-actual-{z}x.gif',save_all=True,append_images=ims[1:],duration=[20 if i%3 else 10 for i in range(len(ims))],loop=0)
 report['scenarios'].append({'mirror':bool(mirror),'starts':starts,'exact_cross_samples':samples,'matched_native_pixels':pixels,'timeout_restart_verified':True,'vram_stable':True})
(a.export/'runtime-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
