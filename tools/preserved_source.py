"""Verify this scoped gameplay patch before historical source-lock comparisons.
No art/audio files are overridden. Historical digests remain unchanged.
The active code is tested separately by fast_bat_test and fast_bat_bank_test.
"""
import hashlib,json

def preserved_bytes(root,name):
    data=(root/name).read_bytes()
    for delta in ['assets/punch-combo/source-delta.json','assets/fast-running-bat/source-delta.json']:
        path=root/delta
        if not path.exists():continue
        entry=json.loads(path.read_text())['files'].get(name)
        if entry is None:continue
        digest=hashlib.sha256(data).hexdigest()
        if digest==entry['before_sha256']:continue
        assert digest==entry['after_sha256'],(name,'unreviewed source drift',delta)
        lines=data.decode().splitlines(keepends=True)
        for patch in reversed(entry['edits']):
            a,b=patch['start'],patch['end'];assert lines[a:b]==patch['after']
            lines[a:b]=patch['before']
        data=''.join(lines).encode()
        assert hashlib.sha256(data).hexdigest()==entry['before_sha256'],name
    return data
