"""ISO regression: validate physical record order, content, and dirty staging."""
from pathlib import Path
import importlib.util,json,struct,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from wingsuit_disc import validate_disc,directory_records,SECTOR
m=json.loads((R/'assets/wingsuit/manifest.json').read_text())
payloads={n:(R/'assets/wingsuit'/n).read_bytes() for n in m['files']}

def record(name,extent,size,flags=0):
    name=name.encode() if isinstance(name,str) else name
    r=bytearray(33+len(name)+(len(name)%2==0));r[0]=len(r)
    struct.pack_into('<I',r,2,extent);struct.pack_into('>I',r,6,extent)
    struct.pack_into('<I',r,10,size);struct.pack_into('>I',r,14,size)
    r[25]=flags;r[28:32]=b'\x01\0\0\x01';r[32]=len(name);r[33:33+len(name)]=name
    return bytes(r)

def directory(entries):
    out=bytearray()
    for r in entries:
        if len(out)%SECTOR+len(r)>SECTOR:out+=bytes(SECTOR-len(out)%SECTOR)
        out+=r
    out+=bytes((-len(out))%SECTOR);return bytes(out)

def fixture(directory_name='ALEVEL2',root_copy=False,missing=None,corrupt=None):
    image=bytearray(64*SECTOR);root_sector=20;child_sector=40;sector=44
    child=[record(b'\0',child_sector,SECTOR,2),record(b'\1',root_sector,8*SECTOR,2)]
    for name,b in sorted(payloads.items()):
        if name==missing:continue
        b=(bytes([b[0]^1])+b[1:]) if name==corrupt else b
        off=sector*SECTOR;end=off+len(b)
        if end>len(image):image+=bytes(end-len(image))
        image[off:end]=b;child.append(record(name+';1',sector,len(b)));sector+=(len(b)+SECTOR-1)//SECTOR
    child=directory(child);image[child_sector*SECTOR:child_sector*SECTOR+len(child)]=child
    names={f'B{i:03d}.BIN':record(f'B{i:03d}.BIN;1',0,0) for i in range(300)}
    names[directory_name]=record(directory_name,child_sector,len(child),2)
    if root_copy:names['WCELL.BIN']=record('WCELL.BIN;1',44,2752)
    root=directory([record(b'\0',root_sector,8*SECTOR,2),record(b'\1',root_sector,8*SECTOR,2)]+[names[n] for n in sorted(names)])
    image[root_sector*SECTOR:root_sector*SECTOR+len(root)]=root
    image[16*SECTOR:16*SECTOR+7]=b'\x01CD001\x01'
    image[16*SECTOR+156:16*SECTOR+190]=record(b'\0',root_sector,len(root),2)
    return bytes(image)

counts=validate_disc(fixture(),payloads);assert counts==(303,2,26),counts
for kwargs in ({'directory_name':'ZLEVEL2'},{'root_copy':True},{'missing':'WPAL.BIN'},{'corrupt':'WDRONE.BIN'},{'corrupt':'WDEATH.TON'},{'missing':'WDEATH.MAP'}):
    try:validate_disc(fixture(**kwargs),payloads)
    except AssertionError:pass
    else:raise AssertionError(('invalid ISO accepted',kwargs))
# Keep the right name but move the directory record past GFS's table limit.
b=bytearray(fixture());pvd=b[16*SECTOR:17*SECTOR];root=directory_records(b,pvd[156:190])
late=directory(root_r for _,root_r in root[:2]+root[3:]+root[2:3])
b[20*SECTOR:20*SECTOR+len(late)]=late
try:validate_disc(bytes(b),payloads)
except AssertionError as error:assert 'outside the pinned GFS' in str(error)
else:raise AssertionError('late directory accepted')
with tempfile.TemporaryDirectory(prefix='mf-wingsuit-disc-') as tmp:
    root=Path(tmp);(root/'BU00.TGA').write_bytes(b'approved Level 1 sentinel')
    for n in payloads:(root/n).write_bytes(b'stale root copy')
    for enabled in ('1','1','0'):
        subprocess.run([sys.executable,str(R/'tools/stage-wingsuit-assets.py'),enabled,str(root)],check=True)
        assert (root/'BU00.TGA').read_bytes()==b'approved Level 1 sentinel'
        assert not any((root/n).exists() for n in payloads)
        if enabled=='1':
            assert {p.name:p.read_bytes() for p in (root/'ALEVEL2').iterdir()}==payloads
        else:assert not (root/'ALEVEL2').exists()
print('PASS ISO/staging: early ALEVEL2 in 303-record root, exact twenty-four payloads; missing/corrupt/root/late-directory rejection; idempotent staging and Level 1 preservation')
