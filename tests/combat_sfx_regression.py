"""Compare all gameplay state against the selected baseline, ignoring new audio tags."""
from pathlib import Path
import subprocess,tempfile,hashlib
R=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    hashes=[]
    for original in [True,False]:
        exe=Path(tmp)/str(original)
        include=R/'tests/combat_sfx_baseline' if original else R/'src'
        src=include/'game.c'
        cmd=['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-DMF_JAB_COHESION=1','-DMF_RUN_BAT=1','-DMF_DASH_ENABLED=1','-DMF_BAT_MOMENTUM=1','-DMF_ATTACK_SEQUENCE=1','-I'+str(include),'-I'+str(R/'src')]
        if original:cmd+=['-DBASELINE=1']
        subprocess.run(cmd+[str(R/'tests/combat_sfx_trace.c'),str(src),'-o',str(exe)],check=True)
        hashes.append(hashlib.sha256(subprocess.check_output([str(exe)])).hexdigest())
    assert hashes[0]==hashes[1],hashes
print('PASS: 16000 input ticks; all gameplay state matches 76f3002 after masking added audio-only tags.')
