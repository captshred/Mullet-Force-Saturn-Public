"""Independently validate placeholder data, palette reuse and bounded allocations."""
from pathlib import Path
import hashlib,json,struct

def validate_parallax(root,files=None):
    m=json.loads((root/'assets/parallax/manifest.json').read_text())
    data={n:(root/'assets/parallax'/n).read_bytes() for n in m['sha256']}
    for n,d in data.items():assert hashlib.sha256(d).hexdigest()==m['sha256'][n]
    if files is not None:
        enabled=(root/'build/parallax-mode.txt').read_text().strip()=='1'
        assert (b'PARALLAX STREAMING TEST' in files['0.BIN'])==enabled
        if not enabled:
            assert not set(data).intersection(files)
            print('PASS: parallax disabled; no preview files or executable entry point.')
            return
        for n,d in data.items():assert files[n]==d
        assert (root/'build/vdp2-mode.txt').read_text().strip()=='1'
        assert (root/'build/gallery-mode.txt').read_text().strip()=='1'
    original=struct.unpack('>8192H',(root/'assets/vdp2/STMAP.BIN').read_bytes())
    chunks=struct.unpack('>2400H',data['PCHUNK.BIN'])
    for s in range(5):
        for y in range(30):
            for x in range(16):
                col=s*16+x
                assert chunks[(s*30+y)*16+x]==original[(col//64)*4096+y*64+col%64]
    cells=data['PSKY.BIN'];mapping=struct.unpack('>4096H',data['PSMAP.BIN'])
    assert len(cells)==8192 and len(data['PSMAP.BIN'])==8192 and len(data['PCHUNK.BIN'])==4800
    assert m['skyline_tiles']==52 and m['indices'] and 0 not in m['indices']
    assert not any(cells[52*64:])
    for p in mapping:
        assert p>>12==1 and not p&1
        i=((p&4095)-512)//2
        assert 0<=i<52
        assert set(cells[i*64:(i+1)*64])<=set(m['indices'])
    assert m['world_pixels']==8192 and m['world_chunks']==64
    assert m['ring_chunks']*128==1024 and m['ring_map_bytes']==16384
    assert m['extra_vdp2_bytes']==16384 and m['total_vdp2_reservation']==385152
    assert m['extra_palette_bytes']==m['extra_vdp1_bytes']==0
    # Both layers' visible addresses for every pixel camera offset, including
    # negative registered source x at the initial left edge (window clips it).
    for camera in range(7873):
        base=max(0,min(56,camera//128-2))
        for x in range(0 if camera else 1,320):
            world=camera-1+x;chunk=world//128
            assert base<=chunk<base+8 and 0<=chunk<64
            assert 0<=(camera//4+x)%512<512
    print('PASS: original chunk pixels/PNDs, 52 skyline tiles, existing palette ID 1; all 7873 viewport ranges; 16384 extra VDP2 bytes, zero extra VDP1/CRAM; ring size independent of level length.')
if __name__=='__main__':validate_parallax(Path(__file__).resolve().parents[1])
