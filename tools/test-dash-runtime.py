#!/usr/bin/env python3
"""Controller-only Yabause dash validation, original-state ABI preserved."""
import argparse,subprocess,re,json,ctypes as C,hashlib,os
from pathlib import Path
from PIL import Image
import numpy as np
from playable_runtime_validation import trace,pose,hardware
R=Path(__file__).resolve().parents[1]
class Dash(C.Structure):_fields_=[(n,C.c_int32) for n in ['dir','tap_dir','window','released','ready','anim']]+[('previous',C.c_uint32)]
class DashRecord(C.Structure):_fields_=[('frame',C.c_uint32),('players',Dash*2)]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--core',type=Path,required=True);p.add_argument('--include',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--control',type=Path,required=True);p.add_argument('--preset',type=int,choices=[15,17],default=17);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
frontend=a.out/'frontend';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime/dash-frontend.c'),'-ldl','-o',str(frontend)],check=True)
sy={}
for name,build in [('dash',a.build),('control',a.control)]:
 text=subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(build/'game.elf')],text=True);sy[name]={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',text,re.M)};out=a.out/name;out.mkdir(exist_ok=True)
 if not os.environ.get('MF_REUSE_CAPTURE'):
  with (out/'run.log').open('w') as log:subprocess.run([str(frontend.resolve()),str(a.core.resolve()),str((build/'mullet-force.cue').resolve()),str(out.resolve()),'800','dash',hex(sy[name]['_game']),hex(sy[name]['_idle_ticks']),'1' if name=='dash' else '0'],stdout=log,stderr=subprocess.STDOUT,check=True)
r=trace(a.out/'dash');control=trace(a.out/'control');raw=(a.out/'dash/dash.bin').read_bytes();assert len(raw)%C.sizeof(DashRecord)==0;d={}
for i in range(0,len(raw),C.sizeof(DashRecord)):
 v=DashRecord.from_buffer_copy(raw[i:i+C.sizeof(DashRecord)]);d[v.frame]=v.players
for f in range(330,387):assert bytes(r[f].game)==bytes(control[f].game),('Normal movement changed',f)
assert all(not d[f][0].dir for f in range(351,384))
assert any(d[f][0].dir==1 and d[f][1].dir==-1 for f in range(406,429))
assert any(d[f][0].dir==-1 for f in range(446,480)) and any(d[f][1].dir==1 for f in range(456,500))
assert any(r[f].game.players[0].bat for f in range(507,525)) and all(not d[f][0].dir for f in range(507,525))
assert any(r[f].game.players[0].height>0 for f in range(568,580)) and all(not d[f][0].dir for f in range(568,580))
assert all(not d[f][0].dir for f in range(615,711)),'Landing/slow taps auto-dashed'
fast=390*a.preset//10;samples=0;normal=0
for f in range(352,380):
 if r[f].game.ticks!=r[f-1].game.ticks:assert r[f].game.players[0].x-r[f-1].game.players[0].x==390;normal+=1
for f,v in d.items():
 if f-1 not in r or r[f].game.ticks==r[f-1].game.ticks:continue
 for j in range(2):
  player=r[f].game.players[j];old=r[f-1].game.players[j]
  if v[j].dir and not player.height and not player.hurt and not player.attack and 35*256<player.x<600*256 and abs(player.x-r[f].game.players[1-j].x)<245*256:
   assert player.x-old.x==v[j].dir*fast,(f,j,player.x-old.x,fast);samples+=1
assert samples>80,(samples,fast)
assert len({x.texture_hash for f,x in r.items() if f>=330})==1
assert r[350].texture_hash==control[350].texture_hash,'Graphics texture bank changed'
raw=(a.out/'dash/frame-0350.wram').read_bytes()
def read32(at):
 v=int.from_bytes(raw[at&0xfffff:(at&0xfffff)+4],'little');return ((v>>16)|(v<<16))&0xffffffff
assert read32(sy['dash']['___jo_sprite_id'])+1==135
assert 362848 in [read32(v) for n,v in sy['dash'].items() if n.startswith('_texture_bytes')]
refs={}
for j,n in enumerate(['buck','chuck']):
 for f in range(4):refs[j,f]=hardware(Image.open(R/f'assets/animation-polish/{n}-{f:02d}.png').convert('RGBA'))
 for f in range(3):refs[j,15+f]=hardware(Image.open(R/f'assets/{"knee-lift" if f==0 else "original-three-walk"}/{n}-{f:02d}.png').convert('RGBA'))
checked=0;dash_seen=[set(),set()];facing_seen=[set(),set()]
for path in sorted((a.out/'dash').glob('frame-*.ppm')):
 f=int(path.stem.split('-')[1]);rec=r.get(f-3)
 if rec is None or f<345:continue
 screen=np.asarray(Image.open(path).convert('RGB'))
 for j in range(2):
  player=rec.game.players[j];which=pose(rec,j,original_hold=10)
  if which<0 or (player.invulnerable and player.invulnerable<112 and not rec.game.ticks&4):continue
  active=d[f-3][j].dir!=0
  if active:which=15+d[f-3][j].anim//50
  ref=refs[j,which]
  if player.facing<0:ref=ref[:,::-1]
  yy,xx=np.where(ref[:,:,3]>0);sx=xx+player.x//256-rec.game.camera-64+1;syy=yy+player.y//256-92+1;keep=(sx>=0)&(sx<320)&(syy>=58)&(syy<221)
  boxes=[]
  for k,other in enumerate(rec.game.players):
   if k!=j and other.active:
    wide=112 if other.attack or other.height or other.vz or other.torch else 64
    boxes.append((other.x//256-rec.game.camera-wide,other.y//256-other.height//256-96,wide*2,100))
  for e in rec.game.enemies:
   if e.state:boxes.append((e.x//256-rec.game.camera-80,e.y//256-96,160,100))
  for drum in rec.game.drums:
   if drum.hp:boxes.append((drum.x//256-rec.game.camera-17,drum.y//256-47,34,48))
  for bx,by,bw,bh in boxes:keep&=~((sx>=bx)&(sx<bx+bw)&(syy>=by)&(syy<by+bh))
  if keep.sum()<40:continue
  assert np.array_equal(screen[syy[keep],sx[keep]],ref[yy[keep],xx[keep],:3]),('Approved player pixels differ',f,j,which)
  checked+=int(keep.sum())
  if active:dash_seen[j].add(which);facing_seen[j].add(player.facing)
assert checked>100000 and all(s=={15,16,17} for s in dash_seen) and all(s=={-1,1} for s in facing_seen),(checked,dash_seen,facing_seen)
for f in [370,410,420,460,470,510,570,635,700]:Image.open(a.out/f'dash/frame-{f:04d}.ppm').save(a.out/f'dash/frame-{f:04d}.png')
report={'frames_per_build':800,'preset_numerator':a.preset,'speed_denominator':10,'actual_dash_velocity_24_8':fast,'exact_velocity_samples':samples,'unchanged_normal_velocity_samples':normal,'simulation_prefix_identical_before_dash':57,'approved_player_pixels_compared':checked,'pixel_mismatches':0,'dash_poses_seen':[sorted(s) for s in dash_seen],'dash_facings_seen':[sorted(s) for s in facing_seen],'actual_vdp1_bytes':362848,'free_vdp1_bytes':95640,'actual_texture_slots':135,'textures_identical_to_approved_lighting':True,'textures_stable_during_gameplay':True,'bat_jump_slowtap_landing_runtime_checks':True,'core_sha256':hashlib.sha256(a.core.read_bytes()).hexdigest(),'method':'Controller-only local Yabause software/interpreter/HLE BIOS, read-only serialized game-prefix and dash-suffix state. No RAM writes. Physical hardware/WebRetro not tested.'}
(a.out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
