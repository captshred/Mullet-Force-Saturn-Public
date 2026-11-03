"""Independent pixel reconstruction, face/feet locking, interning and memory checks."""
from pathlib import Path
import hashlib,json,struct

def validate_polish(root,files=None):
    base=root/'assets/animation-polish';m=json.loads((base/'manifest.json').read_text())
    if files is not None:
        enabled=(root/'build/animation-mode.txt').read_text().strip()=='1'
        if not enabled:
            assert not set(m['tga_sha256']).intersection(files);return 0
    assert hashlib.sha256((base/'gait-before/manifest.json').read_bytes()).hexdigest()=='910fb65b00e6de8604e0fd7f650f83f751fad3817520ebea1f992b8fd1f97168'
    baseline=json.loads((base/'gait-before/manifest.json').read_text())
    from PIL import Image
    old=json.loads((root/'assets/animation-study/manifest.json').read_text())
    pal=(root/'assets/gallery/GB0.TGA').read_bytes()[18:786];assert hashlib.sha256(pal).hexdigest()==m['palette_sha256']
    assert hashlib.sha256((base/'boot-edit-guide.png').read_bytes()).hexdigest()==m['guide_sha256']
    assert m['existing_piece_occurrences']==m['existing_unique_pieces']==42 and m['extra_palette_bytes']==0
    for name,digest in m['gait_source_sha256'].items():assert hashlib.sha256((base/'opposite-source'/name).read_bytes()).hexdigest()==digest
    resources=[];keys=set();newbytes=0;naive=0
    for index,p in enumerate(m['resources']):
        if index<42:
            a,f,part=p['old_ref'];q=old['actors'][a]['frames'][f]['parts'][part];assert q['name']==p['name']
            path=root/('assets/gallery' if not f else 'assets/animation-study')/p['name']
        else:path=base/p['name']
        d=path.read_bytes();w,h=struct.unpack_from('<HH',d,12);assert (w,h)==(p['width'],p['height']) and w%8==0 and d[18:786]==pal
        assert len(d)==786+w*h and max(d[786:])<=253
        key=(w,h,d[786:]);assert key not in keys;keys.add(key);resources.append(d)
        if index>=42:
            assert hashlib.sha256(d).hexdigest()==m['tga_sha256'][p['name']]
            if files is not None:assert files[p['name']]==d
            newbytes+=(w*h+31)&~31
    for ai,actor in enumerate(m['actors']):
        name=actor['name'];idle=Image.open(root/f'assets/animation-study/{name}-00.png').convert('RGBA')
        canonical=Image.open(root/f'assets/animation-study/{name}-01.png').convert('RGBA')
        idlekeys=set()
        for f in actor['frames']:
            im=Image.open(base/f'{name}-{f["frame"]:02d}.png').convert('RGBA');assert im.size==(128,96) and im.getbbox()[1]==4 and im.getbbox()[3]==92
            data=[(0,0,0,0)]*(128*96)
            for p in f['parts']:
                d=resources[p['resource']];w,h=struct.unpack_from('<HH',d,12);assert (w,h)==(p['width'],p['height']);naive+=(w*h+31)&~31
                for y in range(h):
                    for x in range(w):
                        v=d[786+(h-y-1)*w+x]
                        if v:
                            xx,yy=p['x']+x,p['y']+y;assert 0<=xx<128 and 0<=yy<96
                            at=yy*128+xx;assert data[at][3]==0;data[at]=(*pal[3*v:3*v+3][::-1],255)
            assert list(im.getdata())==data and hashlib.sha256(im.tobytes()).hexdigest()==f['rgba_sha256']
            for facing in [1,-1]:
                actual={}
                for p in f['parts']:
                    d=resources[p['resource']];w,h=p['width'],p['height'];left=p['x']-64 if facing>0 else 64-p['x']-w
                    for y in range(h):
                        for x in range(w):
                            v=d[786+(h-y-1)*w+x]
                            if v:
                                key=(left+(x if facing>0 else w-1-x),p['y']+y-92);assert key not in actual;actual[key]=(*pal[v*3:v*3+3][::-1],255)
                expected={(x-64 if facing>0 else 63-x,y-92):data[y*128+x] for y in range(96) for x in range(128) if data[y*128+x][3]}
                assert actual==expected and max(y for x,y in actual)==-1
            if f['frame']<4:
                idlekeys.add(im.tobytes());assert im.crop((0,48,128,96)).tobytes()==idle.crop((0,48,128,96)).tobytes()
                assert im.crop((64,4,85,32)).tobytes()==idle.crop((64,4,85,32)).tobytes()
                if f['frame']==0:assert im.tobytes()==idle.tobytes()
            elif f['frame']<10:
                assert im.crop((0,0,128,24)).tobytes()==canonical.crop((0,0,128,24)).tobytes()
                assert im.crop((64,4,85,32)).tobytes()==canonical.crop((64,4,85,32)).tobytes()
        assert len(idlekeys)==4
        # Baseline identity and first half must survive the opposite-stride edit.
        for phase in range(6):
            im=Image.open(base/f'{name}-{phase+4:02d}.png').convert('RGBA')
            before=Image.open(base/'gait-before'/f'{name}-{phase+4:02d}.png').convert('RGBA')
            assert hashlib.sha256(before.tobytes()).hexdigest()==baseline['actors'][ai]['frames'][phase+4]['rgba_sha256']
            assert im.crop((0,0,128,52)).tobytes()==before.crop((0,0,128,52)).tobytes()
            if phase<3:assert im.tobytes()==before.tobytes()
            else:
                assert im.crop((0,52,128,96)).tobytes()!=before.crop((0,52,128,96)).tobytes()
                first=Image.open(base/f'{name}-{phase+1:02d}.png').convert('RGBA')
                # Geometry must differ, not only shading. This is a regression
                # guard; anatomical leg ownership still requires visual review.
                aa=im.getchannel('A').crop((0,52,128,96));bb=first.getchannel('A').crop((0,52,128,96))
                assert sum(x!=y for x,y in zip(aa.getdata(),bb.getdata()))>=100
            assert [x for x in range(128) if im.getpixel((x,91))[3]]==actor['walk_landmarks'][phase]['floor_x']
        for f in [0,1,2,3,10,11]:
            assert actor['frames'][f]['rgba_sha256']==json.loads((base/'gait-before/manifest.json').read_text())['actors'][ai]['frames'][f]['rgba_sha256']
        for mode,indices in [('idle',range(4)),('walk',range(4,10))]:
            gif=Image.open(base/f'{name}-{mode}.gif');assert gif.n_frames==len(indices)
            for fi,pose in enumerate(indices):
                gif.seek(fi);a=gif.convert('RGBA');b=Image.open(base/f'{name}-{pose:02d}.png').convert('RGBA').resize((384,288),Image.Resampling.NEAREST)
                assert a.getchannel('A').tobytes()==b.getchannel('A').tobytes()
                assert all(x[:3]==y[:3] for x,y in zip(a.getdata(),b.getdata()) if y[3])
    assert naive==m['naive_polished_bytes'] and newbytes==m['new_texture_bytes']
    assert naive-newbytes==m['dedup_saved_bytes'] and 355808+newbytes==m['total_vdp1_bytes']<=430496<458488
    assert len(m['tga_sha256'])+137<255 and m['guide_pixels_used']>0
    print(f'PASS polish: 4 unique breaths + 6 refined walks + 2 bridges per fighter, locked idle feet/faces, first three walks/upper bodies locked, changed second-half leg geometry, exact seams/mirroring/GIF colors, interning saves {naive-newbytes}; VDP1 {355808+newbytes}/458488.')
    return newbytes
if __name__=='__main__':validate_polish(Path(__file__).resolve().parents[1])
