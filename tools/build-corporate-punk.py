#!/usr/bin/env python3
"""Offline one-pose authoring/export. Never invoked by game builds.
Uses the isolated large illustration, pixel-cluster reconstruction, and a
registered local face cleanup. No low-resolution sheet sprites are art sources.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from functools import lru_cache
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];O=R/'assets/corporate-punk';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def binary(im,t=192):
    im=im.convert('RGBA');im.putdata([(*p[:3],255) if p[3]>=t else (0,0,0,0) for p in im.getdata()]);return im
# Native reconstruction guide already has deliberate clusters; nearest sampling
# avoids introducing a second soft resampling pass.
source=binary(Image.open(O/'source/native-cleanup-edit.png'));source=source.crop(source.getchannel('A').getbbox());w=round(source.width*84/source.height)
master=Image.new('RGBA',(96,96));master.alpha_composite(source.resize((w,84),Image.Resampling.NEAREST),(48-w//2,8))
face=Image.open(O/'source/face-cleanup-edit.png').convert('RGBA').resize((24,26),Image.Resampling.NEAREST)
# Register the local edited face to the existing brow/jaw. Skin-only import
# preserves the original narrow head contour, mohawk, costume and body pixels.
for y in range(17,30):
    for x in range(53,66):
        r,g,b,a=master.getpixel((x,y));sx,sy=x-48+1,y-8+2
        if a and r>70 and r>g*1.15 and r>b*1.3 and 0<=sx<24 and 0<=sy<26:
            p=face.getpixel((sx,sy))
            if p[3]>=192:master.putpixel((x,y),(*p[:3],255))
master.save(O/'source/native-cleaned-reference.png')
# Quantize without dithering, then snap the shade ramps to actual RGB555 words.
opaque=[p[:3] for p in master.getdata() if p[3]];swatch=Image.new('RGB',(len(opaque),1));swatch.putdata(opaque);q=swatch.quantize(colors=63,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
qpal=q.getpalette();qcolors=[tuple(qpal[i*3:i*3+3]) for i in sorted(set(q.getdata()))]
def word(c):
    r,g,b=[min(31,(v*31+127)//255) for v in c];return r|(g<<5)|(b<<10)
def rgb(v):return tuple(((v>>s)&31)*255//31 for s in [0,5,10])
words=sorted(set(map(word,qcolors)));newcolors=[rgb(v) for v in words]
legacy=(R/'assets/cd/EN00.TGA').read_bytes();palette=bytearray(legacy[18:786]);oldcolors=[tuple(palette[i*3:i*3+3][::-1]) for i in range(256)]
legacy_used=set()
for path in (R/'assets/cd').glob('EN*.TGA'):legacy_used.update(path.read_bytes()[786:])
# Preserve every old enemy slot. Compare hardware words to avoid duplicate
# allocated shades with different 8-bit representations of the same RGB555.
def source_word(c):return (c[0]>>3)|((c[1]>>3)<<5)|((c[2]>>3)<<10)
lookup={source_word(oldcolors[i]):i for i in sorted(legacy_used) if i}
free=iter(i for i in range(1,254) if i not in legacy_used);extension=[]
for v,c in zip(words,newcolors):
    if v not in lookup:
        i=next(free);lookup[v]=i;palette[i*3:i*3+3]=bytes(c[::-1]);extension.append({'raw_index':i,'rgb':list(c),'rgb555':0x8000|v})
colors=[tuple(palette[i*3:i*3+3][::-1]) for i in range(256)];memo={}
def nearest(c):
    if c not in memo:memo[c]=lookup[words[min(range(len(words)),key=lambda j:sum((c[k]-newcolors[j][k])**2 for k in range(3)))]]
    return memo[c]
pixels=[nearest(p[:3]) if p[3] else 0 for p in master.getdata()];indexed=Image.new('P',(96,96));indexed.putpalette([v for c in colors for v in c]);indexed.putdata(pixels);indexed.info['transparency']=0
indexed.save(O/'corporate-punk-84.png',transparency=0);rgba=indexed.convert('RGBA');rgba.save(O/'corporate-punk-84-rgba.png');rgba.resize((768,768),Image.Resampling.NEAREST).save(O/'corporate-punk-84-8x.png')
bbox=rgba.getbbox();assert bbox[1]==8 and bbox[3]==92 and bbox[3]-bbox[1]==84
rgba.crop(bbox).save(O/'corporate-punk-tight.png')
def band(top,bottom):
    box=rgba.crop((0,top,96,bottom)).getbbox()
    if not box:return None
    x,y,x2,y2=box;y+=top;y2+=top;ww=((x2-x+7)//8)*8;hh=y2-y
    if hh%2:return None
    return {'x':x,'y':y,'width':ww,'height':hh,'payload_bytes':ww*hh,'aligned_bytes':(ww*hh+31)&~31}
@lru_cache(None)
def solve(top,count):
    if count==1:
        p=band(top,92);return (p['aligned_bytes'],[p]) if p else (10**9,[])
    choices=[]
    for cut in range(top+8,92-8*(count-1)+1,2):
        p=band(top,cut)
        if p:
            cost,rest=solve(cut,count-1)
            if rest:choices.append((p['aligned_bytes']+cost,[p]+rest))
    return min(choices,key=lambda c:c[0]) if choices else (10**9,[])
variants=[{'pieces':n,'texture_bytes':solve(8,n)[0],'layout':solve(8,n)[1]} for n in range(1,5)]
minimum=min(v['texture_bytes'] for v in variants);chosen=next(v for v in variants if v['texture_bytes']*100<=minimum*105)
def tga(name,p):
    header=bytearray(18);header[1]=header[2]=1;struct.pack_into('<H',header,5,256);header[7]=24;struct.pack_into('<HH',header,12,p['width'],p['height']);header[16]=8
    payload=bytes(pixels[y*96+x] if x<96 else 0 for y in range(p['y']+p['height']-1,p['y']-1,-1) for x in range(p['x'],p['x']+p['width']))
    (O/name).write_bytes(bytes(header)+bytes(palette)+payload);return p|{'name':name,'sha256':sha(O/name),'anchor':[48-p['x'],92-p['y']]}
for old in O.glob('CP*.TGA'):old.unlink()
whole=tga('CPWHOLE.TGA',variants[0]['layout'][0]);parts=[tga(f'CP{i}.TGA',p) for i,p in enumerate(chosen['layout'])]
(O/'palette.bgr24').write_bytes(palette);(O/'palette-delta.json').write_text(json.dumps({'legacy_used_raw_indices':sorted(legacy_used),'new_entries':extension,'note':'Art-only. No game palette changed. Future Jo loader reuses existing enemy palette handle; raw0 is transparency key1 after loader +1.'},indent=2)+'\n')
# Exact existing approved player images, at native size and a shared sole line.
players=[Image.open(R/f'assets/animation-polish/{n}-00.png').convert('RGBA') for n in ['buck','chuck']]
lineup=Image.new('RGBA',(384,112),(27,31,43,255));draw=ImageDraw.Draw(lineup)
for im,x in [(players[0],0),(players[1],128),(rgba,272)]:lineup.alpha_composite(im,(x,0))
draw.line((0,92,383,92),fill=(91,120,110));
for x,label in [(2,'BUCK 88px'),(130,'CHUCK 88px'),(258,'CORP PUNK 84px')]:draw.text((x,99),label,fill=(240,240,245))
lineup.save(O/'lineup-native.png');lineup.resize((2304,672),Image.Resampling.NEAREST).save(O/'lineup-6x.png')
# Legacy illustration decoded from real EN00 raw pixels; no screenshot source.
lw,lh=struct.unpack_from('<HH',legacy,12);oldim=Image.new('RGBA',(lw,lh));oldim.putdata([(*oldcolors[v],255) if v else (0,0,0,0) for y in range(lh) for v in legacy[786+(lh-y-1)*lw:786+(lh-y)*lw]]);oldim.save(O/'legacy-en00.png')
compare=Image.new('RGBA',(256,112),(27,31,43,255));compare.alpha_composite(oldim,(64-20,91-(oldim.getbbox()[3]-1)));compare.alpha_composite(rgba,(128+16,0));d=ImageDraw.Draw(compare);d.line((0,92,255,92),fill=(91,120,110));d.text((2,99),'LEGACY EN00 90px',fill=(240,240,245));d.text((130,99),'NEW MASTER 84px',fill=(240,240,245));compare.save(O/'legacy-compare-native.png');compare.resize((1536,672),Image.Resampling.NEAREST).save(O/'legacy-compare-6x.png')
used=sorted(set(pixels)-{0});assert len({source_word(colors[i]) for i in used})==len(used) and max(used)<=253
m={'baseline':'c3edb05bb3f65c8cb8c9b3c013f86752dddc6cbc','artwork_only':True,'canvas':[96,96],'root':[48,92],'opaque_bounds':list(bbox),'opaque_width':bbox[2]-bbox[0],'opaque_height':84,'facing':'right','opaque_colors':len(used),'raw_indices_used':used,'palette_entries_file':256,'hardware_palette_bank_bytes':512,'legacy_raw_indices':sorted(legacy_used),'added_palette_entries':extension,'unused_legacy_slots':len(set(range(1,254))-legacy_used),'new_palette_bank_required':False,'active_game_palette_changes':0,'active_vdp1_change':0,'current_playable_allocated':351104,'current_playable_free':107384,'layout_candidates':variants,'chosen_pieces':len(parts),'texture_bytes':chosen['texture_bytes'],'whole_texture':whole,'parts':parts,'selection_rule':'Fewest pieces within5% of minimum1..4 horizontal-band cost; even heights, minimum8px bands,8px width/32byte allocation alignment. Alternatives are not loaded together.','instance_costs':{str(n):{'shared_texture_bytes':chosen['texture_bytes'],'palette_banks':1,'draw_commands':len(parts)*n,'additional_texture_bytes_per_instance':0} for n in [1,2,4,8]},'legacy_opaque_height':oldim.getbbox()[3]-oldim.getbbox()[1],'player_bounds':{n:list(im.getbbox()) for n,im in zip(['buck','chuck'],players)},'player_sha256':{n:sha(R/f'assets/animation-polish/{n}-00.png') for n in ['buck','chuck']},'source_sha256':{p.name:sha(p) for p in sorted((O/'source').glob('*.png'))}}
(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({k:m[k] for k in ['opaque_bounds','opaque_colors','unused_legacy_slots','chosen_pieces','texture_bytes']},indent=2));print('Candidates',[(v['pieces'],v['texture_bytes']) for v in variants]);print('New palette entries',len(extension))
