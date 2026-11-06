#!/usr/bin/env python3
"""Stage only the new shooter bank; remove stale root copies on reused builds."""
from pathlib import Path
import json,shutil,sys
R=Path(__file__).resolve().parents[1]
def stage(enabled,root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    names=json.loads((R/'assets/wingsuit/manifest.json').read_text())['files']
    assert len(names)==26 and all(Path(n).name==n and Path(n).suffix in ('.BIN','.SEQ','.TON','.MAP') for n in names)
    for name in names:(root/name).unlink(missing_ok=True)
    dest=root/'ALEVEL2'
    if dest.exists():shutil.rmtree(dest)
    if enabled:
        dest.mkdir()
        for name in names:shutil.copyfile(R/'assets/wingsuit'/name,dest/name)
if __name__=='__main__':
    assert len(sys.argv)==3 and sys.argv[1] in ('0','1')
    stage(sys.argv[1]=='1',Path(sys.argv[2]))
