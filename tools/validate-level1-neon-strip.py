#!/usr/bin/env python3
"""Phase 2 indexed art/cache validation and immutable approved gameplay suites."""
from pathlib import Path
import argparse,hashlib,importlib.util,io,json,re,struct,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];O=R/'assets/level1-neon-strip';BASE='0de58676e2cb703f6e68552cc46ca0ec03809110'
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args()
def sha(b):return hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('bg',R/'tools/validate-level1-background-touchups.py');bg=importlib.util.module_from_spec(spec);spec.loader.exec_module(bg);bg.validate(a.disc)
m=json.loads((O/'manifest.json').read_text());assert m['parent']==BASE and (m['width'],m['height'])==(1280,240)
for n,h in m['sha256'].items():assert sha((O/n).read_bytes())==h,n
assert sha((O/'SOURCE555.BIN').read_bytes())==m['source_sha256']
pixels=(O/'NSPIX.BIN').read_bytes();old=(R/'assets/city-cleanup/CIPIX.BIN').read_bytes();assert len(pixels)==1280*240
for y in range(240):assert pixels[y*1280:y*1280+640]==old[y*640:(y+1)*640],y
pal=struct.unpack('>255H',(O/'NSPAL.BIN').read_bytes());before=struct.unpack('>255H',(R/'assets/city-cleanup/CIPAL.BIN').read_bytes())
used=set(old)|set((R/'assets/city-gameplay-parallax/LCSKY.BIN').read_bytes())|set((R/'assets/city-cleanup/CISKY.BIN').read_bytes())
for i in used:
 if i:assert pal[i-1]==before[i-1],('original color changed',i)
assert pal[239:247]==before[239:247] and m['new_palette_indices']==[i for i in range(1,256) if i not in used]
cells=(O/'NSCELL.BIN').read_bytes();assert len(cells)==m['tile_count']*64==m['source_cell_bytes'];assert cells[:106496]==(R/'assets/city-cleanup/CICELL.BIN').read_bytes()
assert len(set(cells[i:i+64] for i in range(0,len(cells),64)))==m['tile_count']
chunks=struct.unpack('>4800H',(O/'NSMAP.BIN').read_bytes());assert max(chunks)<m['tile_count']<4096
for y in range(30):
 for x in range(160):
  tile=chunks[(x//16*30+y)*16+x%16];decoded=cells[tile*64:(tile+1)*64]
  assert decoded==b''.join(pixels[(y*8+dy)*1280+x*8:(y*8+dy)*1280+x*8+8] for dy in range(8))
assert m['resident_tiles']==1664 and m['resident_cell_bytes']==106496 and m['map_bytes']==16384 and m['VDP2_delta_bytes']==0 and m['VDP2_reserved_bytes']==434176
assert m['extra_cram_banks']==m['extra_VDP1_bytes']==m['extra_SCSP_bytes']==0
# Static allocations plus code/data must leave a conservative 64KiB high-WRAM
# guard. This complements actual emulator boots instead of assuming CPU is free.
maptext=(R/'build/game.map').read_text();end=int(re.search(r'0x([0-9a-f]+)\s+__bend =',maptext).group(1),16);assert end<0x060f0000,hex(end)
if a.disc:
 for name in ('NSCELL.BIN','NSMAP.BIN','NSPAL.BIN'):assert (R/'build/cd'/name).read_bytes()==(O/name).read_bytes()
print(f'PASS Phase 2: exact opening/used colors/neon/skyline; {m["tile_count"]} lossless unique source tiles / 1664 resident, zero VDP2/VDP1/CRAM/SCSP allocation delta; BSS/data end {end:#x} below guarded {0x060f0000:#x}',flush=True)
subprocess.run(['python3','tools/test-level1-neon-strip.py'],cwd=R,check=True)
if a.test:
 frozen={f:f.read_bytes() for f in O.glob('*.BIN')};frozen[O/'manifest.json']=(O/'manifest.json').read_bytes();frozen[R/'src/neon_strip_data.h']=(R/'src/neon_strip_data.h').read_bytes()
 subprocess.run(['python3','tools/prepare-level1-neon-strip.py'],cwd=R,check=True);assert all(f.read_bytes()==b for f,b in frozen.items()),'non-deterministic indexed conversion'
 subprocess.run(['python3','tools/test-ricky-jump-render.py'],cwd=R,check=True)
 subprocess.run(['python3','tools/validate-fire-hit.py'],cwd=R,check=True)
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='neon-approved-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 allowed={'.gitattributes','Makefile','src/parallax.c','src/city_neon.h','src/main.c','tools/build-native.sh'}
 for f in ref.rglob('*'):
  if f.is_file() and str(f.relative_to(ref)) not in allowed:assert (R/f.relative_to(ref)).read_bytes()==f.read_bytes(),f.relative_to(ref)
 assert (R/'.gitattributes').read_text()==(ref/'.gitattributes').read_text()+'\n# Phase 2 indexed colors may contain CR/LF without any NUL.\nassets/level1-neon-strip/*.BIN binary\n'
 assert (R/'src/main.c').read_text()==(ref/'src/main.c').read_text().replace('"TEMP STREET"','"NEON STRIP "'),'only HUD art label may change'
 # The non-live preview and parallax ratios/windows remain byte-identical.
 oldp=(ref/'src/parallax.c').read_text();newp=(R/'src/parallax.c').read_text();assert oldp[oldp.index('#elif MF_PARALLAX_DEMO'):]==newp[newp.index('#elif MF_PARALLAX_DEMO'):]
 for n in ('.git','.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
 subprocess.run(['python3','tools/validate-ricky-jump-chain.py',*(['--test'] if a.test else [])],cwd=ref,check=True)
print('PASS approved jump-chain/gameplay/world/spawns/character/audio/Level2 byte preservation and original suites; only background/cache/palette routing plus HUD label changed')
