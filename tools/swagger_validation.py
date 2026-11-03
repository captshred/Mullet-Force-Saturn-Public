"""Independent swagger source/texture reconstruction, reuse, and bank budgets."""
from pathlib import Path
import json,hashlib,struct

def validate_swagger(root,files=None):
    base=root/'assets/swagger-walk';m=json.loads((base/'manifest.json').read_text());old=json.loads((root/'assets/animation-polish/manifest.json').read_text())
    enabled=files is None or (root/'build/swagger-mode.txt').read_text().strip()=='1'
    if not enabled:
        assert not set(m['tga_sha256']).intersection(files);return None
    from PIL import Image
    palette=(root/'assets/gallery/GB0.TGA').read_bytes()[18:786]
    assert hashlib.sha256(palette).hexdigest()==m['palette_sha256']
    assert hashlib.sha256((base/'source/leg-edit-guide.png').read_bytes()).hexdigest()==m['guide_sha256']
    assert m['resources'][:m['old_resource_count']]==old['resources']
    payloads=[];keys=set();required=set();extra=0
    for i,p in enumerate(m['resources']):
        if i<42:
            a,f,part=p['old_ref'];path=root/('assets/gallery' if f==0 else 'assets/animation-study')/p['name']
        elif i<m['old_resource_count']:path=root/'assets/animation-polish'/p['name']
        else:path=base/p['name']
        data=path.read_bytes();w,h=struct.unpack_from('<HH',data,12);assert w%8==0 and h%2==0 and (w,h)==(p['width'],p['height'])
        assert data[18:786]==palette and len(data)==786+w*h and max(data[786:])<=253
        key=(w,h,data[786:]);assert key not in keys;keys.add(key);payloads.append(data)
        if i>=m['old_resource_count']:
            extra+=p['aligned_bytes'];assert hashlib.sha256(data).hexdigest()==m['tga_sha256'][p['name']]
            if files is not None:assert files[p['name']]==data
    for a,actor in enumerate(m['actors']):
        name=actor['name'];unique=set()
        for f in actor['frames']:
            im=Image.open(base/f'{name}-{f["frame"]:02d}.png').convert('RGBA');assert im.size==(128,96) and tuple(f['bounds'])==im.getbbox() and im.getbbox()[1]==4 and im.getbbox()[3]==92
            src=Image.open(root/f'assets/animation-polish/{name}-{f["upper_source_frame"]:02d}.png').convert('RGBA')
            assert im.crop((0,0,128,52)).tobytes()==src.crop((0,0,128,52)).tobytes()
            unique.add(im.tobytes());assert hashlib.sha256(im.tobytes()).hexdigest()==f['rgba_sha256']
            for direction in [1,-1]:
                out={}
                for p in f['parts']:
                    required.add(p['resource']);data=payloads[p['resource']];w,h=p['width'],p['height'];left=p['x']-64 if direction>0 else 64-p['x']-w
                    for y in range(h):
                        for x in range(w):
                            v=data[786+(h-y-1)*w+x]
                            if v:
                                key=(left+(x if direction>0 else w-1-x),p['y']+y-92);assert key not in out;out[key]=(*palette[v*3:v*3+3][::-1],255)
                expected={(x-64 if direction>0 else 63-x,y-92):im.getpixel((x,y)) for y in range(96) for x in range(128) if im.getpixel((x,y))[3]}
                assert out==expected and max(y for x,y in out)==-1
        assert len(unique)==3
        gif=Image.open(base/f'{name}-swagger.gif');assert gif.n_frames==3
        for f in range(3):
            gif.seek(f);actual=gif.convert('RGBA');expected=Image.open(base/f'{name}-{f:02d}.png').convert('RGBA').resize((384,288),Image.Resampling.NEAREST)
            assert actual.getchannel('A').tobytes()==expected.getchannel('A').tobytes()
            assert all(x[:3]==y[:3] for x,y in zip(actual.getdata(),expected.getdata()) if y[3])
        for f in old['actors'][a]['frames'][:4]:required.update(p['resource'] for p in f['parts'])
    assert sorted(required)==m['boot_required']
    gallery={0,1,2,21,22,23};boot=302336+sum(m['resources'][r]['aligned_bytes'] for r in required-gallery)
    full=427104+extra
    assert boot==m['boot_vdp1_bytes'] and full==m['expanded_vdp1_bytes']<=458488
    assert extra==m['new_texture_bytes'] and 458488-boot==m['boot_free_bytes'] and 458488-full==m['expanded_free_bytes']
    assert m['boot_sprite_count']==101+len(required-gallery) and m['expanded_sprite_count']==95+len(m['resources'])<255
    print(f'PASS swagger: 3 unique poses/fighter, unchanged upper pixels, palette/transparency, mirrored piece seams/roots, exact dedup; boot {boot}/458488 free {458488-boot}; expanded {full}/458488 free {458488-full}.')
    return m
if __name__=='__main__':validate_swagger(Path(__file__).resolve().parents[1])
