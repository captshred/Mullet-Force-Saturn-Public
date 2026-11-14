#!/usr/bin/env python3
"""Use the existing lossless intersection codec; keep historical previews frozen."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];script=R/'tools/prepare-level1-intersection.py'
s=script.read_text().replace("D=R/'docs/level1-intersection-phase3a'", "D=R/'docs/intersection-hotel-detail'")
exec(compile(s,str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
