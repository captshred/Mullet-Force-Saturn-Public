#!/usr/bin/env python3
"""Use the approved lossless encoder/storage accounting; keep older previews frozen."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];script=R/'tools/prepare-intersection-detail-complete.py'
s=script.read_text().replace("docs/intersection-detail-complete'", "docs/intersection-facade-seal'")
exec(compile(s,str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
