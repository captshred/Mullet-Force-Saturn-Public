#!/usr/bin/env python3
"""Host regression: real damage resolution + draw routing, and actual boot loaders."""
from pathlib import Path
import csv, io, json, subprocess, tempfile
R=Path(__file__).resolve().parents[1]
flags=json.loads((R/'assets/full-gameplay-sfx2/preservation.json').read_text())['profile_flags']
defines=[f'-D{k}={17 if v=="B" else v}' for k,v in flags.items()]
with tempfile.TemporaryDirectory(prefix='mf-dual-fx-') as d:
    for dual in (0,1):
        exe=Path(d)/f'fx-{dual}'
        subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',*defines,
                        f'-DMF_ARCADE_FX={dual}','-Itests/sprite_audit','-Isrc',
                        'tests/arcade_fx_test.c','-o',str(exe)],cwd=R,check=True)
        subprocess.run([str(exe)],cwd=R,check=True)
if (R/'build/build-info.h').exists() and '#define MF_ARCADE_FX 1' in (R/'build/build-info.h').read_text():
    rows=[]
    for extra in ([],['--legacy-fx']):
        output=subprocess.check_output(['python3','tools/audit-sprite-memory.py',*extra],cwd=R,text=True)
        rows.append(list(csv.DictReader(io.StringIO(output))))
    dual,legacy=rows
    assert len(dual)==len(legacy)==255
    assert sum(int(r['allocated_bytes']) for r in dual)==452800
    assert sum(int(r['allocated_bytes']) for r in legacy)==453344
    assert dual[1]['path']=='EXPLODE.TGA' and legacy[1]['path']=='BU01.TGA'
    assert int(dual[1]['allocated_bytes'])==2048 and int(legacy[1]['allocated_bytes'])==2592
    for new,old in zip(dual,legacy):
        if new['id']=='1':continue
        for key in ('id','path','width','height','format','allocated_bytes'):
            assert new[key]==old[key],(key,new,old)
    print('PASS real boot loaders: same 255 definitions; only BU01 slot changes; dual=452800, legacy=453344; all other payload dimensions/formats unchanged')
else:
    print('SKIP dual boot-loader comparison: build the complete dual FX profile to stage both allocations')
