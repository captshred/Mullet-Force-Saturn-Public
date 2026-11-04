#!/usr/bin/env python3
"""Run the selected profile's actual boot loaders with host allocation mocks.
Requires build/build-info.h and staged build/cd assets from the native wrapper.
No Saturn execution, DMA or performance measurement is implied.
"""
from pathlib import Path
import argparse, csv, subprocess, tempfile, sys
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--without-combo',action='store_true',help='compare identical profile with the two cross textures disabled')
parser.add_argument('--legacy-fx',action='store_true',help='retain BU01 upload to compare the original allocation')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='mf-sprite-audit-') as temp:
    work=Path(temp)
    info=(root/'build/build-info.h').read_text()
    dual='#define MF_ARCADE_FX 1' in info and not args.legacy_fx
    if args.legacy_fx:info=info.replace('#define MF_ARCADE_FX 1','#define MF_ARCADE_FX 0')
    if args.without_combo and dual:raise SystemExit('Disable dual FX with --legacy-fx before disabling the required combo profile')
    if args.without_combo:
        assert '#define MF_PUNCH_COMBO 1' in info
        info=info.replace('#define MF_PUNCH_COMBO 1','#define MF_PUNCH_COMBO 0')
    (work/'build-info.h').write_text(info)
    source=(root/'src/main.c').read_text().split('static int depth_key')[0]
    source='#include <assert.h>\nvoid audit_finish(void);\n'+source
    source+='\nint main(void){load_assets();assert(!asset_error);audit_finish();return 0;}\n'
    (work/'loader.c').write_text(source)
    subprocess.run(['cc','-std=c99','-ffunction-sections','-fdata-sections',
        '-include',str(work/'build-info.h'),'-I'+str(work),'-I'+str(root/'tests/sprite_audit'),
        '-I'+str(root/'build'),'-I'+str(root/'src'),str(work/'loader.c'),
        *[str(root/p) for p in ['tests/sprite_audit/stubs.c','src/animation_preview.c',
                                 'src/corporate_animation.c','src/gallery.c']],
        '-Wl,--gc-sections','-o',str(work/'audit')],check=True,cwd=root)
    result=subprocess.run([str(work/'audit')],check=True,cwd=root,capture_output=True,text=True)
    rows=list(csv.DictReader(result.stdout.splitlines()))
    assert len(rows)==(253 if args.without_combo else 255)
    assert sum(int(r['allocated_bytes']) for r in rows)==(446304 if args.without_combo else 452800 if dual else 453344)
    assert sum(r['path']=='EXPLODE.TGA' for r in rows)==int(dual)
    assert sum(r['path']=='BU01.TGA' for r in rows)==int(not dual)
    assert sum(int(r['allocated_bytes'])==0 for r in rows)==14
    def usage(row):
        name=row['path']
        if name=='alias':return 'stable row/tail view: HQ torch or jump; shares existing payload'
        if name.startswith('COMBAT/'):return 'shared attack sequence bank: jab/cross lower/horizontal contact plus legacy bat poses'
        for prefix,label in [('HQTORCH/','HQ blowtorch'),('HQJUMP/','jump and aerial kick'),('HQHURT/','hurt reactions'),('HQDEATH/','death lower pieces'),('COMBO/','jab-jab-cross upper')]:
            if name.startswith(prefix):return label
        if name.startswith(('BT','CT','AL')) or name=='LEGS.TGA':return 'legacy bat/aerial fallback; selected fast profile does not deploy planted bat'
        if name.startswith(('BU','CH','NL')):return 'legacy player fallback pieces; shared lower/body consumers'
        if name.startswith(('CP','HQ')):return 'Corporate Punk shared enemy bank'
        if name.startswith(('DR','SHADOW','HIT','EXPLODE','generated:')):return 'world object/effect or HUD'
        if name.startswith(('FL','EM','CHARGE')):return 'shared torch effect'
        return 'resident movement/gallery/review part; shared animation resource tables'
    for row in rows:row['usage']=usage(row)
    writer=csv.DictWriter(sys.stdout,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    sys.stderr.write(result.stderr)
