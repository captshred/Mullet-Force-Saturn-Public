#!/usr/bin/env python3
"""Validate exported runtime payloads against the selected private build snapshot.
Original art/MIDI/WAV fidelity tests are retained in the private authoring repo.
"""
from pathlib import Path
import hashlib,json,subprocess
root=Path(__file__).resolve().parents[1]
locks=json.loads((root/'assets/public-runtime-lock.json').read_text())
for name,entry in locks.items():
 data=(root/name).read_bytes()
 assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'],name
subprocess.run(['python3',str(root/'tools/check-preserved-audio.py')],check=True)
print(f'PASS {len(locks)} exported runtime payloads match the approved runtime locks (SFX2 audio update).')
