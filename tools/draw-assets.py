#!/usr/bin/env python3
"""Original, deterministic pixel artwork and PCM synthesis. Pillow is authoring-only.
Actors use native 96px canvases, centered anchors and sole baseline y=92.
RGB magenta is transparent; TGA is uncompressed 24-bit, bottom-up BGR.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import random, struct, math, json, hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/cd'; OUT.mkdir(parents=True,exist_ok=True)
PRE=ROOT/'assets/previews'; PRE.mkdir(exist_ok=True)
KEY=(255,0,255)
manifest=[]
def export(im,name):
    im=im.convert('RGB'); w,h=im.size
    assert w%8==0 and w<=504 and h<=255
    header=struct.pack('<BBBHHBHHHHBB',0,0,2,0,0,0,0,0,w,h,24,0)
    pixels=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes('raw','BGR')
    (OUT/(name+'.TGA')).write_bytes(header+pixels)
    manifest.append(dict(name=name+'.TGA',width=w,height=h,vram=w*h*2))
def export_indexed(images,names,group):
    palette=[KEY]+sorted(set(c for im in images for c in im.convert('RGB').getdata())-{KEY})
    assert len(palette)<255,(group,len(palette))
    indices={c:i for i,c in enumerate(palette)}
    color_map=bytes(v for c in palette+[(0,0,0)]*(256-len(palette)) for v in c[::-1])
    for im,name in zip(images,names):
        w,h=im.size; assert w%8==0 and h<=255
        header=struct.pack('<BBBHHBHHHHBB',0,1,1,0,256,24,0,0,w,h,8,0)
        pixels=bytes(indices[c] for c in im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGB').getdata())
        (OUT/(name+'.TGA')).write_bytes(header+color_map+pixels)
        manifest.append(dict(name=name+'.TGA',width=w,height=h,bits=8,vram=w*h,palette_group=group))
# Hand-set compact sign alphabet; single pixels, no smoothing.
FONT={
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01110'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['111','010','010','010','010','010','111'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','10101','10011','10001','10001','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','11011','10001'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00001','00010','00100','01000','10000','11111'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'7':['11111','00001','00010','00100','01000','01000','01000'],
' ':['000']*7,'-':['00000','00000','00000','11111','00000','00000','00000']}
def text(d,xy,s,color,scale=1):
    x,y=xy
    for c in s:
        rows=FONT.get(c,FONT[' ']); w=len(rows[0])
        for yy,row in enumerate(rows):
            for xx,v in enumerate(row):
                if v=='1': d.rectangle((x+xx*scale,y+yy*scale,x+(xx+1)*scale-1,y+(yy+1)*scale-1),fill=color)
        x+=(w+1)*scale
# Night street, a fully authored 640x240 panorama, no external art.
rng=random.Random(73)
street=Image.new('RGB',(640,240)); d=ImageDraw.Draw(street)
for y in range(240):
    c=(9+y//25,11+y//22,28+y//15) if y<145 else (26+(y-145)//11,31+(y-145)//12,47+(y-145)//9)
    d.line((0,y,639,y),fill=c)
# Distant skyline, aerials and warm occupied windows.
for x in range(0,640,27):
    roof=rng.randrange(12,48); w=rng.randrange(18,31)
    d.rectangle((x,roof,x+w,80),fill=(17,24,41))
    d.line((x+5,roof,x+5,roof-8),fill=(39,40,61))
    for yy in range(roof+7,78,9):
        for xx in range(x+4,x+w-2,6):
            if rng.random()<.4: d.rectangle((xx,yy,xx+1,yy+2),fill=rng.choice([(76,74,90),(137,107,88),(49,78,98)]))
d.ellipse((525,12,542,29),fill=(167,177,193)); d.ellipse((520,10,537,26),fill=(10,12,29))
# Brick facade and mortar.
d.rectangle((0,56,639,143),fill=(48,29,49))
for yy in range(58,143,7):
    d.line((0,yy,639,yy),fill=(25,24,40))
    for xx in range(-20+(yy//7%2)*11,640,22):
        d.line((xx,yy,xx,yy+6),fill=(25,24,40))
        d.line((xx+2,yy+1,xx+18,yy+1),fill=(64,37,58))
# Storefront modules, own signage and layout.
for x,w,name,neon in [(8,136,'NIGHT OWL',(54,210,225)),(166,205,'MULLET FORCE',(255,85,158)),(397,113,'ION ARCADE',(117,151,255)),(536,98,'VINYL',(255,179,64))]:
    d.rectangle((x-3,70,x+w+3,145),fill=(11,17,29))
    d.rectangle((x,76,x+w,98),fill=(40,29,61),outline=neon,width=1)
    text(d,(x+6,84),name,neon)
    for wx in range(x+4,x+w-18,27):
        d.rectangle((wx,105,wx+22,137),fill=(16,36,53),outline=(51,59,75))
        d.polygon([(wx+2,107),(wx+19,107),(wx+2,124)],fill=(27,61,77))
        d.line((wx+2,131,wx+19,114),fill=(40,77,90))
        if name=='ION ARCADE':
            d.polygon([(wx+5,111),(wx+16,111),(wx+17,122),(wx+20,125),(wx+18,135),(wx+4,135),(wx+6,123)],fill=(19,27,43),outline=(51,59,75))
            d.rectangle((wx+7,113,wx+14,120),fill=(41,64,78))
            d.line((wx+8,116,wx+12,115),fill=(72,84,97))
            d.line((wx+7,125,wx+17,125),fill=(74,61,86))
            d.point((wx+12,124),fill=(106,81,96));d.point((wx+15,125),fill=(83,101,107))
        elif name=='VINYL':
            d.rectangle((wx+4,111,wx+18,127),fill=(51,46,61),outline=(70,65,76))
            d.ellipse((wx+6,114,wx+17,125),fill=(14,23,36),outline=(57,62,75))
            d.ellipse((wx+10,118,wx+13,121),fill=(124,96,72))
            d.line((wx+5,132,wx+19,132),fill=(73,63,72))
            for rx in range(wx+6,wx+19,3): d.line((rx,129,rx,135),fill=(51,56,73))
        d.line((wx,139,wx+22,139),fill=neon)
    d.rectangle((x-1,99,x+w+1,103),fill=(65,36,68))
    for ax in range(x,x+w,9): d.rectangle((ax,99,ax+3,102),fill=neon)
# Central club entrance and marquee.
d.rectangle((232,106,303,145),fill=(10,11,26),outline=(100,49,104))
d.polygon([(235,108),(254,111),(250,143),(236,143)],fill=(88,29,70))
d.polygon([(300,108),(281,111),(285,143),(300,143)],fill=(88,29,70))
d.rectangle((260,113,278,145),fill=(26,44,63)); d.line((269,115,269,142),fill=(215,178,88))
text(d,(238,62),'LIVE TONIGHT',(236,193,122))
# Pavement, curb and grates.
d.rectangle((0,146,639,157),fill=(56,63,81)); d.line((0,146,639,146),fill=(107,105,121))
for x in range(0,640,30): d.line((x,148,x-3,157),fill=(27,33,52))
d.line((0,158,639,158),fill=(16,22,35)); d.line((0,160,639,160),fill=(96,88,106))
for yy in [178,203,232]:
    for xx in range(-10,650,48): d.line((xx,yy,xx+31,yy),fill=(44,49,66))
for i in range(1500):
    x=rng.randrange(640); y=rng.randrange(163,240)
    d.point((x,y),fill=rng.choice([(48,51,68),(24,30,45),(62,53,71)]))
for x in [40,345,511]:
    d.polygon([(x,187),(x+38,187),(x+43,193),(x-5,193)],fill=(20,26,39),outline=(57,65,77))
    for k in range(6): d.line((x+k*6,188,x+k*6+1,191),fill=(80,80,91))
# Neon reflections: broken, stepped ribbons in wet road.
for x,c in [(54,(38,96,113)),(262,(112,43,91)),(448,(57,70,119)),(578,(111,79,48))]:
    for y in range(163,235,4):
        half=4+(y-160)//4; jitter=rng.randrange(-6,7)
        d.line((x-half+jitter,y,x+half+jitter,y),fill=c)
        if y%3==0: d.line((x-half+3,y+1,x+half-5,y+1),fill=tuple(n//2 for n in c))
# Two streetlights; small cones stay behind players.
for x in [153,523]:
    d.polygon([(x-3,69),(x-29,151),(x+34,151),(x+5,69)],fill=(45,48,66))
    d.line((x,65,x,153),fill=(9,16,29),width=4); d.line((x+1,69,x+1,151),fill=(83,86,112))
    d.line((x,65,x+17,65),fill=(79,80,101),width=3)
    d.rectangle((x+12,63,x+23,66),fill=(205,184,138)); d.rectangle((x+14,67,x+21,68),fill=(250,221,166))
    d.rectangle((x-5,151,x+5,156),fill=(13,20,35))
# Poster, trash, manhole, lane boundary markers.
d.rectangle((378,112,390,134),fill=(210,174,127)); text(d,(380,115),'MF',(61,35,54)); d.line((379,126,388,126),fill=(61,35,54))
d.ellipse((352,216,393,229),fill=(22,28,43),outline=(86,78,98))
for j in range(4): d.line((358,220+j*2,385,220+j*2),fill=(45,48,65))
for x in range(18,640,89): d.rectangle((x,234,x+28,235),fill=(153,128,90))
for x in [81,315,603]:
    d.polygon([(x,169),(x+7,168),(x+10,171),(x+3,173)],fill=(133,129,133))
export_indexed([street.crop((i*128,0,(i+1)*128,240)) for i in range(5)],[f'ST{i}' for i in range(5)],'street')
street.save(PRE/'street.png')
# Lossless removal of transparent margins: actual pixel scale never changes.
from buck_art import draw_buck, draw_air_legs, FRAME_NAMES, BAT_GRIPS, BAT_TIPS
from enemy_art import draw_enemy, FRAME_NAMES as ENEMY_NAMES
from PIL import ImageChops
anchor_tables=[]
# Share exact normal lower-body pixels across both costumes; no resampling.
normal_lowers=[];normal_lower_images=[];normal_lower_lookup={}
normal_lower_for={}
for group,chuck in [('buck',False),('chuck',True)]:
    ids=[]
    for i in range(15):
        src=draw_buck(i,chuck=chuck);low=Image.new('RGB',src.size,KEY)
        low.paste(src.crop((0,60,src.width,96)),(0,60))
        box=ImageChops.difference(low,Image.new('RGB',low.size,KEY)).getbbox()
        compact=low.crop(box);digest=hashlib.sha256(compact.tobytes()).hexdigest()
        # The two legs' location within their source canvas may differ even
        # when cropped pixels match. Anchor comparison avoids false dedup.
        identity=(digest,compact.size,src.width//2-box[0],92-box[1])
        if identity not in normal_lower_lookup:
            index=len(normal_lower_images);normal_lower_lookup[identity]=index
            normal_lower_images.append(low)
        ids.append(normal_lower_lookup[identity])
    normal_lower_for[group]=ids

torch_metadata={}
bat_metadata={"air_lower_for_frame":[0,0,1,1,2,2,0],"right_screen_rotation":"counterclockwise"}
BAT_NAMES=['bat-draw','bat-coil','bat-accelerate','bat-contact','bat-sweep','bat-follow','bat-recover']
def crop_actor(im,name):
    box=ImageChops.difference(im,Image.new('RGB',im.size,KEY)).getbbox()
    width=((box[2]-box[0]+7)//8)*8
    left=box[0];top=box[1]
    canvas=Image.new('RGB',(width,box[3]-top),KEY);canvas.paste(im,(-left,-top))
    return canvas,dict(name=name,anchor=[im.width//2-left,92-top],source_size=list(im.size),crop_origin=[left,top],source_rgb_sha256=hashlib.sha256(im.tobytes()).hexdigest())
def export_actor(prefix,group,images,names):
    cropped=[];metadata=[]
    for i,im in enumerate(images):
        upper=im.copy()
        if group in ('buck','chuck'):upper.paste(KEY,(0,60,im.width,96))
        crop,meta=crop_actor(upper,f'{prefix}{i:02}.TGA');meta['pose']=names[i]
        meta['source_rgb_sha256']=hashlib.sha256(im.tobytes()).hexdigest()
        if group in ('buck','chuck'):meta['lower_id']=normal_lower_for[group][i]
        cropped.append(crop);metadata.append(meta)
    extra=[];extra_names=[]
    if group=='buck':
        for i,low in enumerate(normal_lower_images):
            crop,meta=crop_actor(low,f'NL{i:02}.TGA');normal_lowers.append(meta)
            extra.append(crop);extra_names.append(f'NL{i:02}')
        anchor_tables.append('static const short normal_lower_anchor[][2]={'+','.join('{%d,%d}'%tuple(m['anchor']) for m in normal_lowers)+'};\n')
    if group in ('buck','chuck'):
        anchor_tables.append('static const short '+group+'_lower_for_frame[]={'+','.join(str(i) for i in normal_lower_for[group])+'};\n')
        # The fixed planted stance is identical beneath the belt. Share that
        # lower body, retain every new upper-body/bat pixel at native scale.
        base=draw_buck(0);lower=Image.new('RGB',base.size,KEY)
        lower.paste(base.crop((0,58,base.width,96)),(0,58))
        bt=[];bm=[];bp='BT' if group=='buck' else 'CT'
        for i in range(7):
            full=draw_buck(15+i,chuck=group=='chuck');upper=full.copy()
            shared=Image.new('RGB',full.size,KEY);shared.paste(lower,(full.width//2-lower.width//2,0))
            for y in range(58,96):
                for x in range(full.width):
                    if upper.getpixel((x,y))==shared.getpixel((x,y)):upper.putpixel((x,y),KEY)
            crop,meta=crop_actor(upper,f'{bp}{i:02}.TGA');meta['pose']=BAT_NAMES[i]
            meta['upper_rgb_sha256']=meta['source_rgb_sha256']
            meta['source_rgb_sha256']=hashlib.sha256(full.tobytes()).hexdigest()
            meta['grip']=BAT_GRIPS[i];meta['tip']=BAT_TIPS[i]
            bt.append(crop);bm.append(meta)
        extra+=bt;extra_names+=[f'{bp}{i:02}' for i in range(7)]
        bat_metadata[group]=bm
        anchor_tables.append('static const short '+group+'_bat_anchor[][2]={'+','.join('{%d,%d}'%tuple(m['anchor']) for m in bm)+'};\n')
        tor=[]
        for i in range(3):
            full=draw_buck(22+i,chuck=group=='chuck');upper=full.copy()
            common=Image.new('RGB',full.size,KEY);common.paste(lower,(full.width//2-lower.width//2,0))
            for y in range(60,96):
                for x in range(full.width):
                    if upper.getpixel((x,y))==common.getpixel((x,y)):upper.putpixel((x,y),KEY)
            name=('TU' if group=='buck' else 'TC')+str(i)
            crop,meta=crop_actor(upper,name+'.TGA');meta['source_rgb_sha256']=hashlib.sha256(full.tobytes()).hexdigest()
            meta['pose']=['equip','aim-fire','put-away'][i];extra.append(crop);extra_names.append(name);tor.append(meta)
        torch_metadata[group]=tor
        anchor_tables.append('static const short '+group+'_torch_anchor[][2]={'+','.join('{%d,%d}'%tuple(m['anchor']) for m in tor)+'};\n')
        if group=='buck':
            crop,meta=crop_actor(lower,'LEGS.TGA');extra.append(crop);extra_names.append('LEGS')
            bat_metadata['legs']=meta
            anchor_tables.append('static const short bat_legs_anchor[2]={%d,%d};\n'%tuple(meta['anchor']))
            air=[]
            for j in range(3):
                crop,meta=crop_actor(draw_air_legs(j),f'AL{j}.TGA')
                extra.append(crop);extra_names.append(f'AL{j}');air.append(meta)
            bat_metadata['air_legs']=air
            anchor_tables.append('static const short air_legs_anchor[][2]={'+','.join('{%d,%d}'%tuple(m['anchor']) for m in air)+'};\n')
            anchor_tables.append('static const short air_lower_for_frame[]={0,0,1,1,2,2,0};\n')
    export_indexed(cropped+extra,[f'{prefix}{i:02}' for i in range(len(images))]+extra_names,group)
    idle_box=ImageChops.difference(images[0],Image.new('RGB',images[0].size,KEY)).getbbox()
    (ROOT/f'assets/{group}-frames.json').write_text(json.dumps(dict(native_scale=1,standing_height=idle_box[3]-idle_box[1],damage_frame=9 if group=='enemy' else 8,defeat_frame=11 if group=='enemy' else 13,frames=metadata),indent=2)+'\n')
    anchor_tables.append('static const short '+group+'_anchor[][2]={'+','.join('{%d,%d}'%tuple(m['anchor']) for m in metadata)+'};\n')
    # Decode actual exported textures and place them by their exported anchor.
    sheet=Image.new('RGB',(640,384),(23,29,43));q=ImageDraw.Draw(sheet)
    for i,meta in enumerate(metadata):
        im=Image.open(OUT/meta['name']).convert('RGB');ax,ay=meta['anchor']
        x=(i%5)*128+64-ax;y=(i//5)*128+104-ay
        mask=Image.new('L',im.size);mask.putdata([0 if c==KEY else 255 for c in im.getdata()])
        if group in ('buck','chuck'):
            lm=normal_lowers[meta['lower_id']];li=Image.open(OUT/lm['name']).convert('RGB')
            mk=Image.new('L',li.size);mk.putdata([0 if c==KEY else 255 for c in li.getdata()])
            sheet.paste(li,((i%5)*128+64-lm['anchor'][0],(i//5)*128+104-lm['anchor'][1]),mk)
        sheet.paste(im,(x,y),mask)
        q.line(((i%5)*128+7,(i//5)*128+104,(i%5+1)*128-8,(i//5)*128+104),fill=(58,72,86))
        q.text(((i%5)*128+5,(i//5)*128+108),f'{i:02} '+meta['pose'],fill=(215,219,224))
    sheet.save(PRE/f'{group}-frames-native.png')
    sheet.resize((1280,768),Image.Resampling.NEAREST).save(PRE/f'{group}-frames.png')
    return sheet,metadata
frames=[draw_buck(i) for i in range(15)]
sheet,buck_meta=export_actor('BU','buck',frames,FRAME_NAMES)
chuck_frames=[draw_buck(i,chuck=True) for i in range(15)]
cs,chuck_meta=export_actor('CH','chuck',chuck_frames,FRAME_NAMES)
enemy_frames=[draw_enemy(i) for i in range(12)]
es,enemy_meta=export_actor('EN','enemy',enemy_frames,ENEMY_NAMES)
# Ground and dedicated air silhouettes are assembled from actual exports.
# The upper arc is shared, while compact bent-leg chains shift through air poses.
bats=Image.new('RGB',(7*192,8*128),(23,29,43));bq=ImageDraw.Draw(bats)
rows=[('buck',False,False),('chuck',False,False),('buck',False,True),('chuck',False,True),
      ('buck',True,False),('chuck',True,False),('buck',True,True),('chuck',True,True)]
for group in ('buck','chuck'):bat_metadata['air_'+group]=[]
for row,(group,flip,airborne) in enumerate(rows):
    for i,meta in enumerate(bat_metadata[group]):
        full=Image.new('RGB',(192,96),KEY)
        lower=bat_metadata['air_legs'][bat_metadata['air_lower_for_frame'][i]] if airborne else bat_metadata['legs']
        for part in [lower,meta]:
            im=Image.open(OUT/part['name']).convert('RGB');ax,ay=part['anchor']
            mask=Image.new('L',im.size);mask.putdata([0 if c==KEY else 255 for c in im.getdata()])
            full.paste(im,(96-ax,92-ay),mask)
        if airborne:
            if not flip:bat_metadata['air_'+group].append(dict(pose=BAT_NAMES[i],upper=meta['name'],lower=lower['name'],source_rgb_sha256=hashlib.sha256(full.tobytes()).hexdigest()))
        else:assert hashlib.sha256(full.tobytes()).hexdigest()==meta['source_rgb_sha256']
        if flip:full=full.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        mask=Image.new('L',full.size);mask.putdata([0 if c==KEY else 255 for c in full.getdata()])
        bats.paste(full,(i*192,row*128+5),mask)
        bq.line((i*192+5,row*128+97,(i+1)*192-6,row*128+97),fill=(58,72,86))
        bq.text((i*192+5,row*128+108),f'{i} '+group+(' AIR ' if airborne else ' GND ')+BAT_NAMES[i]+(' L' if flip else ' R'),fill=(215,219,224))
bats.resize((2688,2048),Image.Resampling.NEAREST).save(PRE/'bat-contact-sheet.png')
(ROOT/'assets/normal-lowers.json').write_text(json.dumps(normal_lowers,indent=2)+'\n')
anchor_tables.append('#define MF_NORMAL_LOWERS '+str(len(normal_lowers))+'\n')
from torch_art import flame,ember,cue
fire_pairs=[crop_actor(flame(i),f'FL{i}.TGA') for i in range(4)]
torch_metadata['flames']=[m for im,m in fire_pairs]
anchor_tables.append('static const short flame_anchor[][2]={'+','.join('{%d,%d}'%tuple(m['anchor']) for im,m in fire_pairs)+'};\n')
fire_images=[im for im,m in fire_pairs]+[ember(i) for i in range(2)]+[cue()]
fire_names=[f'FL{i}' for i in range(4)]+['EM0','EM1','CHARGE']
export_indexed(fire_images,fire_names,'fire')
torch_metadata['legs']=normal_lowers[normal_lower_for['buck'][0]];torch_metadata['nozzle']=[34,52];torch_metadata['floor']=[74,92]
(ROOT/'assets/torch-frames.json').write_text(json.dumps(torch_metadata,indent=2)+'\n')
# Actual export contact sheet: both costumes/directions and flame cycle.
ts=Image.new('RGB',(768,512),(23,29,43));td=ImageDraw.Draw(ts)
for row,(group,flip) in enumerate([('buck',False),('chuck',False),('buck',True),('chuck',True)]):
    for i,meta in enumerate(torch_metadata[group]):
        full=Image.new('RGB',(192,104),KEY)
        for part in [torch_metadata['legs'],meta]:
            im=Image.open(OUT/part['name']).convert('RGB');ax,ay=part['anchor']
            mk=Image.new('L',im.size);mk.putdata([0 if c==KEY else 255 for c in im.getdata()]);full.paste(im,(96-ax,92-ay),mk)
        assert hashlib.sha256(full.crop((40,0,152,96)).tobytes()).hexdigest()==meta['source_rgb_sha256']
        if i==1:
            im=Image.open(OUT/f'FL{row%4}.TGA').convert('RGB');mk=Image.new('L',im.size);mk.putdata([0 if c==KEY else 255 for c in im.getdata()]);fm=torch_metadata['flames'][row%4];full.paste(im,(96-fm['anchor'][0],92-fm['anchor'][1]),mk)
        if flip:full=full.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        mk=Image.new('L',full.size);mk.putdata([0 if c==KEY else 255 for c in full.getdata()]);ts.paste(full,(i*192,row*128),mk)
        td.text((i*192+4,row*128+108),group+' '+meta['pose']+(' L' if flip else ' R'),fill=(220,220,220))
    im=Image.open(OUT/f'FL{row}.TGA').convert('RGB');mk=Image.new('L',im.size);mk.putdata([0 if c==KEY else 255 for c in im.getdata()]);fm=torch_metadata['flames'][row];ts.paste(im,(576+96-fm['anchor'][0],row*128+92-fm['anchor'][1]),mk)
    td.text((580,row*128+108),f'flame {row}',fill=(220,220,220))
ts.resize((1536,1024),Image.Resampling.NEAREST).save(PRE/'torch-contact-sheet.png')
(ROOT/'assets/bat-frames.json').write_text(json.dumps(bat_metadata,indent=2)+'\n')
(ROOT/'src/art_data.h').write_text('/* Generated by tools/draw-assets.py; cropped native-resolution anchors. */\n#ifndef MF_ART_DATA_H\n#define MF_ART_DATA_H\n'+''.join(anchor_tables)+'#endif\n')
combined=Image.new('RGB',(640,1152));combined.paste(sheet,(0,0));combined.paste(cs,(0,384));combined.paste(es,(0,768))
combined.resize((1280,2304),Image.Resampling.NEAREST).save(PRE/'fighters-contact-sheet.png')
O='#111625'
for state in range(3):
    im=Image.new('RGB',(32,48),KEY); q=ImageDraw.Draw(im)
    q.rectangle((4,9,27,42),fill='#1d3449',outline=O)
    for xx,c in [(5,'#35647b'),(8,'#438094'),(11,'#37677d'),(20,'#142c43'),(24,'#0f2238')]: q.line((xx,12,xx,41),fill=c,width=2)
    q.ellipse((4,4,27,14),fill='#4c7785',outline='#102338'); q.ellipse((7,6,24,11),fill='#263f54',outline='#6e9a9b')
    for yy in [15,36]:
        q.rectangle((3,yy,28,yy+2),fill='#9ba3a2'); q.line((5,yy+3,26,yy+3),fill=O)
    q.rectangle((9,20,23,31),fill='#c09c54',outline=O); text(q,(11,22),'MF','#3a3040')
    q.ellipse((4,39,27,46),fill='#213e55',outline=O); q.line((6,44,25,44),fill='#588190')
    if state:
        q.line((18,14,14,20,20,25,16,33),fill='#111625',width=2)
    if state==2:
        q.line((8,17,12,23,8,33,14,40),fill='#111625',width=2)
        q.line((19,33,23,38,21,41),fill='#d0b274')
    export(im,f'DR{state}')
im=Image.new('RGB',(48,12),KEY); sd=ImageDraw.Draw(im)
sd.ellipse((0,1,47,11),fill='#202838')
for sy in range(12):
    for sx in range(48):
        if im.getpixel((sx,sy))!=KEY and (sx+sy)%2: im.putpixel((sx,sy),KEY)
sd.ellipse((6,3,41,9),fill='#101828');export(im,'SHADOW')
im=Image.new('RGB',(32,32),KEY); q=ImageDraw.Draw(im)
q.polygon([(15,0),(19,11),(29,5),(23,15),(31,19),(21,22),(23,31),(15,25),(8,31),(10,21),(0,18),(11,13),(6,4)],fill='#ffad64')
q.polygon([(16,6),(18,14),(25,16),(19,19),(15,26),(13,19),(6,16),(13,14)],fill='#fff0bd'); export(im,'HIT')
# PCM8, deterministic, no external recordings; small effects only.
for name,duration,kind in [('PUNCH',.10,0),('JUMP',.13,1),('IMPACT',.16,2)]:
    samples=[]
    for i in range(int(11025*duration)):
        t=i/11025; env=(1-t/duration)**2
        if kind==0: v=rng.uniform(-1,1)*.6+math.sin(2*math.pi*140*t)*.3
        elif kind==1: v=math.sin(2*math.pi*(230*t+1500*t*t))*.65
        else: v=rng.uniform(-1,1)*.6+math.sin(2*math.pi*65*t)*.5
        samples.append(int(max(-127,min(127,v*env*85)))&255)
    (OUT/(name+'.PCM')).write_bytes(bytes(samples))
# Art composite of the exported assets, not an emulator screenshot.
scene=street.crop((280,0,600,240)); q=ImageDraw.Draw(scene)
def paste_key(im,x,y):
    im=im.convert('RGB');mask=Image.new('L',im.size);mask.putdata([0 if c==KEY else 255 for c in im.getdata()]);scene.paste(im,(x,y),mask)
for x,y in [(100,202),(180,206),(245,196),(285,218)]:paste_key(Image.open(OUT/'SHADOW.TGA'),x-24,y-6)
for prefix,index,x,y,meta in [('EN',0,245,196,enemy_meta),('BU',0,100,202,buck_meta),('CH',0,180,206,chuck_meta)]:
    ax,ay=meta[index]['anchor']
    if prefix!='EN':
        lm=normal_lowers[meta[index]['lower_id']];paste_key(Image.open(OUT/lm['name']),x-lm['anchor'][0],y-lm['anchor'][1])
    paste_key(Image.open(OUT/f'{prefix}{index:02}.TGA'),x-ax,y-ay)
paste_key(Image.open(OUT/'DR0.TGA'),285-16,218-46)
text(q,(12,10),'BUCK',(235,227,210));q.rectangle((12,21,91,24),fill=(99,215,186))
text(q,(200,10),'CHUCK',(235,227,210));q.rectangle((200,21,279,24),fill=(99,215,186))
scene.resize((960,720),Image.Resampling.NEAREST).save(PRE/'scene-art.png')
total=sum(x['vram'] for x in manifest)
assert total+21760<0x7fef8-0x10000, total
(ROOT/'assets/manifest.json').write_text(json.dumps({'texture_bytes':total,'runtime_hud_bytes':21760,'total_texture_bytes':total+21760,'texture_budget':458488,'assets':manifest},indent=2)+'\n')
print('Wrote',len(manifest),'textures;',total+21760,'including HUD, of 458488 available VDP1 texture bytes')
