#!/usr/bin/env python3
"""Optional actual Yabause comparison; builds a separate ROM, never edits game sources.
Requires an already built libretro Yabause core/header and a COFF-capable SH nm.
"""
import argparse,hashlib,json,os,re,shutil,struct,subprocess,tempfile
from pathlib import Path

def references(root,out):
    p=(root/'assets/cd/ST0.TGA').read_bytes()[18:786]
    colors=[]
    # Yabause's RGB555 -> RGB565 frontend quantization (green LSB is zero).
    for i in range(256):
        b,g,r=p[3*i:3*i+3];colors.append(bytes([r//8*255//31,g//8*2*255//63,b//8*255//31]))
    rows=[bytearray() for _ in range(240)]
    for i in range(5):
        d=(root/f'assets/cd/ST{i}.TGA').read_bytes()
        for y in range(240):
            for v in d[786+(239-y)*128:786+(240-y)*128]:rows[y].extend(colors[v])
    (out/'street.rgb').write_bytes(b''.join(rows))
    c=(root/'assets/parallax/PSKY.BIN').read_bytes()
    m=struct.unpack('>4096H',(root/'assets/parallax/PSMAP.BIN').read_bytes())
    (out/'sky.rgb').write_bytes(b''.join(colors[c[(((m[(y//8)*64+x//8]&4095)-512)//2)*64+(y%8)*8+x%8]-1] for y in range(64) for x in range(512)))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',type=Path,required=True)
    p.add_argument('--libretro-include',type=Path,required=True)
    p.add_argument('--nm',default='sh-elf-nm')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--quick',action='store_true',help='First ten offsets only; not a complete validation')
    a=p.parse_args();root=Path(__file__).resolve().parents[1];out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env.update(MF_PARALLAX_DEMO='1',MF_SPRITE_GALLERY='1',MF_VDP2_STREET='1',MF_STREET_LEGACY_CHECK='0')
    with tempfile.TemporaryDirectory(prefix='mf-parallax-rom-') as tmp:
        rom=Path(tmp)/'rom'
        shutil.copytree(root,rom,ignore=shutil.ignore_patterns('.git','.deps','build','__pycache__'))
        (rom/'.deps').symlink_to(root/'.deps',target_is_directory=True)
        shutil.copy(root/'tests/runtime/parallax-main.c',rom/'src/main.c')
        with (out/'harness-build.log').open('w') as log:
            subprocess.run(['make','native'],cwd=rom,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        symbols=subprocess.check_output([a.nm,'--target=coff-sh',str(rom/'build/game.elf')],text=True)
        address=int(re.search(r'^([0-9a-f]+) b _preview$',symbols,re.M).group(1),16)+12
        # SH-2 ABI: two 4-byte pointers, active int, camera int. Host writes
        # this private test state; normal gameplay has no test hooks or API.
        references(root,out)
        frontend=out/'parallax-frontend'
        subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-I'+str(a.libretro_include.resolve()),str(root/'tests/runtime/parallax-frontend.c'),'-ldl','-o',str(frontend)],check=True)
        frames=360 if a.quick else 94770
        with (out/'run.log').open('w') as log:
            subprocess.run([str(frontend),str(a.core.resolve()),str(rom/'build/mullet-force.cue'),str(out),str(frames),f'{address:08x}'],stdout=log,stderr=subprocess.STDOUT,check=True)
        text=(out/'run.log').read_text();match=re.search(r'Verified (\d+) complete 320x240 positions; (\d+) pixels; zero mismatches',text)
        assert match,text[-3000:]
        report={'positions':int(match[1]),'compared_pixels':int(match[2]),'mismatched_pixels':0,'quick':a.quick,
                'core_sha256':hashlib.sha256(a.core.read_bytes()).hexdigest(),'bios':'HLE','renderer':'software','viewport':[320,240],
                'source_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['src/parallax.c','src/street.c','tests/runtime/parallax-main.c','tests/runtime/parallax-frontend.c']}}
        (out/'runtime-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
