"""Candidate boundaries and preservation mutations, independent of source locks."""
from pathlib import Path
import importlib.util, struct, zipfile
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('neon',R/'tools/build-level2-neon-city.py')
import sys
sys.path.insert(0,str(R/'tools'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assets,counts=m.generate()
for name,data in assets.items():assert (R/'assets/level2-neon-city'/name).read_bytes()==data
with zipfile.ZipFile(R/'downloads/mullet-force-level2-audio-engine-review.zip') as z:base=z.read('mullet-force.bin')
result,ranges=m.patch(base,assets)
assert result!=base
assert len(assets['WCELL.BIN'])//64==578 and len(assets['WROOF.BIN'])//64==194
assert len(assets['WPAL.BIN'])==32
for name in m.NAMES[:2]:
 old=(R/'assets/wingsuit'/name).read_bytes();new=assets[name]
 assert bytes({9:6,15:8}.get(v,v) for v in new)==old
 assert bytes(v==0 for v in old)==bytes(v==0 for v in new)
# Native map addressing: every referenced tile still exists, no geometry change.
for cn,mn,offset in [('WCELL.BIN','WMAP.BIN',0),('WROOF.BIN','WRMAP.BIN',2048)]:
 for word in struct.unpack('>4096H',(R/'assets/wingsuit'/mn).read_bytes()):
  tile=((word&4095)-offset)//2
  assert word>>12==1 and 0<=tile<len(assets[cn])//64
# Corrupt the executable, an unrelated asset, a palette, and image length.
records=m.level2_records(base)
root=dict(m.directory_records(base,base[16*m.SECTOR+156:16*m.SECTOR+190]))
for label,at in [('executable',m.extent(root['0.BIN'])[0]),('sprite',m.extent(records['WBUCK.BIN'])[0]),('map',m.extent(records['WMAP.BIN'])[0]),('palette',m.extent(records['WPAL.BIN'])[0])]:
 bad=bytearray(result);bad[at]^=1
 try:m.validate_candidate(base,bytes(bad),assets)
 except AssertionError:print('PASS preservation mutation rejected:',label)
 else:raise AssertionError(label+' corruption accepted')
try:m.validate_candidate(base,result+b'\0',assets)
except AssertionError:print('PASS preservation mutation rejected: changed image length')
else:raise AssertionError('image growth accepted')
print('PASS exact Level1 colors, reproducible native assets, unchanged tile/map/VRAM footprints, geometry/transparency and entire image outside three background extents')
