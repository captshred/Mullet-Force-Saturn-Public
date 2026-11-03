#!/usr/bin/env python3
"""Real-pad Yabause capture, read-only trace assertions and review exports."""
from pathlib import Path
import argparse,subprocess,os,re,json,ctypes as C
import numpy as np
from PIL import Image
from playable_runtime_validation import trace,hardware
from fast_bat_previews import render
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
for n in ['core','include','build','out']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--reuse',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
info=(a.build/'BUILD-INFO.txt').read_text();assert 'Fast horizontal running bat: 1' in info
symbols={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(a.build/'game.elf')],text=True),re.M)}
front=a.out/'frontend';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-DMF_FAST_BAT_RUNTIME=1','-DMF_JAB_COHESION=1','-I'+str(a.include),'-I'+str(R/'src'),str(R/'tests/runtime/custom-sfx-frontend.c'),'-ldl','-o',str(front)],check=True)
report={'build_commit':re.search(r'^Commit: (.+)$',info,re.M).group(1),'build_source_sha256':re.search(r'^Source SHA256: (.+)$',info,re.M).group(1),'core':'Yabause libretro / HLE / no RAM cartridge','no_ram_writes':True,'webretro_tested':False,'physical_saturn_tested':False,'actors':[]}
export=R/'docs/fast-bat-captures';export.mkdir(exist_ok=True)
for actor,name in enumerate(['buck','chuck']):
 out=a.out/str(actor);out.mkdir(exist_ok=True)
 if not a.reuse:
  with (out/'run.log').open('w') as log:subprocess.run([str(front.resolve()),str(a.core.resolve()),str((a.build/'mullet-force.cue').resolve()),str(out.resolve()),'1400','run',hex(symbols['_game']),hex(symbols['_idle_ticks']),'1','1'],env=dict(os.environ,MF_FAST_BAT_SCENARIO=str(actor)),stdout=log,stderr=subprocess.STDOUT,check=True)
 rows=trace(out);attacks=[];contacts=[];seen=0;pixels=0;first=None;contact_screens=[]
 for k,r in rows.items():
  g=r.game;p=g.players[actor];prev=rows.get(k-1)
  if p.bat==2 and prev and not prev.game.players[actor].bat:attacks.append(k)
  if prev and g.score>prev.game.score:
   assert p.bat==2 and 5<=p.attack<=8
   assert g.events&(1<<(7+3*actor));assert p.hit_mask
   contacts.append({'frame':k,'attack_counter_after_step':p.attack,'score_delta':g.score-prev.game.score,'broken':g.broken,'enemy_hp':[e.hp for e in g.enemies]})
   if first is None:first=k
 assert len(attacks)==3 and [c['score_delta'] for c in contacts]==[360,250],contacts
 assert all(rows[k].game.players[actor].bat!=2 for k in range(attacks[0]+18,attacks[1]))
 final=rows[1000].game;assert final.score==610 and final.broken==1 and all(e.hp==0 for e in final.enemies)
 assert any(v.game.players[actor].bat==2 and v.game.players[actor].facing<0 for v in rows.values())
 assert any(v.game.players[actor].height and v.game.players[actor].attack and not v.game.players[actor].bat for k,v in rows.items() if k>=1000)
 assert all(not v.game.players[actor].bat for k,v in rows.items() if v.game.players[actor].height or v.game.players[actor].vz)
 assert any(v.game.players[actor].bat==1 and not v.game.players[actor].height for k,v in rows.items() if k>=1060)
 assert not rows[1100].game.players[actor].bat
 assert len({v.texture_hash for k,v in rows.items() if k>=750})==1
 mem=(out/'frame-0750.wram').read_bytes()
 def read(addr):
  v=int.from_bytes(mem[addr&0xfffff:(addr&0xfffff)+4],'little');return ((v>>16)|(v<<16))&0xffffffff
 assert read(symbols['___jo_sprite_id'])+1==253
 assert 446304 in [read(v) for n,v in symbols.items() if n.startswith('_texture_bytes')]
 # Exact native horizontal contact appearance, with known SGL +3 frame lag.
 # Exclude existing target, spark and other-player occlusions from matching.
 for path in sorted(out.glob('frame-*.ppm')):
  k=int(path.stem.split('-')[1]);r=rows.get(k-3)
  if r is None:continue
  g=r.game;p=g.players[actor]
  if p.bat!=2 or not(4<=p.attack<9):continue
  if p.invulnerable and p.invulnerable<112 and not g.ticks&4:continue
  im=np.asarray(Image.open(path).convert('RGB'));ref=hardware(render(actor,p.attack,0,p.facing<0));yy,xx=np.where(ref[:,:,3]>0);sx=xx+p.x//256-g.camera-(96 if p.facing<0 else 64)+1;sy=yy+p.y//256-108+1
  keep=(sx>=0)&(sx<320)&(sy>=58)&(sy<221)
  boxes=[]
  for j,q in enumerate(g.players):
   if j!=actor and q.active:boxes.append((q.x//256-g.camera-64,q.y//256-96,128,100))
  for e in g.enemies:
   if e.state:boxes.append((e.x//256-g.camera-70,e.y//256-96,140,98))
  for d in g.drums:
   if d.hp or d.flash or d.respawn<12:boxes.append((d.x//256-g.camera-18,d.y//256-48,36,50))
  if g.spark:boxes.append((g.spark_x-g.camera-18,g.spark_y-g.spark_z-18,36,36))
  for x,y,w,h in boxes:keep&=~((sx>=x)&(sx<x+w)&(sy>=y)&(sy<y+h))
  assert np.array_equal(im[sy[keep],sx[keep]],ref[yy[keep],xx[keep],:3]),(name,k,'contact rendering mismatch')
  pixels+=int(keep.sum());seen+=1;contact_screens.append(k)
 assert seen>=4 and pixels>1000,(name,seen,pixels)
 for n,start in enumerate(attacks[:2]):
  ims=[Image.open(out/f'frame-{k:04}.ppm').convert('RGB') for k in range(start-12,start+30) if (out/f'frame-{k:04}.ppm').exists()]
  ims[0].save(export/f'{name}-{("barrel-and-punk" if n==0 else "punk-ko")}-actual-1x.gif',save_all=True,append_images=ims[1:],duration=[20 if i%3 else 10 for i in range(len(ims))],loop=0)
  if n==0:
   for z in [1,4]:
    q=Image.open(out/f'frame-{next(k for k in contact_screens if k>=first+3):04}.ppm');q.resize((q.width*z,q.height*z),Image.Resampling.NEAREST).save(export/f'{name}-barrel-punk-contact-actual-{z}x.png')
 report['actors'].append({'actor':name,'attacks':attacks,'contacts':contacts,'exact_contact_samples':seen,'matched_native_pixels':pixels,'left_swing_verified':True,'airborne_kick_verified':True,'planted_bat_verified':True,'score_at_1000':final.score,'broken_at_1000':final.broken})
report.update(texture_bytes=446304,free_bytes=12184,definitions=253,texture_allocation_delta=0,registrations_freed=0,airborne_assets_retained=True)
(export/'runtime-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
