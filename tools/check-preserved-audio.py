#!/usr/bin/env python3
"""Read-only check of committed PCM/SEQ/TON/MAP assets; never calls music.py."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];report=json.loads((R/'assets/music/report.json').read_text())
for name,entry in report['outputs'].items():
 data=(R/'assets/cd'/name).read_bytes();assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'],name
print('PASS audio payloads match their report; original PCM and unrelated sounds validated separately.')
