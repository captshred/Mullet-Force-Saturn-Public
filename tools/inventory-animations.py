#!/usr/bin/env python3
"""Read-only inventory of existing authored pixels and runtime contracts."""
from pathlib import Path
import hashlib,json,re,struct
r=Path(__file__).resolve().parents[1];manifest=json.loads((r/'assets/manifest.json').read_text())
resources={a['name']:dict(a,aligned_bytes=(a['vram']+31)&~31,sha256=hashlib.sha256((r/'assets/cd'/a['name']).read_bytes()).hexdigest()) for a in manifest['assets']}
actors={}
for actor in ['buck','chuck']:
 data=json.loads((r/f'assets/{actor}-frames.json').read_text())
 bat=json.loads((r/'assets/bat-frames.json').read_text())[actor]
 torch=json.loads((r/'assets/torch-frames.json').read_text())[actor]
 frames=[]
 for category,items in [('normal',data['frames']),('bat',bat),('torch',torch)]:
  for i,f in enumerate(items):
   d=dict(f,index=i,category=category,resource=resources[f['name']]);frames.append(d)
 actors[actor]={'standing_height':data['standing_height'],'frames':frames}
contract={
 'clock_hz':60,'normal_priority':['defeated','hurt','airborne','punch','landing','walk','idle'],
 'renderer_priority':['torch if alive and not hurt','bat if alive and attacking and not hurt','normal'],
 'states':[
 {'state':'idle','frames':[0,1],'selector':'(g.ticks/32)%2','ticks_per_pose':32},
 {'state':'walk','frames':list(range(2,8)),'selector':'2+(p.walk/5)%6','ticks_per_pose':5,'loop_ticks':30},
 {'state':'punch/hurt-coil','frames':[8],'attack_counters':[1,5],'hurt_ticks':12},
 {'state':'punch-contact','frames':[9],'attack_counters':[6,10],'active_ground':[6,10]},
 {'state':'punch-recovery','frames':[10],'attack_counters':[11,24]},
 {'state':'jump-rise','frames':[11],'selector':'height>0 and vz>1200; not attacking'},
 {'state':'jump-air','frames':[12],'selector':'height>0 and vz<=1200; not attacking'},
 {'state':'landing/defeated','frames':[13],'landing_ticks':6,'defeated_recovery_ticks':120},
 {'state':'air-attack','frames':[14],'selector':'height>0 and attack>0; normal renderer','active_air':[3,15]},
 {'state':'bat ground/air','frames':list(range(7)),'attack_counter_intervals':[[1,5],[6,11],[12,13],[14,16],[17,19],[20,27],[28,36]],'active_counters':[12,17],'air_land_resume_counter':28},
 {'state':'torch','frames':[0,1,2],'names':['equip','fire','away'],'charge_ticks':60,'cue_ticks':40,'equip_ticks':6,'away_ticks':6,'note':'Current charge path enters FIRE directly; EQUIP renderer/timer exists but is not entered by this path. Fire held until release/interruption. Damage interval 12 ticks.'}
 ],
 'jump':{'initial_vz_24_8':1510,'gravity_24_8_per_tick':74,'normal_flight_ticks':42,'maximum_rendered_height_pixels':63,'root_translation':'world_y - height/256'},
 'hitboxes_relative_to_ground_root':{'player_hurt':{'x':[-12,12],'ground_depth':[-8,8],'z_above_air_height':[4,84]},'enemy_hurt':{'x':[-13,13],'ground_depth':[-8,8],'z':[4,84]},'punch_right':{'x':[6,52],'depth':[-8,8],'z':[30,58]},'air_kick_right':{'x':[6,54],'depth':[-8,8],'z_above_air_height':[24,45]},'bat_right':{'x':[6,78],'depth':[-8,8],'z_by_counter':{'12..13':[14,58],'14..16':[40,64],'17':[54,90]}},'enemy_attack_right':{'x':[8,40],'depth':[-8,8],'z':[36,64]},'torch':{'x_nominal':[34,74],'x_tolerance':[30,78],'depth_tolerance':8,'sloping_z':'40*(74-x)/40 with +/-5 tolerance; ground only'}},
 'simulation_notes':['Counters increment at end of simulation; intervals are counter values, not a promise of first rendered dwell.','3-tick hitstop freezes g.ticks, locomotion and attack counters; input/torch preprocessing precedes hitstop.','A target is hit once per punch/bat via hit_mask. Artwork must not change active intervals.','Invulnerability 60 ticks after hit; hurt 12; defeated recovery 120. Respawn gives 120 invulnerability ticks.','Ground bat freezes walking; normal movement 390/256 px/tick, ground punch 100/256, torch 140/256, diagonal factor 181/256.']}
shared_names=[n for n in resources if n.startswith(('NL','AL')) or n=='LEGS.TGA']
groups={}
for a in resources.values():
 key=a.get('palette_group','rgb16');g=groups.setdefault(key,{'textures':0,'aligned_bytes':0,'raw_bytes':0});g['textures']+=1;g['aligned_bytes']+=a['aligned_bytes'];g['raw_bytes']+=a['vram']
anchors={n:json.loads(v.replace('{','[').replace('}',']')) for n,v in re.findall(r'static const short (\w+)(?:\[[^\]]*\])+\s*=\s*(\{.*?\});',(r/'src/art_data.h').read_text())}
result={'anchor_arrays':anchors,'source_commit':'ba4938ecac49715f241446b617f5336d95888d0a','source_hashes':{n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in ['src/game.c','src/game.h','src/combat_config.h','src/art_data.h','tools/draw-assets.py','tools/buck_art.py']},'actors':actors,'shared_lowers':[resources[n] for n in shared_names],'resources_by_palette':groups,'runtime_contract':contract,'original_vdp2_runtime_vdp1_bytes':291552,'with_approved_gallery_bytes':302336,'enemies_current_maximum':2}
(r/'docs/animation/current-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['# Existing Buck / Chuck frame inventory','','Generated read-only from the existing metadata and texture manifest. No asset generator is run.','', '| Actor | Set | Index | Pose | File | Dimensions | Anchor | Raw / aligned bytes |','|---|---|---:|---|---|---|---|---|']
for actor,a in actors.items():
 for f in a['frames']:
  t=f['resource'];lines.append(f"| {actor} | {f['category']} | {f['index']} | {f.get('pose','')} | {f['name']} | {t['width']}x{t['height']} | {f['anchor']} | {t['vram']} / {t['aligned_bytes']} |")
lines+=['','Shared lower-body resources (all use Buck palette):','','| File | Dimensions | Raw / aligned bytes |','|---|---|---|']
for n in shared_names:
 a=resources[n];lines.append(f"| {n} | {a['width']}x{a['height']} | {a['vram']} / {a['aligned_bytes']} |")
lines+=['','Full crop origins, source-canvas dimensions, anchors, lower-piece mappings, bat grips/tips, SHA-256 values, hitboxes and timing contracts are recorded in `current-inventory.json`. Runtime anchor arrays are preserved verbatim in `src/art_data.h`.']
(r/'docs/animation/current-inventory.md').write_text('\n'.join(lines)+'\n')
print('Inventory: 15 normal + 7 bat + 3 torch upper poses per fighter; 15 normal, 1 bat and 3 air shared lower textures. Original resources unchanged.')
