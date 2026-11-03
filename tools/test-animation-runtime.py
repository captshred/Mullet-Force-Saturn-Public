#!/usr/bin/env python3
"""Optional controller-driven Yabause test of an existing animation+parallax build.
Requires an already built libretro core/header, C compiler and Pillow. No game
source modification, BIOS download or automatic core installation occurs.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
from PIL import Image

def hardware(c):
    red,green,blue=c
    return (red//8*255//31,green//8*2*255//63,blue//8*255//31)

def verify(root,out,core):
    palette=(root/'assets/cd/ST0.TGA').read_bytes()[18:786]
    colors=[hardware(palette[i*3:i*3+3][::-1]) for i in range(256)]
    rows=[[] for _ in range(240)]
    for tile in range(5):
        data=(root/f'assets/cd/ST{tile}.TGA').read_bytes()
        for y in range(240):rows[y].extend(colors[v] for v in data[786+(239-y)*128:786+(240-y)*128])
    base=Image.new('RGB',(320,240));base.putdata([(8,8,24)]*320+[c for row in rows[:239] for c in row[279:599]])
    # Stable paused poses cover every new idle/walk and every original pose
    # in both facings. Guards are compared frame-by-frame during a real stop.
    sequence=[(359,0,1),(389,1,1),(409,2,1),(429,3,1),(449,0,1),(469,0,-1),(489,1,-1),(509,2,-1),(529,3,-1),
              (549,4,-1),(569,5,-1),(589,6,-1),(609,7,-1),(629,8,-1),(649,9,-1),
              (669,9,1),(689,8,1),(709,7,1),(729,6,1),(749,5,1),(769,4,1),(1069,0,1),(1199,0,1),(1459,0,1)]
    originals=[(789,1,1),(809,2,1),(829,3,1),(849,4,1),(869,5,1),(889,6,1),
               (909,6,-1),(929,5,-1),(949,4,-1),(969,3,-1),(989,2,-1),(1009,1,-1),(1029,0,-1),(1049,0,1)]
    checks=[];references={}
    def expected(pose,facing,polish):
        pair=pose if isinstance(pose,tuple) else (pose,pose)
        key=(pair,facing,polish)
        if key not in references:
            im=base.copy()
            for ai,(actor,center) in enumerate([('buck',90),('chuck',226)]):
                pose=pair[ai]
                frame=Image.open(root/f"assets/{'animation-polish' if polish else 'animation-study'}/{actor}-{pose:02d}.png").convert('RGBA')
                if facing<0:frame=frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                for y in range(96):
                    for x in range(128):
                        c=frame.getpixel((x,y))
                        if c[3]:im.putpixel((center-64+x+1,118+y+1),hardware(c[:3]))
            references[key]=im.crop((0,122,320,212)).tobytes()
        return references[key]
    for polish,poses in [(True,sequence),(False,originals)]:
        for capture,pose,facing in poses:
            actual=Image.open(out/f'frame-{capture:04d}.ppm').convert('RGB');a=actual.crop((0,122,320,212)).tobytes();b=expected(pose,facing,polish)
            errors=sum(a[i:i+3]!=b[i:i+3] for i in range(0,len(a),3))
            checks.append({'capture_frame':capture,'set':'polish' if polish else 'original','pose':pose,'facing':facing,'mismatched_pixels':errors})
            assert not errors,f'Pose {pose}, facing {facing}, capture {capture}: {errors} pixels differ'
            actual.save(out/f'frame-{capture:04d}.png')
    bridge_seen=False
    for capture in range(1120,1160):
        actual=Image.open(out/f'frame-{capture:04d}.ppm').convert('RGB');a=actual.crop((0,122,320,212)).tobytes()
        matches=[pose for pose in range(12) if a==expected(pose,1,True)]
        assert matches,f'Unassembled pose during stop/bridge at capture {capture}'
        bridge_seen=bridge_seen or 10 in matches
        checks.append({'capture_frame':capture,'set':'polish','matching_poses':matches,'facing':1,'mismatched_pixels':0})
        if 10 in matches:actual.save(out/'guard-bridge.png')
    assert bridge_seen,'Stop did not render its lowered-guard bridge'
    breathing=[]
    for capture in range(1470,1641):
        actual=Image.open(out/f'frame-{capture:04d}.ppm').convert('RGB').crop((0,122,320,212)).tobytes()
        matches=[(a,b) for a in range(4) for b in range(4) if actual==expected((a,b),1,True)]
        assert len(matches)==1,f'Breathing assembly mismatch at capture {capture}'
        breathing.append((capture,matches[0]))
        checks.append({'capture_frame':capture,'set':'polish-idle-auto','poses':list(matches[0]),'facing':1,'mismatched_pixels':0})
    duration_checks=[]
    for actor,holds in enumerate([[24,16,24,16],[30,18,24,18]]):
        assert {pair[actor] for capture,pair in breathing}==set(range(4))
        runs=[]
        for capture,pair in breathing:
            pose=pair[actor]
            if runs and runs[-1][0]==pose:runs[-1][1]+=1
            else:runs.append([pose,1])
        for pose,length in runs[1:-1]:assert length==holds[pose],(actor,pose,length,holds)
        duration_checks.append({'actor':actor,'complete_holds_verified':runs[1:-1]})
    def same(a,b):return Image.open(out/f'frame-{a:04d}.ppm').convert('RGB').tobytes()==Image.open(out/f'frame-{b:04d}.ppm').convert('RGB').tobytes()
    assert same(299,1249),'Original gallery restoration changed'
    report={'core':re.search(r'^Core (.+)$',(out/'run.log').read_text(),re.M).group(1),'core_sha256':hashlib.sha256(core.read_bytes()).hexdigest(),
            'bios':'HLE','renderer':'software','frames_run':2000,'checks':checks,'compared_character_region_pixels':len(checks)*320*90,
            'mismatched_pixels':0,'gallery_restore_exact':True,'bridge_seen':True,'idle_duration_checks':duration_checks,
            'region':'Whole 320x90 actor/ground region y122..211; independent native PNG + street reconstruction, SGL raster origin (+1,+1), RGB565 quantization.',
            'source_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['src/animation_preview.c','src/animation_data.h','src/animation_polish_data.h','src/gallery.c','src/main.c','src/game.c']}}
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    for capture in [299,1249,1289,1399,1499,1599,1759,1999]:Image.open(out/f'frame-{capture:04d}.ppm').save(out/f'frame-{capture:04d}.png')
    return report

def main():
    root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',required=True,type=Path);p.add_argument('--libretro-include',required=True,type=Path)
    p.add_argument('--cue',type=Path,default=root/'build/mullet-force.cue');p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);frontend=out/'animation-frontend'
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-I'+str(a.libretro_include.resolve()),str(root/'tests/runtime/animation-frontend.c'),'-ldl','-o',str(frontend)],check=True)
    with (out/'run.log').open('w') as log:
        subprocess.run([str(frontend),str(a.core.resolve()),str(a.cue.resolve()),str(out),'2000','controls'],stdout=log,stderr=subprocess.STDOUT,check=True)
    report=verify(root,out,a.core.resolve())
    print(f"PASS: polished breaths/walk and original poses, both facings, guard handoff; {report['compared_character_region_pixels']} pixels; gallery restoration exact.")
if __name__=='__main__':main()
