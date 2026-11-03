"""Independently decode hardware PND/cells and compare every source/scroll pixel."""
import hashlib,json,struct

def validate_street(root,files=None):
    enabled=(root/'build/vdp2-mode.txt').read_text().strip()=='1' if files is not None else True
    manifest=json.loads((root/'assets/vdp2/manifest.json').read_text())
    names={'STCELLS.BIN','STMAP.BIN','STPAL.BIN'}
    if not enabled:
        assert not names.intersection(files)
        print('PASS: VDP1 fallback; no VDP2 street files in disc.')
        return 0
    if files is not None:
        obj=(root/'build/street.o').read_bytes()
        assert obj[:4]==b'\x7fELF' and obj[5]==2,'Generated maps require the pinned big-endian target'
    data={n:(root/'assets/vdp2'/n).read_bytes() for n in names}
    for n,d in data.items():
        assert hashlib.sha256(d).hexdigest()==manifest['sha256'][n]
        if files is not None:assert files[n]==d
    cells=data['STCELLS.BIN'];mapping=struct.unpack('>8192H',data['STMAP.BIN'])
    pal=struct.unpack('>255H',data['STPAL.BIN'])
    assert len(cells)==90240 and manifest['tile_count']==1410
    assert len(data['STMAP.BIN'])==16384 and len(data['STPAL.BIN'])==510
    assert 0 not in cells and max(cells)<=254
    source=[bytearray() for _ in range(240)];palette=None
    for i in range(5):
        n=f'ST{i}.TGA';d=(root/'assets/cd'/n).read_bytes()
        assert hashlib.sha256(d).hexdigest()==manifest['source_sha256'][n]
        if palette is None:palette=d[18:786]
        assert d[18:786]==palette
        for y in range(240):source[y].extend(d[786+(239-y)*128:786+(240-y)*128])
    for i in range(255):
        b,g,r=palette[3*i:3*i+3]
        assert pal[i]==0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10)
    # Decode two horizontal 512x512 hardware pages, not a flat 128-wide map.
    rebuilt=[]
    for y in range(240):
        row=bytearray()
        for x in range(640):
            pnd=mapping[(x//512)*4096+(y//8)*64+(x%512)//8]
            assert pnd>>12==1 and not pnd&1
            tile=(pnd&4095)//2;assert tile<1410
            pixel=cells[tile*64+(y%8)*8+x%8]
            row.append(pixel-1)
        assert row==source[y],f'Source pixel/seam mismatch at y={y}'
        rebuilt.append(row)
    # Every valid camera position and every column, including fractional tile
    # offsets, original 128px seams and the new hardware page seam at x=512.
    for camera in range(321):
        for y in range(240):
            assert rebuilt[y][camera:camera+320]==source[y][camera:camera+320]
    # Screen registration is separate from lossless source conversion. SGL's
    # unit-scale VDP1 sprites rasterize at requested (x+1,y+1). Reproduce the
    # original strict culling too: at camera 0/128/256 column zero is backdrop.
    # 255 is a sentinel for the backdrop, never an opaque street index.
    for camera in range(321):
        left=int(camera%128==0)
        for screen_y in range(240):
            original=bytearray([255])*320
            if screen_y:
                for tile in range(5):
                    requested=tile*128-camera
                    if not -128<requested<320:continue
                    start=requested+1
                    lo=max(0,start);hi=min(320,start+128)
                    if lo<hi:
                        tex=source[screen_y-1][tile*128:(tile+1)*128]
                        original[lo:hi]=tex[lo-start:hi-start]
            actual=bytearray([255])*320
            if screen_y:
                start=camera+left-1
                actual[left:]=rebuilt[screen_y-1][start:start+320-left]
            assert original==actual,f'VDP1/VDP2 screen registration: camera={camera}, y={screen_y}'
    assert 90240<0x20000 and 16384<0x20000
    assert manifest['street_vdp2_bytes']==106624
    assert manifest['reserved_vdp2_bytes']==368768
    assert manifest['vdp1_recovered_bytes']==153600
    print('PASS: VDP2 exact 640x240 pixels/RGB555 palette, all 321 source AND screen camera positions including backdrop borders and strict VDP1 culling, tile/TGA/page seams; 106624 street VRAM + 262144 SDK-protected = 368768 reserved; 153600 VDP1 recovered.')
    return 153600

if __name__=='__main__':
    from pathlib import Path
    validate_street(Path(__file__).resolve().parents[1])
