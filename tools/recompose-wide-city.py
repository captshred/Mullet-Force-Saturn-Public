#!/usr/bin/env python3
"""Idempotently recompose existing 8px cells into a 512px city, without new art.
Left 32 columns remain canonical. Right district reuses rows +128px so the
128px cross-streets still meet, with alternate rooftop detail and no mirroring.
A future art pass can replace any of the 64x64 map cells independently.
"""
from pathlib import Path
import struct,json,hashlib
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit'
p=A/'WMAP.BIN';old=struct.unpack('>4096H',p.read_bytes())
words=[old[((y+(16 if x>=32 else 0))%64)*64+x%32] for y in range(64) for x in range(64)]
b=struct.pack('>4096H',*words);p.write_bytes(b)
p=A/'manifest.json';m=json.loads(p.read_text());m['files']['WMAP.BIN']={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
m['max_sprite_commands']=73 # 72 sprites plus one user-clip command.
p.write_text(json.dumps(m,indent=2)+'\n')
