"""Independent gallery file, raster, mirrored placement, palette and budget checks."""
import hashlib,json,struct,re

def validate_gallery(root,files,existing):
    enabled=(root/'build/gallery-mode.txt').read_text().strip()=='1'
    assert (b'MULLET FORCE SPRITE GALLERY' in files['0.BIN'])==enabled
    manifest=json.loads((root/'assets/gallery/manifest.json').read_text())
    names={p['name'] for a in manifest['actors'] for p in a['parts']}
    if not enabled:
        assert not names.intersection(files),'Disabled build contains gallery textures'
        print('PASS: gallery disabled; no experimental textures packaged.')
        return
    header=(root/'src/gallery_data.h').read_text();palette=None;total=0
    for actor in manifest['actors']:
        w,h=actor['width'],actor['height'];assert h==88
        expected_name='GB' if actor['name']=='Buck' else 'GC'
        full=[None]*(w*h)
        for index,p in enumerate(actor['parts']):
            assert p['name']==f'{expected_name}{index}.TGA'
            data=(root/'assets/gallery'/p['name']).read_bytes()
            assert files[p['name']]==data
            assert hashlib.sha256(data).hexdigest()==p['sha256']
            assert data[:3]==b'\0\1\1' and data[16:18]==b'\x08\0'
            pw,ph=struct.unpack_from('<HH',data,12)
            assert (pw,ph)==(p['width'],p['height']) and pw%8==0
            assert len(data)==786+pw*ph and max(data[786:])<=253
            pal=data[18:786];assert pal[:3]==b'\xff\0\xff'
            assert all(v%8==0 for v in pal[3:])
            if palette is None:palette=pal
            assert palette==pal
            cost=(pw*ph+31)&~31;assert cost==p['vram'];total+=cost
            literal='{"%s",%d,%d,%d,%d}'%(p['name'],p['x'],p['y'],pw,ph)
            assert literal in header
            for y in range(ph):
                for x in range(pw):
                    i=data[786+(ph-1-y)*pw+x]
                    if i:
                        xx,yy=p['x']+x,p['y']+y
                        assert 0<=xx<w and 0<=yy<h
                        assert full[yy*w+xx] is None,'Overlapping opaque pieces'
                        full[yy*w+xx]=pal[i*3:i*3+3][::-1]
        # Compare assembled RGB + coverage to the approved full indexed PNG.
        from PIL import Image
        ref=Image.open(root/'assets/gallery'/f"{actor['name'].lower()}-88.png").convert('RGBA')
        assert ref.size==(w,h)
        expected=[bytes(c[:3]) if c[3] else None for c in ref.getdata()]
        assert full==expected,'Piece seam, coverage or color mismatch'
        assert any(full[x] is not None for x in range(w))
        assert any(full[87*w+x] is not None for x in range(w))
        # Match the C world-origin formula including padded-width mirroring.
        for facing in (1,-1):
            assembled={};center=90;ground=210;origin=w//2
            for p in actor['parts']:
                d=files[p['name']];pw,ph=p['width'],p['height']
                left=center-origin+p['x'] if facing>0 else center+origin-p['x']-pw
                for y in range(ph):
                    for x in range(pw):
                        i=d[786+(ph-1-y)*pw+x]
                        if i:
                            xx=left+(x if facing>0 else pw-1-x)
                            yy=ground-88+p['y']+y
                            assert (xx,yy) not in assembled
                            assembled[xx,yy]=palette[i*3:i*3+3][::-1]
            target={}
            for y in range(h):
                for x in range(w):
                    if full[y*w+x] is not None:
                        xx=center-origin+x if facing>0 else center+origin-1-x
                        target[xx,ground-88+y]=full[y*w+x]
            assert assembled==target
            assert max(y for x,y in assembled)==209,'Feet must end at ground boundary 210'
    assert total==manifest['texture_bytes']==10784
    assert f'#define MF_GALLERY_BYTES {total}u' in header
    assert existing+total<458488
    assert 7+manifest['palette_banks']==8
    print(f'PASS: six gallery pieces exact, seamless, mirrored and grounded; VDP1 {existing+total}/458488 ({458488-existing-total} free); CRAM 8/8 banks.')
