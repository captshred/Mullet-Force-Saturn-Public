"""Narrow, hash-pinned source exceptions for the Level 1 milestone; assets stay locked."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
ALLOWED={'src/game.c','src/game.h','src/main.c','make/saturn.mk','tools/build-native.sh','tools/build.sh'}
def stage_digest(name, baseline, kind):
    lock=json.loads((R/'docs/level1-source-lock.json').read_text())
    assert lock['base_commit']=='8d79a36f97dfd0b02de7d1b6b58e85b16fdc0b96'
    assert set(lock['updates'])==ALLOWED
    if name not in ALLOWED:return baseline
    change=lock['updates'][name][kind]
    assert change['before']==baseline,(name,'unexpected source baseline')
    return change['after']
