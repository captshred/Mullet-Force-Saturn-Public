"""Frame1-only leg override, unchanged canvas/anchors/layout and prior frame bytes."""
from pathlib import Path
import hashlib,json,struct

def validate_knee_lift(root,files=None):
    if files is not None and (root/'build/knee-lift-mode.txt').read_text().strip()!='1':return None
    from PIL import Image
    base=root/'assets/knee-lift';m=json.loads((base/'manifest.json').read_text());original=json.loads((root/'assets/original-three-walk/manifest.json').read_text())
    assert {p.name for p in (base/'overrides').glob('*.TGA')}==set(m['overrides'])
    polish=json.loads((root/'assets/animation-polish/manifest.json').read_text())
    assert all(not {4,5,25,26}.intersection(p['resource'] for p in f['parts']) for a in polish['actors'] for f in a['frames'])
    assert set(m['overrides'])=={'AB11.TGA','AB12.TGA','AC11.TGA','AC12.TGA'}
    assert hashlib.sha256((base/'source/frame1-edit.png').read_bytes()).hexdigest()==m['guide_sha256']
    for n,h in m['frame2_3_sha256'].items():assert (base/n).read_bytes()==(root/'assets/original-three-walk'/n).read_bytes() and hashlib.sha256((base/n).read_bytes()).hexdigest()==h
    for a,actor in enumerate(m['actors']):
        n=actor['name'];assert (base/'before'/f'{n}-00.png').read_bytes()==(root/f'assets/original-three-walk/{n}-00.png').read_bytes();before=Image.open(root/f'assets/original-three-walk/{n}-00.png').convert('RGBA');after=Image.open(base/f'{n}-00.png').convert('RGBA')
        assert after.size==(128,96) and after.getbbox()[1]==4 and after.getbbox()[3]==92
        assert hashlib.sha256(after.tobytes()).hexdigest()==actor['rgba_sha256']
        changed=0
        for y in range(96):
            for x in range(128):
                if before.getpixel((x,y))!=after.getpixel((x,y)):
                    changed+=1;assert (56<=y<58 and 72<=x<100) or (58<=y<92 and 64<=x<(100 if y<80 else 102))
        assert changed==actor['changed_pixels']>0
        assert after.crop((0,0,64,96)).tobytes()==before.crop((0,0,64,96)).tobytes()
        assert after.crop((48,44,72,58)).tobytes()==before.crop((48,44,72,58)).tobytes() # fixed hip/pelvis
        assert actor['front_sole_y']==88 and actor['rear_sole_y']==91
        assert not any(after.getpixel((x,y))[3] for y in range(89,92) for x in range(64,102))
        for f in range(3):
            im=Image.open(base/f'{n}-{f:02d}.png').convert('RGBA')
            for direction in [1,-1]:
                actual={}
                for p in original['actors'][a]['frames'][f]['parts']:
                    override=base/'overrides'/p['name'];source=root/'assets/animation-study'/p['name'];d=override.read_bytes() if f==0 and override.exists() else source.read_bytes()
                    if override.exists() and f==0:
                        assert d[:786]==source.read_bytes()[:786] and len(d)==len(source.read_bytes())
                        assert hashlib.sha256(d).hexdigest()==m['overrides'][p['name']]
                        original_bytes=source.read_bytes()
                        for offset,(v,oldv) in enumerate(zip(d[786:],original_bytes[786:])):
                            if v!=oldv:
                                xx=p['x']+offset%p['width'];yy=p['y']+p['height']-1-offset//p['width']
                                assert (56<=yy<58 and 72<=xx<100) or (58<=yy<92 and 64<=xx<(100 if yy<80 else 102))
                    if files is not None:assert files[p['name']]==d
                    w,h=struct.unpack_from('<HH',d,12);assert (w,h)==(p['width'],p['height'])
                    left=p['x']-64 if direction>0 else 64-p['x']-w
                    for y in range(h):
                        for x in range(w):
                            v=d[786+(h-y-1)*w+x]
                            if v:
                                assert v<=253;key=(left+(x if direction>0 else w-1-x),p['y']+y-92);assert key not in actual;actual[key]=(*d[18+3*v:21+3*v][::-1],255)
                expected={(x-64 if direction>0 else 63-x,y-92):im.getpixel((x,y)) for y in range(96) for x in range(128) if im.getpixel((x,y))[3]}
                assert actual==expected
        gif=Image.open(base/f'{n}-cycle.gif');assert gif.n_frames==3
        for f in range(3):
            gif.seek(f);aa=gif.convert('RGBA');bb=Image.open(base/f'{n}-{f:02d}.png').convert('RGBA').resize((384,288),Image.Resampling.NEAREST)
            assert aa.getchannel('A').tobytes()==bb.getchannel('A').tobytes()
            assert all(x[:3]==y[:3] for x,y in zip(aa.getdata(),bb.getdata()) if y[3])
    assert (root/'src/original_three_timing.h').read_text().find('#define MF_ORIGINAL_HOLD_SLOW 10')>=0
    assert m['boot_bytes']==351104 and m['free_bytes']==107384 and m['full_bytes']==427104
    print('PASS knee lift: frame1 front-leg-only ROI, fixed upper/pelvis/support, three-pixel front sole clearance, exact frame2/3 bytes, same palette/layout, mirrored seams and GIFs, zero added texture bytes.')
    return m
if __name__=='__main__':validate_knee_lift(Path(__file__).resolve().parents[1])
