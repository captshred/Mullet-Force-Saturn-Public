from pathlib import Path
import struct,hashlib,json
r=Path(__file__).resolve().parents[1];o=r/'assets/city-gameplay-parallax';p=(r/'assets/city-cleanup/CIPIX.BIN').read_bytes();lookup={};tiles=[];rows=[]
for y in range(7):
 row=[]
 for x in range(80):
  t=b''.join(p[(y*8+k)*640+x*8:(y*8+k)*640+x*8+8] for k in range(8))
  if t not in lookup:lookup[t]=len(tiles);tiles.append(t)
  row.append(lookup[t])
 rows.append(row)
cells=b''.join(tiles).ljust(32768,b'\0');assert len(cells)+0x4000+16384<=131072 and 512+len(tiles)*2<=4096
mapping=[0x1000|512|(rows[y][page*64+x]*2 if y<7 and page*64+x<80 else 0) for page in range(2) for y in range(64) for x in range(64)]
# Offset is addition, not OR: cell IDs can themselves include bit nine.
mapping=[0x1000|(512+(rows[y][page*64+x]*2 if y<7 and page*64+x<80 else 0)) for page in range(2) for y in range(64) for x in range(64)]
files={'LCSKY.BIN':cells,'LCMAP.BIN':struct.pack('>8192H',*mapping)}
for n,d in files.items():(o/n).write_bytes(d)
(r/'src/live_city_data.h').write_text('#define MF_LIVE_SKY_BYTES %du\n'%len(cells))
(o/'manifest.json').write_text(json.dumps({'sky_bytes':len(cells),'map_bytes':16384,'vdp2_delta':len(cells),'ratio':[1,4],'sha256':{n:hashlib.sha256(d).hexdigest() for n,d in files.items()}},indent=2)+'\n')
print('Sky bytes',len(cells),'total VDP2 reserved',401408+len(cells))
