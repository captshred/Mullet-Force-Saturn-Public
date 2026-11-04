#!/usr/bin/env python3
"""Exact runtime payloads, hardware-format budgets, and scoped Level 1 source lock."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');args=p.parse_args()
m=json.loads((R/'assets/wingsuit/manifest.json').read_text())
assert m['textures']==6 and m['vdp1_bytes']==7552 and m['tiles']==43
for name,f in m['files'].items():
 b=(R/'assets/wingsuit'/name).read_bytes()
 assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],name
 if args.disc:
  data=subprocess.check_output(['isoinfo','-i',str(R/'build/mullet-force.bin'),'-x','/'+name+';1'])
  assert data==b,(name,'disc payload differs')
assert sum(m['files'][n]['bytes'] for n in ('WBUCK.BIN','WCHUCK.BIN','WDRONE.BIN','WSHOT.BIN','WHOST.BIN','WBOOM.BIN'))==7552
assert m['files']['WCELL.BIN']['bytes']==43*64==2752
assert m['files']['WMAP.BIN']['bytes']==8192
for word in struct.unpack('>4096H',(R/'assets/wingsuit/WMAP.BIN').read_bytes()):
 assert word>>12==1 and not word&1 and (word&4095)//2<43
assert m['vdp2_payload_bytes']==10944<=106496+65536
assert m['cram_bytes']==32 and m['max_sprite_commands']==58
assert 7552<458488 and 6<255
# Every old gameplay/asset check remains active. Only four source integrations
# may differ, each checked against an exact before/after digest.
lock=json.loads((R/'docs/level2-source-lock.json').read_text())
assert lock['base_commit']=='467fc259b2afce35a210db4e10d467c758fced7f'
assert set(lock['updates'])=={'src/main.c','make/saturn.mk','tools/build-native.sh','tools/build.sh'}
for name,u in lock['updates'].items():
 b=(R/name).read_bytes()
 assert hashlib.sha256(b).hexdigest()==u['sha256']['after'],name
 assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==u['blob']['after'],name
source=(R/'src/main.c').read_text()
assert source.index('if(stage2_owned){mf_ws_runtime_frame')<source.index('if(asset_error) {draw_asset_diagnostics();return;}')
assert 'if(!stage2_owned)' in source and 'stage2_owned=1;pending[0]=pending[1]=0;' in source
assert 'mf_ws_runtime_begin(game.players[1].active,&street_palette,now);return;' in source
if args.disc:
 assert (R/'build/wingsuit-mode.txt').read_text().strip()=='1'
 assert 'Level 2 wingsuit: 1' in (R/'build/BUILD-INFO.txt').read_text()
print('PASS wingsuit payloads/budgets: 6 definitions, 7552 VDP1 bytes, 43 tiles, 10944 VDP2 payload bytes, 32 CRAM bytes; exact scoped integration lock')
