#!/usr/bin/env python3
"""Pinned 2.10 ownership audit + instruction-level allocator snapshot tests.

Executes the actual 68K allocator's integer/branch instructions, stopping BEFORE
hardware key-on. Not a full CPU/SCSP emulator, not an audible playback test.
"""
from pathlib import Path
import hashlib,struct,importlib.util
R=Path(__file__).resolve().parents[1]
PIN='68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6'
# Reviewed instruction windows; the complete executable is also SHA pinned.
WINDOWS={
0x366a:'1012020000701d4018156600060245fa317252523e2e1824', # poly mode + native note serial
0x38b2:'3039000067ec3940003e', # assign serial to physical slot
0x271a:'48e70060227c00009900347c078070007200740010180c4000076200005ad040d4c0d040d040d040d040d2c0d2c0d2c0e94872001218334100421418', # control gain
0x280e:'48e7ffc022007400760f3c36001a3a2900480a4500804885dc456b080c460100640260044a465ac646067e1f780041ee1000b2704006661eb430400266180830000740346610', # owner/channel gain application

0x2ece:'101912191401024200e0d442d442d442d4423d4218000241001f0c41001064223401eb4ad46e18003d42180a3d4118021419161102400007d040327b00104e914e75',
0x1b14:'0242007f302e180a263600046700004c20437608d642d642b668000064000028302e180a1d82000076003d83000816360001080300066600000a0203007f1d8300018040',
0x378a:'49ee10003c3c001f780072ff74ff3a3900003c86362e1800302c003a670000b80240ffcc66023204b66c000666240240ffc0661e3404302c003a0240ffc86612ba6c0002660648413204484148423404484206440040d8fc004051ceffbc38016a74484138016a6e484238026a68484238026b0e6060103c008c61001e40527807f249ee10007c1f7000720074007800322c003e76000c41100063080c41f00064026006363c8000d2433034203ed043b041651032003034203a0240ffc06604380260120642004051ceffe0103c009961001dea4e75',
0x38c8:'396e18000006323900003c86363900003c883941000219430001',
0x263a:'700010180c4000076200006c327c0781d2c0d2c051d1610000ac61002e7e',
0x54d4:'48e7fffed040d040d040d040d040d040d040d040d0403d4018007e0f7a0008b6000650030645002051cffff47e1f287c000080002a7c001000001c2c00346b0000363c2c0006bc6e18006600002a08ac0003000508ac00010005082c0006000067046100e8881a2d000002050007000500101b450000d8fc0040dafc002051cfffba4cdf7fff',
}
def allocator(code,slots,control,key):
    d=[0]*8;a=[0]*8;a[6]=0x7000;mem=bytearray(0x10000);mem[:len(code)]=code
    def put(at,v):struct.pack_into('>H',mem,at,v&65535)
    def get(at):return struct.unpack_from('>H',mem,at)[0]
    def sx(v):return v-65536 if v&32768 else v
    put(0x8800,control<<9);put(0x3c86,key)
    for i,(owner,chan_note,flags,stamp) in enumerate(slots):
        for off,v in [(6,owner<<9),(2,chan_note),(0x3a,flags),(0x3e,stamp)]:put(0x8000+i*64+off,v)
    pc=0x378a;n=z=c=False;fallback=False
    def flags(v):return bool(v&32768),not(v&65535),False
    def ea(mode,reg):
        nonlocal pc
        if mode==0:return d[reg]&65535
        if mode==5:at=a[reg]+sx(get(pc));pc+=2;return get(at)
        if mode==6:
            ext=get(pc);pc+=2;index=(ext>>12)&7;disp=ext&255;disp=disp-256 if disp&128 else disp
            assert not(ext&0x8800);return get(a[reg]+sx(d[index]&65535)+disp)
        if mode==7 and reg==1:at=(get(pc)<<16)|get(pc+2);pc+=4;return get(at)
        if mode==7 and reg==4:v=get(pc);pc+=2;return v
        raise AssertionError(('EA',mode,reg,hex(pc)))
    for _ in range(3000):
        if pc==0x3860:return (d[4]&65535)//64,fallback
        if pc==0x3856:return None,True
        if pc==0x380c:fallback=True
        origin=pc;op=get(pc);pc+=2
        if op==0x49ee:a[4]=a[6]+sx(get(pc));pc+=2
        elif op&0xf100==0x7000:
            value=op&255;d[(op>>9)&7]=(value-256 if value&128 else value)&0xffffffff;n,z,c=flags(value if value<128 else value|0xff00)
        elif op&0xfff8==0x4840:
            r=op&7;d[r]=((d[r]<<16)|(d[r]>>16))&0xffffffff;n,z,c=flags(d[r]&65535)
        elif op>>12==3:
            r=(op>>9)&7;assert ((op>>6)&7)==0
            value=ea((op>>3)&7,op&7);d[r]=(d[r]&0xffff0000)|value;n,z,c=flags(value)
        elif op&0xfff8==0x0240:
            r=op&7;value=get(pc);pc+=2;d[r]=(d[r]&0xffff0000)|((d[r]&value)&65535);n,z,c=flags(d[r])
        elif op&0xfff8==0x0640:
            r=op&7;value=get(pc);pc+=2;v=(d[r]&65535)+value;d[r]=(d[r]&0xffff0000)|(v&65535);n,z,c=flags(v);c=v>65535
        elif op==0xd8fc:a[4]+=sx(get(pc));pc+=2
        elif op&0xf1c0==0xb040:
            r=(op>>9)&7;v=ea((op>>3)&7,op&7);lhs=d[r]&65535;n,z,c=flags(lhs-v);c=lhs<v
        elif op&0xfff8==0x0c40:
            r=op&7;v=get(pc);pc+=2;lhs=d[r]&65535;n,z,c=flags(lhs-v);c=lhs<v
        elif op&0xf1f8==0xd040:
            r=(op>>9)&7;v=(d[r]&65535)+(d[op&7]&65535);d[r]=(d[r]&0xffff0000)|(v&65535);n,z,c=flags(v);c=v>65535
        elif op&0xfff8==0x51c8:
            r=op&7;disp=sx(get(pc));d[r]=(d[r]&0xffff0000)|((d[r]-1)&65535)
            pc=pc+disp if d[r]&65535!=65535 else pc+2
        elif op>>12==6:
            cc=(op>>8)&15;disp=op&255
            if not disp:disp=sx(get(pc));base=pc;pc+=2
            else:disp=disp-256 if disp&128 else disp;base=pc
            take={0:True,3:c or z,4:not c,5:c,6:not z,7:z,10:not n,11:n}[cc]
            if take:pc=base+disp
        else:raise AssertionError((hex(origin),hex(op)))
    raise AssertionError('allocator did not terminate')
def main():
    roots=[R/'.deps/joengine/Compiler/COMMON/SGL_302j/LIB_ELF/SDDRVS.TSK',R/'work/SDDRVS.TSK']
    path=next((p for p in roots if p.is_file()),None)
    if path is None:
        print('SKIP native allocator execution: pinned driver unavailable (structural guards still run)');return
    b=path.read_bytes();assert hashlib.sha256(b).hexdigest()==PIN
    for at,h in WINDOWS.items():assert b[at:at+len(h)//2]==bytes.fromhex(h),hex(at)
    assert struct.unpack_from('>8H',b,0x2f1a)==(0x3cac,0x3574,0x2f92,0x2faa,0x1b14,0x2f9a,0x3480,0x2fa2)
    # Context stored by native dispatcher: ctrl<<9 + MIDI-channel<<5.
    contexts=[(p<<9)+(p<<5) for p in range(8)];assert len(set(contexts))==8
    slots=[(0,0,0,0)]*32
    for p in range(8):
        chosen,fallback=allocator(b,slots,p,(p<<8)|60);assert chosen==p and not fallback
        slots[p]=(p,(p<<8)|60,0xa,p+1)
    # Same note AND same control still prefers a completely free physical slot.
    assert allocator(b,slots,4,0x43c)==(8,False)
    # Finite sounds can leave held-key flag8 after EG falls to0. Exercise 2000
    # allocations; a lease means each reused control's prior sample has ended.
    steals=0;peak=0;slots=[(0,61,0xa,1),(1,0x13d,0xa,2)]+[(0,0,0,0)]*30
    for tick in range(2000):
        p=2+tick%6
        slots=[(o,k,8 if o==p else f,t) for o,k,f,t in slots]
        chosen,fallback=allocator(b,slots,p,(p<<8)|60);assert chosen is not None and chosen>=2 and not fallback
        steals+=bool(slots[chosen][2]&6)
        slots[chosen]=(p,(p<<8)|60,0xa,tick+1)
        peak=max(peak,sum(bool(s[2]&6) for s in slots))
    assert not steals and peak==8
    # Deliberately saturate all32 audible slots: native global fallback can steal.
    full=[(i%8,((i%8)<<8)|60,0xa,i+1) for i in range(32)]
    chosen,fallback=allocator(b,full,4,0x43c);assert chosen is not None
    assert full[chosen][0]==4 # same-control fallback, no protection promise at saturation
    global_full=[(0,60,0xa,i+1) for i in range(32)]
    chosen,fallback=allocator(b,global_full,4,0x43c)
    assert chosen is not None and fallback and global_full[chosen][2]&6
    protected=[(0,60,0xffca,i+1) for i in range(32)]
    assert allocator(b,protected,4,0x43c)==(None,True)
    # Actual bank uses single-layer polyphonic play mode0, no modulation slots.
    spec=importlib.util.spec_from_file_location('tone',R/'tools/validate-flame-tone.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    ton=(R/'assets/wingsuit/WDEATH.TON').read_bytes()
    for program in range(4):
        v=mod.decode(ton,program,148948);assert ton[v['voice_offset']]==0 and ton[v['voice_offset']+2]==0
        assert ton[v['layer_offset']+14]&0xf0==0,'no modulation slots'
    print('PASS pinned 2.10: distinct control/channel contexts, free-first actual allocator execution, same-note polyphony, held-key reuse over2000 allocations with two persistent Flames + six one-shots / peak8 / zero active replacements; saturation CAN steal, not exercised by normal leases; tone poly mode0/single layer/no modulation')
if __name__=='__main__':main()
