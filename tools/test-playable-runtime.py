#!/usr/bin/env python3
"""Controller-driven playable/control Yabause test; no writes to game memory.
Requires Pillow/NumPy, an existing libretro core/header, and pinned sh-elf-nm.
"""
import argparse,subprocess,os,re,json,hashlib
from pathlib import Path
from playable_runtime_validation import validate
R=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',required=True,type=Path);p.add_argument('--libretro-include',required=True,type=Path)
    p.add_argument('--playable',required=True,type=Path,help='Build directory with BIN/CUE and game.elf')
    p.add_argument('--control',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--knee-lift',action='store_true',help='Frame1-only knee refinement at Timing B')
    p.add_argument('--original-hold',type=int,choices=[8,10],default=0,help='Restored original three:8 moderate or10 slow ticks')
    p.add_argument('--swagger',action='store_true',help='Validate the experimental three-pose swagger renderer')
    p.add_argument('--nm',default='sh-elf-nm');a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    frontend=a.out/'playable-frontend'
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-I'+str(a.libretro_include.resolve()),'-I'+str(R/'src'),str(R/'tests/runtime/playable-frontend.c'),'-ldl','-o',str(frontend)],check=True)
    for name,build in [('playable',a.playable),('control',a.control)]:
        out=a.out/name;out.mkdir(exist_ok=True)
        symbols=subprocess.check_output([a.nm,'--target=coff-sh',str(build/'game.elf')],text=True)
        game=re.search(r'^([a-f0-9]+) . _game$',symbols,re.M).group(1)
        idle=re.search(r'^([a-f0-9]+) . _idle_ticks$',symbols,re.M)
        env=os.environ.copy()
        if name=='control':env['MF_RUNTIME_CONTROL']='1'
        with (out/'run.log').open('w') as log:
            subprocess.run([str(frontend),str(a.core.resolve()),str((build/'mullet-force.cue').resolve()),str(out),'1050','controls',game,idle.group(1) if idle else '0'],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
    report=validate(a.out/'playable',a.out/'control',swagger=a.swagger,original_hold=a.original_hold,knee_lift=a.knee_lift)
    report.update({'core_sha256':hashlib.sha256(a.core.read_bytes()).hexdigest(),'bios':'HLE','renderer':'software','cpu':'interpreter','hardware_tested':False,
                   'playable_bin_sha256':hashlib.sha256((a.playable/'mullet-force.bin').read_bytes()).hexdigest(),'control_bin_sha256':hashlib.sha256((a.control/'mullet-force.bin').read_bytes()).hexdigest()})
    (a.out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"PASS playable/control: {report['compared_pixels']} native sprite pixels, zero mismatches; simulation identical for {report['simulation_frames_compared']} frames; resident textures unchanged.")
if __name__=='__main__':main()
