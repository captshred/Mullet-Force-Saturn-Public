#!/usr/bin/env python3
"""Decode native TON layer/register words independently of the bank generator.

Sources: Sega ST-235-030795 pp.54-56; ST-077-R2-052594, slot registers.
This is a structural model, not a Saturn driver/emulator/audio execution result.
"""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1]
def word(data,offset):return struct.unpack_from('>H',data,offset)[0]
def decode(data,program,base):
    v=word(data,8+program*2)
    assert data[v+2]==0,'expected one layer'
    layer=v+4
    # Pinned driver 0x38ec..0x3902: add bank base to the layer's packed
    # control/SA longword; copy LSA/LEA and the two EG words verbatim.
    packed=struct.unpack_from('>I',data,layer+2)[0]+base
    control=packed>>16;eg1=word(data,layer+10);eg2=word(data,layer+12)
    return dict(voice_offset=v,layer_offset=layer,control=control,
        lpctl=(control>>5)&3,pcm8b=(control>>4)&1,ssctl=(control>>7)&3,
        sa=packed&0xfffff,lsa=word(data,layer+6),lea=word(data,layer+8),
        ar=eg1&31,eghold=(eg1>>5)&1,d1r=(eg1>>6)&31,d2r=(eg1>>11)&31,
        rr=eg2&31,dl=(eg2>>5)&31,krs=(eg2>>10)&15,lpslnk=(eg2>>14)&1,
        tl=data[layer+15],disdl=data[layer+24]>>5,base_note=data[layer+25]&127,
        fine=struct.unpack_from('b',data,layer+26)[0])
def validate(d):
    assert (d['lpctl'],d['pcm8b'],d['ssctl'])==(1,0,0),'normal looping / PCM16 external DRAM'
    assert (d['sa'],d['lsa'],d['lea'])==(225600,27981,41239),'byte SA; sample-count LSA/LEA'
    assert (d['ar'],d['d1r'],d['d2r'],d['rr'])==(31,0,0,31),'flat held envelope and fast release'
    assert (d['base_note'],d['fine'],d['tl'],d['disdl'])==(60,0,0,7),'unity pitch / audible direct output'
    assert d['sa']%2==0 and d['lsa']<d['lea']<=65535

def main():
    ton=(R/'assets/wingsuit/WDEATH.TON').read_bytes();d=decode(ton,2,148948);validate(d)
    assert (d['voice_offset'],d['layer_offset'])==(128,132)
    pcm=ton[d['sa']-148948:d['sa']-148948+2*d['lea']]
    assert len(pcm)==82478 and hashlib.sha256(pcm).hexdigest()=='977588e18e36c230b227f5cf6bf53d242f6ffa2a9b4427475aaefb43b28620d2'
    # These mutations must fail after decoding actual bank bytes, even when JSON
    # still says 27981/41239. Include endian, byte/sample and disabled-loop errors.
    mutations=[]
    for offset,value in [(135,ton[135]&~0x60),(135,(ton[135]&~0x60)|0x40),
                         (135,(ton[135]&~0x60)|0x60),(138,0),(140,0),
                         (135,ton[135]|0x10),(136,0),(143,0x5f),(142,8)]:
        broken=bytearray(ton);broken[offset]=value;mutations.append(broken)
    for offset in [138,140]:
        broken=bytearray(ton);broken[offset:offset+2]=broken[offset:offset+2][::-1];mutations.append(broken)
    broken=bytearray(ton);broken[138:140]=(27981*2).to_bytes(2,'big');mutations.append(broken)
    for broken in mutations:
        try:validate(decode(broken,2,148948))
        except AssertionError:pass
        else:raise AssertionError('undetected tone mutation')
    # Advance the documented normal-loop cursor for eight seconds. This proves
    # the decoded register model loops, not that a WebRetro slot stays alive.
    pos=wraps=0
    for _ in range(8*44100):
        pos+=1
        if pos>=d['lea']:pos=d['lsa'];wraps+=1
    assert wraps==24 and d['lsa']<=pos<d['lea']
    # Pin the actual driver bytes behind diagnostic offsets and TON -> SCSP copy.
    roots=[R/'.deps/joengine/Compiler/COMMON/SGL_302j/LIB_ELF/SDDRVS.TSK',R/'work/SDDRVS.TSK']
    driver=next((p for p in roots if p.is_file()),None)
    if driver:
        b=driver.read_bytes()
        assert hashlib.sha256(b).hexdigest()=='68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6'
        for addr,hexbytes in {
            0x177e:'4bf9001000004df87000', # SCSP register base / driver work base
            0x17a8:'207c00100408227c00008000', # shared monitor / 64-byte slot records
            0x17da:'3029003a024000c06632', # flags at +3a
            0x17e4:'102800010a40001ce44802400006', # cached live EG mask 6
            0x1812:'3340003a', # store cached EG/held-note flags
            0x38e2:'24533c2a0010294a00082a3900003c8adaaa00022a853b46000e2b6a000600042b6a000a0008'
        }.items():assert b[addr:addr+len(hexbytes)//2]==bytes.fromhex(hexbytes),hex(addr)
        print('PASS pinned driver: packed TON relocation/LSA/LEA/EG copy and read-only slot ownership/cache layout verified')
    else:print('SKIP pinned driver byte audit: driver unavailable; no runtime claim')
    print('PASS native Flame tone: LPCTL=01 normal, PCM16 BE, SA=225600, LSA=27981, LEA=41239, AR31/D1R0/D2R0/RR31; exact PCM; mutation rejection; 24 model wraps in eight seconds (not emulator evidence)')
    print(json.dumps(d,sort_keys=True))
if __name__=='__main__':main()
