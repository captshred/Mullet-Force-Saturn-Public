"""Independent strict decoder for validating emitted Sega SEQ (no audio rendering)."""
import struct

def decode(data,song=0):
    count=struct.unpack_from('>H',data)[0]; assert song<count
    p=struct.unpack_from('>I',data,2+song*4)[0]; assert p%2==0
    ppqn,nt,off,loopoff=struct.unpack_from('>HHHH',data,p)
    tempos=[struct.unpack_from('>II',data,p+8+i*8) for i in range(nt)]
    p+=off; tick=0; gate_ext=delta_ext=0; notes=[]; controls=[]; loops=[]; pcs=[]; bends=[]
    while p<len(data):
        b=data[p]; p+=1
        if b==0x83: return dict(ppqn=ppqn,tempos=tempos,tempo_loop_offset=loopoff,notes=notes,controls=controls,loops=loops,programs=pcs,bends=bends,end=tick)
        if b in (0x88,0x89,0x8a,0x8b): gate_ext+={0x88:512,0x89:2048,0x8a:4096,0x8b:8192}[b]; continue
        if b in (0x8c,0x8d,0x8e,0x8f): delta_ext+={0x8c:256,0x8d:512,0x8e:2048,0x8f:4096}[b]; continue
        if b<128:
            n,v,g,d=data[p:p+4]; p+=4
            tick+=d+delta_ext+(256 if b&32 else 0)
            notes.append((tick,tick+g+gate_ext+(256 if b&64 else 0),b&15,n,v))
            gate_ext=delta_ext=0
        elif b==0x82:
            tick+=data[p]+delta_ext; p+=1; delta_ext=0; loops.append(tick)
        elif b&240 in (176,160):
            a,v,d=data[p:p+3];p+=3; tick+=d+delta_ext;delta_ext=0
            controls.append((tick,b&15,a,v))
        elif b&240 in (192,208,224):
            a,d=data[p:p+2];p+=2;tick+=d+delta_ext;delta_ext=0
            (pcs if b&240==192 else bends).append((tick,b&15,a))
        else: raise ValueError(('Unsupported SEQ opcode',hex(b),p))
    raise ValueError('Missing end marker')
