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
def validate(d,loop):
    assert (d['lpctl'],d['pcm8b'],d['ssctl'])==(int(loop),0,0),'PCM16 external DRAM / exact loop mode'
    assert (d['sa'],d['lsa'],d['lea'])==((281592,0,12832) if loop else (225640,0,27975)),'byte SA; exclusive sample-count LEA'
    assert (d['ar'],d['d1r'],d['d2r'],d['rr'],d['dl'])==(31,0,0,31,0),'flat held envelope and fast release'
    assert (d['base_note'],d['fine'],d['tl'],d['disdl'])==(61 if loop else 60,0,0,7),'unity pitch / audible direct output'
    assert d['sa']%4==0 and d['lsa']<d['lea']<=65535

def main():
    ton=(R/'assets/wingsuit/WDEATH.TON').read_bytes()
    for program,loop,frames,digest in [(2,False,27975,'9e62074cf628c6c4611a488bb2afa0c8e4b29f034cbd2e4a093258a4e6479676'),(3,True,12832,'effcb354cef8271d53590c298c5f32b9df29946a29e203582988941d88c0122d')]:
        d=decode(ton,program,148948);validate(d,loop);a=d['sa']-148948;v=d['voice_offset']
        pcm=ton[a:a+2*frames];assert len(pcm)==2*frames and hashlib.sha256(pcm).hexdigest()==digest
        if loop:assert ton[a+2*frames:a+2*frames+4]==pcm[:4],'SA+LEA cyclic guard equals SA+LSA'
        mutations=[]
        for offset,value in [(v+7,(ton[v+7]&~0x60)|(0 if loop else 0x20)),(v+7,ton[v+7]|0x10),(v+8,0),(v+15,0x5f),(v+14,8)]:
            broken=bytearray(ton);broken[offset]=value;mutations.append(broken)
        for value in [frames-1,(frames*2)&65535]:
            broken=bytearray(ton);struct.pack_into('>H',broken,v+12,value);mutations.append(broken)
        broken=bytearray(ton);struct.pack_into('>H',broken,v+10,1);mutations.append(broken)
        broken=bytearray(ton);broken[v+12:v+14]=broken[v+12:v+14][::-1];mutations.append(broken)
        for broken in mutations:
            try:validate(decode(broken,program,148948),loop)
            except AssertionError:pass
            else:raise AssertionError(('undetected tone mutation',program))
        pos=wraps=0;alive=True
        for _ in range(10*44100):
            if not alive:continue
            pos+=1
            if pos>=d['lea']:
                if loop:pos=d['lsa'];wraps+=1
                else:alive=False
        if loop:assert alive and wraps==34 and 0<=pos<frames
        else:assert not alive and pos==frames and not wraps
    # Pin the actual driver bytes behind diagnostic offsets and TON -> SCSP copy.
    roots=[R/'.deps/joengine/Compiler/COMMON/SGL_302j/LIB_ELF/SDDRVS.TSK',R/'work/SDDRVS.TSK']
    driver=next((p for p in roots if p.is_file()),None)
    if driver:
        b=driver.read_bytes()
        assert hashlib.sha256(b).hexdigest()=='68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6'
        for addr,hexbytes in {
            0x17a0:'526e1838', # live timer heartbeat at sound-RAM 0x8838
            0x10e2:'207c000007007e07', # eight 16-byte command blocks
            0x110c:'30bc0000', # consumer acknowledges by clearing command word
            0x177e:'4bf9001000004df87000', # SCSP register base / driver work base
            0x17a8:'207c00100408227c00008000', # shared monitor / 64-byte slot records
            0x17da:'3029003a024000c06632', # flags at +3a
            0x17e4:'102800010a40001ce44802400006', # cached live EG mask 6
            0x1812:'3340003a', # store cached EG/held-note flags
            0x38e2:'24533c2a0010294a00082a3900003c8adaaa00022a853b46000e2b6a000600042b6a000a0008'
        }.items():assert b[addr:addr+len(hexbytes)//2]==bytes.fromhex(hexbytes),hex(addr)
        print('PASS pinned driver: packed TON relocation/LSA/LEA/EG copy and read-only slot ownership/cache layout verified')
    else:print('SKIP pinned driver byte audit: driver unavailable; no runtime claim')
    print('PASS split native tones: Attack PCM16/27975 frames/LPCTL00; Loop PCM16/12832 frames/LSA0/LEA12832 exclusive/LPCTL01/flat envelope; exact PCM and cyclic guard; mutated mode/format/address/endian/envelope rejection; ten-second cursor model (not emulator evidence)')
if __name__=='__main__':main()
