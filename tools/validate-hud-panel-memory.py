#!/usr/bin/env python3
"""Phase 4 preservation: generated panel width and its two draw consumers only."""
from pathlib import Path
import io,json,subprocess,sys,tarfile,tempfile
R=Path(__file__).resolve().parents[1]
BASE='279e33d2f60645b12cf479ba3b096954565a0173'
allowed={'Makefile','src/main.c','src/animation_preview.c','src/arcade_fx_config.h',
         'tools/build-native.sh','tools/build-source-complete.sh','tools/audit-sprite-memory.py'}
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='sprite-cleanup-baseline-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 for p in ref.rglob('*'):
  if p.is_file() and str(p.relative_to(ref)) not in allowed:
   assert (R/p.relative_to(ref)).read_bytes()==p.read_bytes(),str(p.relative_to(ref))
 main=(R/'src/main.c').read_text()
 main=main.replace('img.width=MF_HUD_PANEL_WIDTH; img.height=40;','img.width=256; img.height=40;')
 main=main.replace('for(i=0;i<MF_HUD_PANEL_WIDTH*40;i++) pixels[i]=(i/MF_HUD_PANEL_WIDTH==0 || i/MF_HUD_PANEL_WIDTH==39)?','for(i=0;i<256*40;i++) pixels[i]=(i/256==0 || i/256==39)?')
 main=main.replace('width*65536/MF_HUD_PANEL_WIDTH,8*65536/40','width*65536/256,8*65536/40')
 main=main.replace('    if(mode) {\n#if MF_HUD_PANEL_MEMORY\n        /* Original SGL center-zoom uses size-1 and truncates the half-size:\n           CMDCTRL=0xa01, A=(0,64), B=(255,39) -> x33..288, y165..204.\n           Match those inclusive edges without the HV angle workaround. */\n        static const jo_pos2D_fixed corners[4]={\n            {-127*65536,45*65536},{128*65536,45*65536},\n            {128*65536,84*65536},{-127*65536,84*65536}\n        };\n        jo_sprite_draw_4p_fixed(panel,corners,180*65536,true);\n#else\n        jo_sprite_draw3D2(panel,32,164,180);\n#endif\n    }\n','    if(mode)jo_sprite_draw3D2(panel,32,164,180);\n')
 assert main==(ref/'src/main.c').read_text(),'change outside the exact panel generation/health scale/quad integrations'
 assert (R/'src/animation_preview.c').read_text().replace('-MF_HUD_PANEL_SAVED_BYTES','')==(ref/'src/animation_preview.c').read_text(),'animation change outside panel accounting'
 for n in ('.git','.deps'):(ref/n).symlink_to(R/n,target_is_directory=True)
 # Native staging contains copies of current src headers. Never let those
 # shadow the archived profile's own config headers during its host tests.
 (ref/'build').mkdir()
 for p in (R/'build').iterdir():
  if p.suffix not in ('.h','.c'):(ref/'build'/p.name).symlink_to(p,target_is_directory=p.is_dir())
 (ref/'build/build-info.h').write_text((R/'build/build-info.h').read_text().replace('#define MF_HUD_PANEL_MEMORY 1','#define MF_HUD_PANEL_MEMORY 0'))
 subprocess.run(['python3','tools/validate-duplicate-texture-cleanup.py',*[x for x in sys.argv[1:] if x in ('--test','--disc')]],cwd=ref,check=True)
print('PASS Phase4 scope: baseline assets/AI/input/audio/Level2 frozen; only exact panel generation/scale/quad and budgets changed; all gameplay/animation/audio/Level2 frozen',flush=True)
if '--disc' in sys.argv or '--test' in sys.argv:
 subprocess.run(['python3','tools/test-hud-panel-memory.py'],cwd=R,check=True)
