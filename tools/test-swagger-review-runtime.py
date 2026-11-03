#!/usr/bin/env python3
"""Read-only Yabause test of one-shot swagger review expansion and game return."""
import argparse,subprocess,re,json,hashlib
from pathlib import Path
from PIL import Image
import numpy as np
from playable_runtime_validation import trace,hardware
R=Path(__file__).resolve().parents[1]
def read32(data,address):
    n=int.from_bytes(data[address&0xfffff:(address&0xfffff)+4],'little');return ((n>>16)|(n<<16))&0xffffffff

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--refined',action='store_true',help='Refined92px Corporate Punk bank; also pass --corporate')
    p.add_argument('--corporate',action='store_true',help='Include shared Corporate Punk resident bank')
    p.add_argument('--original',action='store_true',help='Original three compact/full bank')
    p.add_argument('--core',required=True,type=Path);p.add_argument('--libretro-include',required=True,type=Path);p.add_argument('--build',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--nm',default='sh-elf-nm');a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    symbols=subprocess.check_output([a.nm,'--target=coff-sh',str(a.build/'game.elf')],text=True)
    def addr(name):return re.search(r'^([0-9a-f]+) . '+re.escape(name)+r'$',symbols,re.M).group(1)
    texture_addresses=[int(v,16) for v in re.findall(r'^([0-9a-f]+) [bd] _texture_bytes[^\n]*$',symbols,re.M)]
    frontend=out/'frontend'
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-I'+str(a.libretro_include.resolve()),'-I'+str(R/'src'),str(R/'tests/runtime/playable-frontend.c'),'-ldl','-o',str(frontend)],check=True)
    with (out/'run.log').open('w') as log:subprocess.run([str(frontend),str(a.core.resolve()),str((a.build/'mullet-force.cue').resolve()),str(out),'1600','review',addr('_game'),addr('_idle_ticks')],stdout=log,stderr=subprocess.STDOUT,check=True)
    allocations={};slots={}
    for frame,want,slot in ([(299,351104,124),(1000,427104,175),(1500,427104,175)] if a.original else [(299,346368,122),(1000,439776,187),(1500,439776,187)]):
        if a.corporate:want+=(11744 if a.refined else 14016);slot+=(10 if a.refined else 9)
        raw=(out/f'frame-{frame:04d}.wram').read_bytes();values=[read32(raw,v) for v in texture_addresses];assert want in values,(frame,values);allocations[frame]=want
        actual=read32(raw,int(addr('___jo_sprite_id'),16));assert actual==slot,(frame,actual,slot);slots[frame]=actual+1
    # Independently rebuild the old preview's street and try all 16 idle pairs.
    rows=[[] for _ in range(240)]
    for i in range(5):
        im=hardware(Image.open(R/f'assets/cd/ST{i}.TGA').convert('RGBA'))[:,:,:3]
        for y in range(240):rows[y].extend(im[y])
    background=np.zeros((240,320,3),dtype=np.uint8);background[0]=[8,8,24]
    for y in range(1,240):background[y]=rows[y-1][279:599]
    actual=np.asarray(Image.open(out/'frame-1000.ppm').convert('RGB'))[122:212];matches=[]
    for buck in range(4):
        for chuck in range(4):
            expected=background.copy()
            for name,f,center in [('buck',buck,90),('chuck',chuck,226)]:
                ref=hardware(Image.open(R/f'assets/animation-polish/{name}-{f:02d}.png').convert('RGBA'));yy,xx=np.where(ref[:,:,3]>0);expected[119+yy,center-63+xx]=ref[yy,xx,:3]
            if np.array_equal(actual,expected[122:212]):matches.append([buck,chuck])
    assert len(matches)==1,('Expanded preview image mismatch',matches)
    records=trace(out);assert records[1500].game.started and records[1500].game.ticks>0
    assert len({r.texture_hash for f,r in records.items() if f>=1000})==1,'Expanded textures changed during playback/game return'
    for f in [299,1000,1250,1500]:Image.open(out/f'frame-{f:04d}.ppm').save(out/f'frame-{f:04d}.png')
    report={'frames_run':1600,'core_sha256':hashlib.sha256(a.core.read_bytes()).hexdigest(),'actual_allocations':allocations,'actual_sprite_slots':slots,'preview_idle_pair':matches[0],'preview_compared_pixels':320*90,'preview_mismatches':0,'game_return_verified':True,'expanded_textures_stable':True,'method':'Normal gallery Down / Start input, read-only save states. Actual allocation counters and Jo descriptor count, independent RGB565 preview reconstruction. No RAM writes/game hooks.'}
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS swagger review: actual boot/full allocations and descriptor counts, old preview pixels, gameplay return, no further texture changes.')
if __name__=='__main__':main()
