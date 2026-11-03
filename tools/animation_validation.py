"""Independent native candidate reconstruction, transparency, palette and budget checks."""
import hashlib,json,struct
from pathlib import Path

def validate_animation(root,files=None):
    m=json.loads((root/'assets/animation-study/manifest.json').read_text())
    if files is not None:
        enabled=(root/'build/animation-mode.txt').read_text().strip()=='1'
        run=(root/'build/run-bat-mode.txt').exists() and (root/'build/run-bat-mode.txt').read_text().strip()=='1'
        assert ((b'RUN / APPROVED WALK REVIEW' if run else b'ANIMATION POLISH REVIEW') in files['0.BIN'])==enabled
        if not enabled:
            assert not set(m['tga_sha256']).intersection(files)
            print('PASS: animation study disabled; no candidate textures or entry point in disc.')
            return 0
    from PIL import Image
    assert m['canvas']==[128,96] and m['root']==[64,92] and m['standing_height']==88
    assert m['walk_ticks']==5 and m['extra_palette_bytes']==0
    base=root/'assets/animation-study';pal=(root/'assets/gallery/GB0.TGA').read_bytes()[18:786]
    assert hashlib.sha256(pal).hexdigest()==m['palette_sha256']
    assert hashlib.sha256((base/'source-walk.png').read_bytes()).hexdigest()==m['source_sha256']
    total=0
    for actor in m['actors']:
        for f in actor['frames']:
            data=[None]*(128*96)
            for p in f['parts']:
                fn=p['name'];blob=(root/'assets/gallery'/fn if f['frame']==0 else base/fn).read_bytes()
                w,h=struct.unpack_from('<HH',blob,12)
                assert (w,h)==(p['width'],p['height']) and w%8==0
                assert blob[18:786]==pal and len(blob)==786+w*h
                assert max(blob[786:])<=253
                if f['frame']:
                    assert hashlib.sha256(blob).hexdigest()==m['tga_sha256'][fn]
                    if files is not None:
                        replacement=root/'assets/knee-lift/overrides'/fn
                        knee=(root/'build/knee-lift-mode.txt').read_text().strip()=='1'
                        assert files[fn]==(replacement.read_bytes() if knee and replacement.exists() else blob)
                    total+=(w*h+31)&~31
                for y in range(h):
                    for x in range(w):
                        i=blob[786+(h-1-y)*w+x]
                        if not i:continue
                        xx,yy=p['x']+x,p['y']+y
                        assert 0<=xx<128 and 0<=yy<96
                        at=yy*128+xx;assert data[at] is None
                        data[at]=(*pal[i*3:i*3+3][::-1],255)
            ref=Image.open(base/f"{actor['name'].lower()}-{f['frame']:02d}.png").convert('RGBA')
            assert ref.size==(128,96) and ref.getbbox()==tuple(f['opaque_bounds'])
            assert ref.getbbox()[1]==4 and ref.getbbox()[3]==92
            expected=[tuple(c) if c[3] else None for c in ref.getdata()]
            assert expected==data,'Split seam, palette or alpha mismatch'
            assert hashlib.sha256(ref.tobytes()).hexdigest()==f['rgba_sha256']
            for facing in [1,-1]:
                actual={}
                for p in f['parts']:
                    left=-64+p['x'] if facing>0 else 64-p['x']-p['width']
                    for y in range(p['height']):
                        for x in range(p['width']):
                            xx=p['x']+x;yy=p['y']+y
                            if xx>=128:continue
                            c=data[yy*128+xx]
                            if c is not None:
                                key=(left+(x if facing>0 else p['width']-1-x),yy-92)
                                assert key not in actual;actual[key]=c
                exp={(x-64 if facing>0 else 63-x,y-92):c for y in range(96) for x in range(128) if (c:=data[y*128+x]) is not None}
                assert actual==exp and max(y for x,y in actual)==-1
            if f['frame']==0:
                idle=Image.open(root/f"assets/gallery/{actor['name'].lower()}-88.png").convert('RGBA');canvas=Image.new('RGBA',(128,96));canvas.alpha_composite(idle,(64-idle.width//2,4));assert canvas.tobytes()==ref.tobytes()
    for actor in m['actors']:
        gif=Image.open(base/(actor['name'].lower()+'-walk.gif'))
        assert gif.n_frames==6
        for frame in range(6):
            gif.seek(frame);actual=gif.convert('RGBA')
            ref=Image.open(base/f"{actor['name'].lower()}-{frame+1:02d}.png").convert('RGBA').resize((384,288),Image.Resampling.NEAREST)
            assert actual.getchannel('A').tobytes()==ref.getchannel('A').tobytes()
            assert all(a[:3]==b[:3] for a,b in zip(actual.getdata(),ref.getdata()) if b[3])
    assert total==m['new_texture_bytes']==53472
    assert 302336+total==355808<458488
    print('PASS: 14 native canvases, 36 new textures, exact approved idle reuse, both facings/foot roots/three-piece seams/alpha/palette; VDP1 355808/458488, no additional CRAM.')
    return total
if __name__=='__main__':validate_animation(Path(__file__).resolve().parents[1])
