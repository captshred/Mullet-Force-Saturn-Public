#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
def validate_hit(original):
 b=(R/'assets/wingsuit/WDEATH.TON').read_bytes();r=json.loads((R/'assets/wingsuit/new-hit.json').read_text());start=31884
 expected=bytearray(original);expected[106:108]=(18798).to_bytes(2,'big');expected[start:start+44806]=b[start:start+37596]+bytes(7210)
 assert b==expected,'only Hit end frame and Hit allocation may change'
 assert hashlib.sha256(b[start:start+37596]).hexdigest()==r['pcm_sha256']
 assert hashlib.sha256(b).hexdigest()==r['tone_sha256'] and len(b)==158312
 assert r['source_sha256']=='601f85a59b5284cb4cb09fc37be29396ec573b1b9bb194201962d55e1b584b4d'
 assert r['frames']==18798 and r['pcm_bytes']==37596 and r['pcm_address']==180832
 print('PASS new Hit only: 18798 mono PCM16 frames at180832; end-frame update; 7210 obsolete PCM bytes zeroed; all other bank bytes unchanged')
 return b
