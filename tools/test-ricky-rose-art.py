#!/usr/bin/env python3
"""Validate source localization and exact native preservation around the rose edit."""
from pathlib import Path
from PIL import Image
import hashlib,json,struct
R=Path(__file__).resolve().parents[1]
p=json.loads((R/'art/ricky/provenance.json').read_text())
for file,sha in [('source','source_sha256'),('original_source','original_source_sha256'),('edit_mask','edit_mask_sha256')]:
 assert hashlib.sha256((R/p[file]).read_bytes()).hexdigest()==p[sha],file
assert p['original_source_sha256']=='7928d4f38fcd4a76fae9053d1ab466b10af6d8c2e966b1ecacaf903c5e62627b'
source=Image.open(R/p['source']).convert('RGB');original=Image.open(R/p['original_source']).convert('RGB');mask=Image.open(R/p['edit_mask']).convert('L')
assert source.size==original.size==mask.size==(1536,1024)
original_bytes=original.tobytes();source_bytes=source.tobytes()
assert all(edited or source_bytes[i*3:i*3+3]==original_bytes[i*3:i*3+3] for i,edited in enumerate(mask.tobytes())),'source change outside reviewed shoulders/arms'
old=json.loads((R/'art/ricky/manifest.original.json').read_text());new=json.loads((R/'assets/ricky/manifest.json').read_text())
assert new['source_sha256']==p['source_sha256']
assert new['definitions']==old['definitions']==25 and new['texture_bytes']==old['texture_bytes']==114048
assert new['reserve']==old['reserve']==49152
assert hashlib.sha256((R/'art/ricky/manifest.original.json').read_bytes()).hexdigest()==p['original_manifest_sha256']
for name,sha in p['original_runtime_sha256'].items():assert hashlib.sha256((R/'art/ricky/runtime-original'/name).read_bytes()).hexdigest()==sha
regions=json.loads((R/'art/ricky/rose-regions.json').read_text());assert len(regions)==25
palettes=set();report=[]
def decode(b):
 rgb=[tuple(b[i:i+3][::-1]) for i in range(18,786,3)]
 words=[0x8000|(r>>3)|((g>>3)<<5)|((blue>>3)<<10) for r,g,blue in rgb]
 return [words[v] for v in b[786:]],b[786:],rgb
for i,(a,f) in enumerate(zip(old['frames'],new['frames'])):
 for k in ('name','source_box','scale','root','width','height','anchor','bytes','resource'):assert a[k]==f[k],(f['name'],k)
 before=(R/f'art/ricky/runtime-original/RK{i:02}.TGA').read_bytes();after=(R/f'assets/ricky/RK{i:02}.TGA').read_bytes()
 palettes.add(after[18:786]);ac,ar,_=decode(before);bc,br,rgb=decode(after)
 assert before[:18]==after[:18],f['name']
 assert all(bool(a)==bool(b) for a,b in zip(ar,br)),'alpha/silhouette changed: '+f['name']
 x0,y0,x1,y1=f['source_box'];scale=f['scale'];w=round((x1-x0)*scale);h=round((y1-y0)*scale)
 left=round((f['root'][0]-x0)*scale)-f['anchor'][0];top=round((f['root'][1]-y0)*scale)-f['anchor'][1]
 region=list(mask.crop((x0,y0,x1,y1)).resize((w,h),Image.Resampling.NEAREST).crop((left,top,left+f['width'],top+f['height'])).tobytes())
 differences=[a!=b and bool(alpha) for a,b,alpha in zip(ac,bc,ar)]
 assert all(not changed or edited for changed,edited in zip(differences,region)),'native color drift outside arm: '+f['name']
 assert any(differences),f['name']+' has no arm edit'
 colors=[rgb[index] for index,edited in zip(br,region) if index and edited]
 green=sum(g>r and g>blue for r,g,blue in colors)
 red=sum(r>g*1.5 and r>blue*1.3 for r,g,blue in colors)
 assert green and red,'missing native rose red/leaf green: '+f['name']
 report.append(dict(pose=f['name'],changed_rgb555_pixels=sum(differences),green_pixels=green,red_pixels=red))
assert len(palettes)==1,'shared palette differs across frames'
assert next(iter(palettes))==(R/'assets/ricky/palette.bgr24').read_bytes()
print('PASS rose art: 25 localized edits; source/anchors/alpha/chain/clothing outside arms exact; red and green retained in every native pose; 25 definitions/114048 bytes, reserve 49152')
print(json.dumps(report))
