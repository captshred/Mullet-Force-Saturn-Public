#!/usr/bin/env python3
"""Run the established actual-transport UBSan/mutation suite at final mix values."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'tools/test-recovered-audio.py';s=p.read_text()
s=s.replace("s=s.replace('word(0x8838", "s=s.replace('b==110','b==127')\ns=s.replace('word(0x8838",1)
s=s.replace('p==0?127','p==0?108').replace('gain127','gain108')
exec(compile(s,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
