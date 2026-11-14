#!/usr/bin/env python3
"""Production traversal, with every video frame saved near both review positions."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'tools/test-full-detail-runtime.py';wrapper=p.read_text();scope={'__file__':str(p)};exec(wrapper[:wrapper.index('exec(compile(')],scope)
s=scope['s'].replace('if(frame<1100 || frame%4)return;', 'if(frame<1100 || (frame%4 && !(seen_camera>=1180 && seen_camera<=1240) && !(seen_camera>=1440 && seen_camera<=1500)))return;')
exec(compile(s,str(R/'tools/test-intersection-runtime.py'),'exec'))
