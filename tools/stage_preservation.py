"""Narrow, hash-pinned source exceptions for the Level 1 milestone; assets stay locked."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
ALLOWED={'src/game.c','src/game.h','src/main.c','make/saturn.mk','tools/build-native.sh','tools/build.sh'}
def stage_digest(name, baseline, kind):
    lock=json.loads((R/'docs/level1-source-lock.json').read_text())
    assert lock['base_commit']=='8d79a36f97dfd0b02de7d1b6b58e85b16fdc0b96'
    assert set(lock['updates'])==ALLOWED
    if name=='tools/check-city-cleanup.py':
        # Permit only the stage-aware lock lookup; verify every other byte
        # against the original preservation digest rather than bypassing it.
        data=(R/name).read_bytes()
        original=data.replace(b'from stage_preservation import stage_digest\n',b'').replace(
            b"==stage_digest(n,h,'sha256'),n",b'==h,n')
        def digest(value):
            return hashlib.sha256(value).hexdigest() if kind=='sha256' else hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()
        assert digest(original)==baseline,(name,'unexpected validator change')
        return digest(data)
    if name=='README.md':
        # Level 2 adds a documented build section. Pin its complete Git blob
        # instead of broadly exempting README from the approved source locks.
        path=R/'docs/level2-source-lock.json'
        if not path.exists():return baseline
        integration=json.loads(path.read_text())
        assert integration['base_commit']=='467fc259b2afce35a210db4e10d467c758fced7f'
        assert baseline=={'sha256':'c733fcee4bc84589dca10c74a286e9050ddd4692d35785938ad33e9ee987113c',
                          'blob':'2a5ca887ec8d0d402f3aa676b1d0ac59c88eb688'}[kind],(name,'unexpected README baseline')
        data=(R/name).read_bytes()
        actual_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert actual_blob=='805c59bf3145e841ea272c7f4ebfd64774f152ac',(name,'unexpected README content')
        return hashlib.sha256(data).hexdigest() if kind=='sha256' else actual_blob
    if name in {'src/input.c','src/input.h'}:
        scoped=json.loads((R/'docs/flame-input-lock.json').read_text())
        assert set(scoped)=={'src/input.c','src/input.h'}
        assert scoped[name][kind]['before']==baseline,(name,'unexpected input baseline')
        return scoped[name][kind]['after']
    if name not in ALLOWED:return baseline
    change=lock['updates'][name][kind]
    assert change['before']==baseline,(name,'unexpected source baseline')
    value=change['after']
    path=R/'docs/level2-source-lock.json'
    if path.exists():
        integration=json.loads(path.read_text())
        assert integration['base_commit']=='467fc259b2afce35a210db4e10d467c758fced7f'
        assert set(integration['updates'])=={'src/main.c','make/saturn.mk','tools/build-native.sh','tools/build.sh'}
        if name in integration['updates']:
            scoped=integration['updates'][name][kind]
            assert scoped['before']==value,(name,'unexpected Level 2 baseline')
            value=scoped['after']
    return value
