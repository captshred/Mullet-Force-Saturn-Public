#!/usr/bin/env python3
"""Read-only local Yabause controller test and simulation/control comparison."""
import argparse,subprocess,os,re,json,hashlib
from pathlib import Path
from PIL import Image
from playable_runtime_validation import trace,hardware
import numpy as np
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lighting',action='store_true');p.add_argument('--refined',action='store_true');p.add_argument('--core',type=Path,required=True);p.add_argument('--include',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--control',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
bank=R/('assets/corporate-punk-lighting' if a.lighting else 'assets/corporate-punk-refined' if a.refined else 'assets/corporate-punk-animation');manifest=json.loads((bank/'manifest.json').read_text())
frontend=a.out/'frontend';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime/corporate-frontend.c'),'-ldl','-o',str(frontend)],check=True)
symbols={}
for name,build in [('new',a.build),('control',a.control)]:
 text=subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(build/'game.elf')],text=True)
 symbols[name]={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',text,re.M)}
 out=a.out/name;out.mkdir(exist_ok=True)
 if not os.environ.get('MF_REUSE_CAPTURE'):
  with (out/'run.log').open('w') as log:subprocess.run([str(frontend.resolve()),str(a.core.resolve()),str((build/'mullet-force.cue').resolve()),str(out.resolve()),'2800','controls',hex(symbols[name]['_game']),hex(symbols[name].get('_idle_ticks',0))],stdout=log,stderr=subprocess.STDOUT,check=True)
records=trace(a.out/'new');control=trace(a.out/'control')
for f,r in records.items():
 if f>=330:assert bytes(r.game)==bytes(control[f].game),('simulation changed',f)
assert len({r.texture_hash for f,r in records.items() if f>=330})==1,'Texture upload occurred during gameplay'
def read32(b,at):
 v=int.from_bytes(b[at&0xfffff:(at&0xfffff)+4],'little');return ((v>>16)|(v<<16))&0xffffffff
raw=(a.out/'new/frame-0350.wram').read_bytes();sy=symbols['new'];assert read32(raw,sy['___jo_sprite_id'])+1==manifest['boot_slots']
assert manifest['boot_bytes'] in [read32(raw,v) for n,v in sy.items() if n.startswith('_texture_bytes')]
cpids=[read32(raw,sy['_cp_ids']+4*i) for i in range(manifest['texture_slots'])];assert len(set(cpids))==manifest['texture_slots']
# Direct CRAM inspection proves both normal and warm palettes, independently
# of whether a flashing enemy is unoccluded in a screenshot.
import struct
cram=(a.out/'new/cram.bin').read_bytes();oldcram=(a.out/'control/cram.bin').read_bytes();pal=((bank if (a.refined or a.lighting) else R/'assets/corporate-punk')/'palette.bgr24').read_bytes()
for palette_bank in [4,5]:assert cram[palette_bank*512+2:palette_bank*512+32]==oldcram[palette_bank*512+2:palette_bank*512+32]
added=json.loads(((bank if (a.refined or a.lighting) else R/'assets/corporate-punk')/'palette-delta.json').read_text())
for i in ([v['raw_index'] for v in added['new_entries']]):
 b,g,red=[v>>3 for v in pal[i*3:i*3+3]]
 expected=0x8000|red|(g<<5)|(b<<10);warm=0x8000|min(red+10,31)|(min(g+3,31)<<5)|((b//2)<<10)
 assert struct.unpack_from('<H',cram,4*512+2*(i+1))[0]==expected
 assert struct.unpack_from('<H',cram,5*512+2*(i+1))[0]==warm
refs={n:hardware(Image.open(bank/f'{n}.png').convert('RGBA')) for n in ['idle-0','idle-1','idle-2','walk-0','walk-1','walk-2']}
# Reconstruct independent idle clocks from advanced simulation ticks.
clocks={};idle=[0,0];last=[0,0];tick=None
for f,r in records.items():
 if tick!=r.game.ticks:
  for j,e in enumerate(r.game.enemies):idle[j]=(idle[j]+1)%54 if e.state==1 and last[j]==1 else 0;last[j]=e.state
 tick=r.game.ticks;clocks[f]=idle.copy()
lighting_screen_pixels=0;lighting_changed_pixels=0
checked=0;seen=set();facings=set();burn_seen=0;states=set();captures=[]
for path in sorted((a.out/'new').glob('frame-*.ppm')):
 f=int(path.stem.split('-')[1]);r=records.get(f-3)
 if r is None or f<345:continue
 actual=np.asarray(Image.open(path).convert('RGB'))
 if a.lighting:
  oldscreen=np.asarray(Image.open(a.out/'control'/path.name).convert('RGB'));allowed=np.zeros((240,320),dtype=bool)
  for j,e in enumerate(r.game.enemies):
   if e.state not in [1,2]:continue
   name='walk-'+str(e.walk//7%3) if e.state==2 else 'idle-'+str(0 if clocks[f-3][j]<24 else 1 if clocks[f-3][j]<36 else 2)
   old=Image.open(R/f'assets/corporate-punk-refined/{name}.png').convert('RGBA');new=Image.open(bank/f'{name}.png').convert('RGBA')
   aa=np.asarray(old);bb=np.asarray(new);mask=np.any(aa[:,:,:3]!=bb[:,:,:3],axis=2)&(aa[:,:,3]>0)
   if e.facing<0:mask=mask[:,::-1]
   yy,xx=np.where(mask);sx=xx+e.x//256-r.game.camera-48+1;syy=yy+e.y//256-92+1;keep=(sx>=0)&(sx<320)&(syy>=0)&(syy<240);allowed[syy[keep],sx[keep]]=True
  differences=np.any(actual!=oldscreen,axis=2)
  assert not (differences&~allowed).any(),('Unrelated screen pixels changed',f,int((differences&~allowed).sum()))
  lighting_screen_pixels+=int((~allowed).sum());lighting_changed_pixels+=int(differences.sum())
 for j,e in enumerate(r.game.enemies):
  states.add(e.state)
  if e.state not in [1,2]:continue
  pose='walk-'+str(e.walk//7%3) if e.state==2 else 'idle-'+str(0 if clocks[f-3][j]<24 else 1 if clocks[f-3][j]<36 else 2)
  ref=refs[pose].copy()
  if e.fire_flash:
   # Warm palette is derived in 5-bit space before the software RGB565 output.
   src=np.asarray(Image.open(bank/f'{pose}.png').convert('RGBA')).copy();c=src[:,:,:3].astype(np.uint16)//8
   c[:,:,0]=np.minimum(c[:,:,0]+10,31);c[:,:,1]=np.minimum(c[:,:,1]+3,31);c[:,:,2]//=2
   ref[:,:,:3]=np.stack([c[:,:,0]*255//31,c[:,:,1]*2*255//63,c[:,:,2]*255//31],axis=2).astype(np.uint8);burn_seen+=1
  if e.facing<0:ref=ref[:,::-1]
  yy,xx=np.where(ref[:,:,3]>0);sx=xx+e.x//256-r.game.camera-48+1;syy=yy+e.y//256-92+1
  keep=(sx>=0)&(sx<320)&(syy>=58)&(syy<221)
  # Exclude foreground objects/actors and fire particle regions.
  blockers=[]
  for player in r.game.players:
   if player.active:
    wide=112 if (player.attack or player.height or player.vz or player.torch) else 64
    blockers.append((player.x//256-r.game.camera-wide,player.y//256-player.height//256-96,wide*2,100))
  for k,other in enumerate(r.game.enemies):
   if k!=j and other.state and other.y>=e.y:blockers.append((other.x//256-r.game.camera-80,other.y//256-96,160,100))
  for d in r.game.drums:
   if d.hp and d.y//256>=e.y//256:blockers.append((d.x//256-r.game.camera-17,d.y//256-47,34,48))
  if e.burn:blockers.append((e.x//256-r.game.camera-20,e.y//256-65,45,45))
  for bx,by,bw,bh in blockers:keep &= ~((sx>=bx)&(sx<bx+bw)&(syy>=by)&(syy<by+bh))
  if keep.sum()<25:continue
  expected=ref[yy[keep],xx[keep],:3];got=actual[syy[keep],sx[keep]]
  assert np.array_equal(expected,got),('Enemy native pixels differ',f,j,pose,e.facing,int(np.any(expected!=got,axis=1).sum()),len(got))
  checked+=int(keep.sum());seen.add(pose);facings.add(e.facing)
  if f in [350,400,500,700,900,1000,1200,1400,2000,2600]:captures.append(f)
assert checked>10000 and facings=={-1,1} and {'walk-0','walk-1','walk-2'}<=seen,(checked,seen,facings)
for f in sorted(set(captures)):Image.open(a.out/f'new/frame-{f:04d}.ppm').save(a.out/f'new/frame-{f:04d}.png')
report={'frames_run_per_build':2800,'simulation_frames_identical':sum(f>=330 for f in records),'compared_enemy_pixels':checked,'pixel_mismatches':0,'poses_seen':sorted(seen),'facings_seen':sorted(facings),'enemy_states_seen':sorted(states),'warm_frames_candidates':burn_seen,'actual_loaded_slots':manifest['boot_slots'],'actual_allocated_bytes':manifest['boot_bytes'],'free_bytes':manifest['boot_free'],'texture_memory_stable':True,'normal_and_warm_palette_entries_verified':len(added['new_entries']),'legacy_enemy_palette_entries_preserved':True,'lighting_unchanged_screen_pixels_checked':lighting_screen_pixels,'lighting_visible_rim_pixel_changes':lighting_changed_pixels,'core_sha256':hashlib.sha256(a.core.read_bytes()).hexdigest(),'method':'Controller-driven local Yabause libretro, software renderer, interpreter, HLE BIOS; read-only save states. No RAM writes. Not WebRetro or physical hardware.'}
(a.out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
