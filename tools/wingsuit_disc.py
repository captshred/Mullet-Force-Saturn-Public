"""Read primary ISO9660 directory records in their actual on-disc GFS order."""
import struct
SECTOR=2048
DIRECTORY='ALEVEL2'
GFS_LIMIT=256

def directory_records(image,record):
    start=struct.unpack_from('<I',record,2)[0]*SECTOR
    size=struct.unpack_from('<I',record,10)[0]
    assert start+size<=len(image),'directory outside image'
    data=image[start:start+size];pos=0;entries=[]
    while pos<len(data):
        length=data[pos]
        if not length:
            pos=(pos//SECTOR+1)*SECTOR;continue
        assert length>=34 and pos+length<=len(data),'invalid directory record'
        r=data[pos:pos+length];pos+=length
        assert 33+r[32]<=len(r),'invalid ISO identifier'
        raw=r[33:33+r[32]]
        name='.' if raw==b'\0' else '..' if raw==b'\1' else raw.decode('ascii').split(';')[0]
        entries.append((name,r))
    assert len({n for n,_ in entries})==len(entries),'duplicate ISO identifiers'
    return entries

def validate_disc(image,payloads):
    pvd=image[16*SECTOR:17*SECTOR]
    assert pvd[:7]==b'\x01CD001\x01','expected cooked ISO9660 primary descriptor'
    root=directory_records(image,pvd[156:190]);names=[n for n,_ in root]
    assert DIRECTORY in names,'missing /ALEVEL2 directory'
    index=names.index(DIRECTORY)
    assert index<GFS_LIMIT,'/ALEVEL2 is outside the pinned GFS directory table'
    entry=root[index][1];assert entry[25]&2,'/ALEVEL2 is not a directory'
    assert not set(payloads)&set(names),'stale Level 2 files in ISO root'
    child=directory_records(image,entry)
    assert len(child)<=GFS_LIMIT,'Level 2 directory exceeds pinned GFS limit'
    files={n:r for n,r in child if n not in ('.','..')}
    assert set(files)==set(payloads),'Level 2 directory must contain exactly nine assets'
    for name,expected in payloads.items():
        r=files[name];assert not r[25]&2,(name,'asset is a directory')
        offset=struct.unpack_from('<I',r,2)[0]*SECTOR
        size=struct.unpack_from('<I',r,10)[0]
        assert offset+size<=len(image),(name,'payload outside image')
        assert image[offset:offset+size]==expected,(name,'disc payload differs')
    return len(root),index,len(child)
