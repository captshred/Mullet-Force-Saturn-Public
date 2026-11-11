#!/usr/bin/env python3
"""Experimental Level 1 scope gate; approved baseline locks remain unchanged."""
from pathlib import Path
import io, subprocess, sys, tarfile, tempfile
R = Path(__file__).resolve().parents[1]
BASE = '712dbd8e6cb5db4ac3555bed77cb160ec586ee29'
ALLOWED = {'src/game.c', 'src/game.h', 'src/combat_config.h',
           'src/corporate_animation.c', 'tests/corporate_hq_test.c',
           'tests/punk_ai_test.c', 'tools/test-punk-ai.py', 'tools/validate-punk-ai.py'}
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
    # Gameplay/input and stage code share game.c with AI: freeze those regions
    # explicitly rather than granting the entire translation unit an exception.
    old=(ref/'src/game.c').read_text();new=(R/'src/game.c').read_text()
    for start,end in [('static void recover_player(', 'void mf_game_init('),
                      ('static void stage_defeat(', 'static void hit_sound('),
                      ('static void clear_gesture(', 'static void player_hits('),
                      ('static void stage_transition_step(', None),
                      ('if(e->state==MF_ENEMY_ACTIVE){', '        if(--e->timer<=0)')]:
        def region(s):
            value=s.split(start,1)[1]
            return value.split(end,1)[0] if end else value
        assert region(old)==region(new), ('preserved game.c region',start)
    for n in ('.git', '.deps'):
        (ref/n).symlink_to(R/n, target_is_directory=True)
    if '--disc' in sys.argv:
        (ref/'build').symlink_to(R/'build', target_is_directory=True)
    subprocess.run(['python3', 'tools/validate-punk-ai.py',
                    *[x for x in sys.argv[1:] if x in ('--disc', '--test')]], cwd=ref, check=True)
print('PASS AI 3.0 scope: approved AI 2.0 parent and all other baseline files unchanged outside eight reviewed AI/test integrations', flush=True)
if '--test' in sys.argv:
    subprocess.run(['python3', 'tools/test-punk-ai.py'], cwd=R, check=True)
