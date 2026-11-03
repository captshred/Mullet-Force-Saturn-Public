"""Exact historical PNG/TGA restoration, mirrored roots and compact budget."""
from pathlib import Path
import json,hashlib,struct

def validate_original_three(root,files=None):
    base=root/'assets/original-three-walk';m=json.loads((base/'manifest.json').read_text())
    enabled=files is None or (root/'build/original-three-mode.txt').read_text().strip()=='1'
    if not enabled:return None
    from PIL import Image
    study=json.loads((root/'assets/animation-study/manifest.json').read_text());polish=json.loads((root/'assets/animation-polish/manifest.json').read_text());required=set()
    for a,actor in enumerate(m['actors']):
        for f in actor['frames']:
            raw=(base/f'{actor["name"]}-{f["frame"]:02d}.png').read_bytes();assert raw==(root/f['source_path']).read_bytes() and hashlib.sha256(raw).hexdigest()==f['png_sha256']
            im=Image.open(base/f'{actor["name"]}-{f["frame"]:02d}.png').convert('RGBA');assert im.size==(128,96) and im.getbbox()[1]==4 and im.getbbox()[3]==92
            assert hashlib.sha256(im.tobytes()).hexdigest()==f['rgba_sha256']==study['actors'][a]['frames'][f['source_frame']]['rgba_sha256']
            for direction in [1,-1]:
                actual={}
                for p in f['parts']:
                    required.add(p['resource']);blob=(root/'assets/animation-study'/p['name']).read_bytes();assert hashlib.sha256(blob).hexdigest()==p['tga_sha256']
                    if files is not None:
                        replacement=root/'assets/knee-lift/overrides'/p['name']
                        knee=(root/'build/knee-lift-mode.txt').read_text().strip()=='1'
                        assert files[p['name']]==(replacement.read_bytes() if knee and replacement.exists() else blob)
                    w,h=struct.unpack_from('<HH',blob,12);assert (w,h)==(p['width'],p['height'])
                    left=p['x']-64 if direction>0 else 64-p['x']-w
                    for y in range(h):
                        for x in range(w):
                            v=blob[786+(h-y-1)*w+x]
                            if v:
                                key=(left+(x if direction>0 else w-1-x),p['y']+y-92);assert key not in actual
                                actual[key]=(*blob[18+3*v:21+3*v][::-1],255)
                expected={(x-64 if direction>0 else 63-x,y-92):im.getpixel((x,y)) for y in range(96) for x in range(128) if im.getpixel((x,y))[3]}
                assert actual==expected and max(y for x,y in actual)==-1
    for actor in polish['actors']:
        for f in actor['frames'][:4]:required.update(p['resource'] for p in f['parts'])
    assert sorted(required)==m['boot_required']
    total=302336+sum(polish['resources'][r]['aligned_bytes'] for r in required-{0,1,2,21,22,23})
    assert total==m['boot_vdp1_bytes']==351104 and m['boot_free_bytes']==458488-total and m['new_texture_bytes']==0
    assert m['boot_sprite_slots']==95+len(required)==125 and m['full_vdp1_bytes']==427104
    print(f'PASS original three: byte-identical historical PNG/TGA, both mirrored native88px assemblies; boot {total}/458488 free {458488-total}, zero new texture data.')
    return m
if __name__=='__main__':validate_original_three(Path(__file__).resolve().parents[1])
