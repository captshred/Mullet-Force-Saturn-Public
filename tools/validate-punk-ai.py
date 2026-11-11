#!/usr/bin/env python3
"""Experimental Level 1 scope gate; approved baseline locks remain unchanged."""
from pathlib import Path
import io, subprocess, sys, tarfile, tempfile
R = Path(__file__).resolve().parents[1]
BASE = 'a97aedf614ad9077eb2349f435aaea70ca394811'
ALLOWED = {'Makefile', 'src/game.c', 'src/game.h', 'src/combat_config.h', 'tests/combat_test.c', 'tests/coop_test.c'}
if subprocess.run(['git', 'cat-file', '-e', BASE+'^{commit}'], cwd=R,
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
    subprocess.run(['git', 'fetch', '--no-tags', '--depth=1', 'origin', BASE], cwd=R, check=True)
with tempfile.TemporaryDirectory(prefix='punk-approved-') as d:
    ref = Path(d)
    data = subprocess.check_output(['git', 'archive', BASE], cwd=R)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(ref, filter='data')
    for p in ref.rglob('*'):
        if p.is_file() and str(p.relative_to(ref)) not in ALLOWED:
            assert (R/p.relative_to(ref)).read_bytes() == p.read_bytes(), str(p.relative_to(ref))
    for n in ('.git', '.deps'):
        (ref/n).symlink_to(R/n, target_is_directory=True)
    if '--disc' in sys.argv:
        (ref/'build').symlink_to(R/'build', target_is_directory=True)
    subprocess.run(['python3', 'tools/validate-e008-diagnostic.py',
                    *[x for x in sys.argv[1:] if x in ('--disc', '--test')]], cwd=ref, check=True)
print('PASS AI scope: every approved file outside six reviewed AI/test integrations unchanged; original locks executed on approved source', flush=True)
if '--test' in sys.argv:
    subprocess.run(['python3', 'tools/test-punk-ai.py'], cwd=R, check=True)
