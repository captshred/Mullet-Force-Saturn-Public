#!/usr/bin/env python3
"""Check hardware texture budget, asset encoding, exact ISO payloads and source ID."""
from pathlib import Path
import struct,json,hashlib,re
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'assets/manifest.json').read_text())
image=(root/'build/mullet-force.bin').read_bytes()
def u32(data,offset): return struct.unpack_from('<I',data,offset)[0]
rec=image[16*2048+156:16*2048+190]
directory=image[u32(rec,2)*2048:u32(rec,2)*2048+u32(rec,10)]
files={}
def scan_directory(directory,prefix=''):
    off=0;entries=0
    while off<len(directory):
        length=directory[off]
        if not length: off=(off//2048+1)*2048; continue
        rec=directory[off:off+length]; off+=length;entries+=1
        rawname=rec[33:33+rec[32]]
        if rawname in (b'\0',b'\1'):continue
        name=rawname.decode('ascii',errors='replace').split(';')[0]
        data=image[u32(rec,2)*2048:u32(rec,2)*2048+u32(rec,10)]
        if rec[25]&2:scan_directory(data,prefix+name+'/')
        else:files[prefix+name]=data
    assert entries<=256,('Jo filesystem directory entry budget exceeded',prefix,entries)
scan_directory(directory)
from run_waist_validation import validate_active_disc as validate_waist_disc
files=validate_waist_disc(root,files)
from chuck_denim_validation import validate_active_disc
files=validate_active_disc(root,files)
total=manifest['runtime_hud_bytes']
for asset in manifest['assets']:
    data=(root/'assets/cd'/asset['name']).read_bytes()
    w,h=struct.unpack_from('<HH',data,12)
    bits=asset.get('bits',24)
    if bits==8:
        assert data[:3]==b'\0\1\1' and data[16:18]==b'\x08\0',asset
        assert struct.unpack_from('<H',data,5)[0]==256 and data[7]==24,asset
        assert len(data)==18+768+w*h and asset['vram']==w*h,asset
        raw=data[18+768:]
        assert max(raw)<254,asset
        assert (0 not in raw) if asset.get("palette_group")=="street" else (0 in raw),asset
        assert data[18:21]==b'\xff\0\xff',asset # transparent key is raw zero -> Jo one
    else:
        assert data[:3]==b'\0\0\2' and data[16:18]==b'\x18\0',asset
        assert len(data)==18+w*h*3 and asset['vram']==w*h*2,asset
    assert w==asset['width'] and h==asset['height'] and w%8==0 and w<=504 and h<=255,asset
    total+=asset['vram']
# Decode and assemble the exact runtime layers without Pillow.
key=bytes([255,0,255])
def tga_rgb(meta,flip=False):
    data=(root/'assets/cd'/meta['name']).read_bytes();w,h=struct.unpack_from('<HH',data,12)
    palette=data[18:786];raw=data[786:];rgb=[]
    for y in range(h):
        row=[palette[3*raw[(h-1-y)*w+x]:3*raw[(h-1-y)*w+x]+3][::-1] for x in range(w)]
        rgb.extend(row[::-1] if flip else row)
    return w,h,rgb
def assemble(parts,sw,sh,flip=False):
    pixels=[key]*(sw*sh)
    for part in parts:
        w,h,rgb=tga_rgb(part,flip);ax,ay=part['anchor']
        left=sw//2-(w-ax if flip else ax);top=92-ay
        for y in range(h):
            for x in range(w):
                color=rgb[y*w+x]
                if color!=key:
                    assert 0<=x+left<sw and 0<=y+top<sh
                    pixels[(y+top)*sw+x+left]=color
    return pixels
lowers=json.loads((root/'assets/normal-lowers.json').read_text())
for group,count in [('buck',15),('chuck',15),('enemy',12)]:
    actor=json.loads((root/f'assets/{group}-frames.json').read_text());assert len(actor['frames'])==count
    palette=None
    for frame in actor['frames']:
        data=(root/'assets/cd'/frame['name']).read_bytes();sw,sh=frame['source_size']
        if palette is None:palette=data[18:786]
        assert data[18:786]==palette
        parts=[lowers[frame['lower_id']],frame] if 'lower_id' in frame else [frame]
        pixels=assemble(parts,sw,sh)
        assert hashlib.sha256(b''.join(pixels)).hexdigest()==frame['source_rgb_sha256']
        mirrored=assemble(parts,sw,sh,True);expected=[]
        for y in range(sh):expected+=pixels[y*sw:(y+1)*sw][::-1]
        assert mirrored==expected
    anchors='{'+','.join('{%d,%d}'%tuple(m['anchor']) for m in actor['frames'])+'}'
    assert group+'_anchor[][2]='+anchors in (root/'src/art_data.h').read_text()
    if group!='enemy':
        ids='{'+','.join(str(m['lower_id']) for m in actor['frames'])+'}'
        assert group+'_lower_for_frame[]='+ids in (root/'src/art_data.h').read_text()
    print(f'PASS: {count} {group} full-frame pixel hashes, both mirrored runtime layer assemblies and anchors.')
anchors='{'+','.join('{%d,%d}'%tuple(m['anchor']) for m in lowers)+'}'
assert 'normal_lower_anchor[][2]='+anchors in (root/'src/art_data.h').read_text()
bat=json.loads((root/'assets/bat-frames.json').read_text());key=bytes([255,0,255])
assert bat['right_screen_rotation']=='counterclockwise'
for group in ('buck','chuck'):
    assert len(bat[group])==len(bat['air_'+group])==7
    vectors=[(f['tip'][0]-f['grip'][0],f['tip'][1]-f['grip'][1]) for f in bat[group]]
    for u,v in zip(vectors,vectors[1:]):
        assert u[0]*v[1]-u[1]*v[0]<0 # y-down screen coordinates: CCW
        assert (-u[0])*v[1]-u[1]*(-v[0])>0 # mirrored: clockwise
    for i,frame in enumerate(bat[group]):
        sw,sh=frame['source_size']
        for airborne in (False,True):
            lower=bat['air_legs'][bat['air_lower_for_frame'][i]] if airborne else bat['legs']
            directions=[]
            for flip in (False,True):
                pixels=[key]*(sw*sh)
                for part in (lower,frame):
                    w,h,rgb=tga_rgb(part,flip);ax,ay=part['anchor']
                    left=sw//2-(w-ax if flip else ax);top=92-ay
                    for y in range(h):
                        for x in range(w):
                            color=rgb[y*w+x]
                            if color!=key:
                                assert 0<x+left<sw-1 and 0<y+top<sh-1
                                pixels[(y+top)*sw+x+left]=color
                directions.append(pixels)
            expected_hash=bat['air_'+group][i]['source_rgb_sha256'] if airborne else frame['source_rgb_sha256']
            assert hashlib.sha256(b''.join(directions[0])).hexdigest()==expected_hash
            expected=[]
            for y in range(sh):expected+=directions[0][y*sw:(y+1)*sw][::-1]
            assert directions[1]==expected
            # Geometry is attached to actual wood pixels, not just a direction label.
            tx=sw//2+frame['tip'][0];ty=frame['tip'][1]
            wood={bytes.fromhex(c) for c in ('b88850','e0b878','806038','d0a068')}
            assert sum(directions[0][y*sw+x] in wood for y in range(max(0,ty-4),min(sh,ty+5))
                       for x in range(max(0,tx-4),min(sw,tx+5)))>=5
    anchors='{'+','.join('{%d,%d}'%tuple(m['anchor']) for m in bat[group])+'}'
    assert group+'_bat_anchor[][2]='+anchors in (root/'src/art_data.h').read_text()
assert 'bat_legs_anchor[2]={%d,%d}'%tuple(bat['legs']['anchor']) in (root/'src/art_data.h').read_text()
anchors='{'+','.join('{%d,%d}'%tuple(m['anchor']) for m in bat['air_legs'])+'}'
assert 'air_legs_anchor[][2]='+anchors in (root/'src/art_data.h').read_text()
assert 'air_lower_for_frame[]={'+','.join(str(i) for i in bat['air_lower_for_frame'])+'}' in (root/'src/art_data.h').read_text()
print('PASS: ground/air bat assemblies, both mirrored anchors, unclipped bounds, CCW right/CW left arc and real wood tips.')
torch=json.loads((root/'assets/torch-frames.json').read_text())
assert torch['nozzle']==[34,52] and torch['floor']==[74,92]
for group in ('buck','chuck'):
    assert len(torch[group])==3
    for frame in torch[group]:
        sw,sh=frame['source_size'];parts=[torch['legs'],frame]
        pixels=assemble(parts,sw,sh);assert hashlib.sha256(b''.join(pixels)).hexdigest()==frame['source_rgb_sha256']
        mirrored=assemble(parts,sw,sh,True);expected=[]
        for y in range(sh):expected+=pixels[y*sw:(y+1)*sw][::-1]
        assert mirrored==expected
    anchors='{'+','.join('{%d,%d}'%tuple(m['anchor']) for m in torch[group])+'}'
    assert group+'_torch_anchor[][2]='+anchors in (root/'src/art_data.h').read_text()
for f in torch['flames']:
    sw,sh=f['source_size'];pixels=assemble([f],sw,sh)
    assert hashlib.sha256(b''.join(pixels)).hexdigest()==f['source_rgb_sha256']
    hot={bytes.fromhex(c) for c in ('fff0c0','ffd868','ffc050')}
    assert all(pixels[(52+i)*sw+sw//2+34+i] in hot for i in range(40))
    assert pixels[92*sw+sw//2+74]!=key
anchors='{'+','.join('{%d,%d}'%tuple(m['anchor']) for m in torch['flames'])+'}'
assert 'flame_anchor[][2]='+anchors in (root/'src/art_data.h').read_text()
print('PASS: both torch costumes/poses mirrored, flame core connects nozzle to floor, generated anchors exact.')
palettes={}
for asset in manifest['assets']:
    if asset.get('bits')!=8: continue
    key=asset['palette_group']; data=(root/'assets/cd'/asset['name']).read_bytes()[18:786]
    if key in palettes: assert palettes[key]==data
    palettes[key]=data
assert set(palettes)=={'street','buck','chuck','enemy','fire'}
assert len(palettes)+2<=8 # five asset palettes + warm enemy alternative + font
print('PASS: five asset palettes + one runtime warm-flash palette fit alongside font in CRAM.')
for p in (root/'assets/cd').iterdir():
    assert files[p.name.upper()]==p.read_bytes(),p.name
assert total==manifest['total_texture_bytes'] and total<manifest['texture_budget']
assert manifest['texture_budget']==0x7fef8-0x10000
aligned_total=sum((a['vram']+31)&~31 for a in manifest['assets'])+21760
from street_validation import validate_street
recovered=validate_street(root,files)
from parallax_validation import validate_parallax
validate_parallax(root,files)
aligned_total-=recovered
assert aligned_total<manifest['texture_budget']
print(f'PASS: normal runtime VDP1 textures with SDK 32-byte allocation alignment: {aligned_total} bytes.')
from gallery_validation import validate_gallery
validate_gallery(root,files,aligned_total)
from animation_validation import validate_animation
animation_bytes=validate_animation(root,files)
from polish_validation import validate_polish
polish_bytes=validate_polish(root,files)
source_list=(root/'build/SOURCE-SHA256SUMS.txt').read_bytes()
for line in source_list.decode().splitlines():
    digest,name=line.split('  ',1)
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
source_hash=hashlib.sha256(source_list).hexdigest()
assert source_hash.encode() in files['0.BIN']
assert source_hash in (root/'build/BUILD-INFO.txt').read_text()
end=int(re.search(r'0x([0-9a-f]+)\s+__bend', (root/'build/game.map').read_text()).group(1),16)
assert end<0x060c0000,hex(end) # SGL owns the sort/DMA buffers starting here.
print(f'PASS: all {len(manifest["assets"])} TGA + 3 PCM + native music payloads match ISO; TGA formats valid.')
gallery_bytes=10784 if (root/'build/gallery-mode.txt').read_text().strip()=='1' else 0
from swagger_validation import validate_swagger
swagger=validate_swagger(root,files)
from original_three_validation import validate_original_three
original=validate_original_three(root,files)
runtime_bytes=original['boot_vdp1_bytes'] if original else swagger['boot_vdp1_bytes'] if swagger else aligned_total+gallery_bytes+animation_bytes+polish_bytes
base_runtime_bytes=runtime_bytes
cp_mode=(root/'build/corporate-mode.txt').read_text().strip()=='1'
if cp_mode:
    from corporate_animation_validation import validate_corporate_animation
    if (root/'build/corporate-lighting-mode.txt').read_text().strip()=='1':
        from corporate_lighting_validation import validate_corporate_lighting
        cp=validate_corporate_lighting(root,files)
    elif (root/'build/corporate-refined-mode.txt').read_text().strip()=='1':
        from corporate_refined_validation import validate_corporate_refined
        cp=validate_corporate_refined(root,files)
    else:cp=validate_corporate_animation(root,files)
    runtime_bytes+=cp['texture_bytes']
    assert runtime_bytes==cp['boot_bytes'] and runtime_bytes<manifest['texture_budget']
if (root/'build/run-bat-mode.txt').exists() and (root/'build/run-bat-mode.txt').read_text().strip()=='1':
    from running_validation import validate_running
    running=validate_running(root,files)
    runtime_bytes+=running['texture_bytes']
    assert runtime_bytes==running['boot_vdp1_bytes'] and runtime_bytes<manifest['texture_budget']
if (root/'build/running-bat-visual-mode.txt').exists() and (root/'build/running-bat-visual-mode.txt').read_text().strip()=='1':
    from running_bat_visual_validation import validate_rbv
    rv=validate_rbv(root,files);runtime_bytes+=rv['texture_bytes'];assert runtime_bytes==rv['boot_bytes']
if (root/'build/combat-animation-mode.txt').exists() and (root/'build/combat-animation-mode.txt').read_text().strip()=='1':
    from combat_animation_validation import validate_combat
    momentum=(root/'build/bat-momentum-mode.txt').exists() and (root/'build/bat-momentum-mode.txt').read_text().strip()=='1'
    combat=validate_combat(root,None if momentum else files)
    if momentum:
        from bat_momentum_validation import validate_momentum
        sequence=(root/'build/attack-sequence-mode.txt').exists() and (root/'build/attack-sequence-mode.txt').read_text().strip()=='1'
        combat=validate_momentum(root,None if sequence else files)
        if sequence:
            from attack_sequence_validation import validate_sequence
            combat=validate_sequence(root,files)
    runtime_bytes+=combat['texture_bytes'];assert runtime_bytes==combat['boot_bytes']
if (root/'build/jab-cohesion-mode.txt').exists() and (root/'build/jab-cohesion-mode.txt').read_text().strip()=='1':
    from jab_cohesion_validation import validate_jab
    jab=validate_jab(root);assert runtime_bytes==jab['texture_bytes']
if (root/'build/hq-torch-mode.txt').exists() and (root/'build/hq-torch-mode.txt').read_text().strip()=='1':
    from hq_torch_validation import validate_hq_torch
    ht=validate_hq_torch(root,files);runtime_bytes+=ht['texture_bytes']-ht['replaced_bytes'];assert runtime_bytes==ht['boot_bytes']
if (root/'build/hq-jump-mode.txt').exists() and (root/'build/hq-jump-mode.txt').read_text().strip()=='1':
    from hq_jump_validation import validate_hq_jump
    hj=validate_hq_jump(root,files);runtime_bytes+=hj['texture_bytes']-hj['replaced_bytes'];assert runtime_bytes==hj['boot_bytes']
# Later presentation-only replacements use the same immutable legacy disc files.
for mode,directory,subdir in [('corporate-hq-mode.txt','corporate-punk-hq-combat',''),('player-hurt-mode.txt','player-hurt','HQHURT/'),('player-death-mode.txt','player-death','HQDEATH/')]:
    flag=root/'build'/mode
    if not flag.exists() or flag.read_text().strip()!='1':continue
    m=json.loads((root/f'assets/{directory}/manifest.json').read_text())
    if directory=='corporate-punk-hq-combat':runtime_bytes+=m['texture_bytes']-56960
    else:runtime_bytes+=m['bytes']-m['replaced_bytes']
    assert runtime_bytes==m['boot_bytes'] and runtime_bytes<458488 and m['slots']<=255
    for item in m['resources']:
        assert files[subdir+item['name']]==(root/f'assets/{directory}'/item['name']).read_bytes()
    if directory=='player-hurt':pairs=[('RC0.TGA','RC0.TGA'),('RC1.TGA','RC1.TGA'),('CT0.TGA','COMBAT/CT0.TGA'),('CT1.TGA','COMBAT/CT1.TGA')]
    elif directory=='player-death':pairs=[('RD0.TGA','RD0.TGA'),('RD1.TGA','RD1.TGA'),('DT0.TGA','COMBAT/DT0.TGA'),('DT1.TGA','COMBAT/DT1.TGA')]
    else:pairs=[]
    for source,target in pairs:assert files[target]==(root/f'assets/{directory}'/source).read_bytes()
if (root/'build/punch-combo-mode.txt').exists() and (root/'build/punch-combo-mode.txt').read_text().strip()=='1':
    from punch_combo_validation import validate as validate_combo
    combo=validate_combo(root,files);runtime_bytes+=combo['added_bytes'];assert runtime_bytes==combo['boot_bytes'] and combo['definitions']<=255
print(f'PASS: runtime VDP1 textures at boot {runtime_bytes}/{manifest["texture_budget"]} bytes; BSS ends {end:#x}.')
print('PASS: current gameplay/assets source fingerprint matches executable:',source_hash)

playable=(root/'build/playable-animation-mode.txt').read_text().strip()=='1'
assert (b'HIGH DETAIL MOVEMENT' in files['0.BIN'])==playable
if playable:
    assert (root/'build/animation-mode.txt').read_text().strip()=='1'
    assert base_runtime_bytes==(original['boot_vdp1_bytes'] if original else swagger['boot_vdp1_bytes'] if swagger else 427104)
    print('PASS: playable renderer reuses the loaded character IDs; no duplicate gameplay texture bank.')

from knee_lift_validation import validate_knee_lift
knee=validate_knee_lift(root,files)
if knee:assert base_runtime_bytes==351104
