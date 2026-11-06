#!/usr/bin/env python3
"""Inspect pinned SH-2 instructions, without executing a Saturn or sound driver."""
from pathlib import Path
import struct,subprocess,hashlib,json,argparse
R=Path(__file__).resolve().parents[1]
def section(b,wanted):
 assert b[:6]==b'\x7fELF\x01\x02'
 off=struct.unpack_from('>I',b,32)[0];size,names,strings=struct.unpack_from('>3H',b,46)
 headers=[struct.unpack_from('>10I',b,off+i*size) for i in range(names)];h=headers[strings];ns=b[h[4]:h[4]+h[5]]
 for h in headers:
  if ns[h[0]:].split(b'\0',1)[0].decode()==wanted:return b[h[4]:h[4]+h[5]]
 raise AssertionError(wanted)
def request(code,form,command,args):
 # Execute the real formatter after its two external flush/handshake calls.
 # The tiny interpreter supports only instructions actually used here.
 regs=[0]*16;regs[15]=0x10000;regs[3]=0x25a004e0;memory={};T=False;pc=0x16;pending=None
 def put(addr,value,n):
  for i in range(n):memory[addr+i]=(value>>(8*(n-i-1)))&255
 def get(addr,n):
  return int.from_bytes(bytes(memory.get(addr+i,0) for i in range(n)),'big')
 for i,b in enumerate(code):memory[i]=b
 fmt=0x20000
 for i,b in enumerate(form.encode()+b'\0'):memory[fmt+i]=b
 for i,v in enumerate([0,fmt,command,*args,0,0,0]):put(regs[15]+4*i,v,4)
 def sx(v,bits):return v-(1<<bits) if v&(1<<(bits-1)) else v
 for _ in range(200):
  op=get(pc,2);prior=pending;pending=None;n=(op>>8)&15;m=(op>>4)&15;next_pc=pc+2
  if op>>12==0xd:regs[n]=get(((pc+4)&~3)+(op&255)*4,4)
  elif op&0xf00f==0x6003:regs[n]=regs[m]
  elif op>>12==7:regs[n]=(regs[n]+sx(op&255,8))&0xffffffff
  elif op&0xf00f==0x6006:regs[n]=get(regs[m],4);regs[m]+=4
  elif op&0xf00f==0x6004:regs[n]=sx(get(regs[m],1),8)&0xffffffff;regs[m]+=1
  elif op&0xf00f==0x2008:T=not(regs[n]&regs[m])
  elif op>>8==0x88:T=regs[0]==(sx(op&255,8)&0xffffffff)
  elif op>>8 in (0x8d,0x8f):pending=pc+4+sx(op&255,8)*2 if T==(op>>8==0x8d) else pc+4
  elif op>>12==0xa:pending=pc+4+sx(op&4095,12)*2
  elif op&0xf00f in (0x2000,0x2001):put(regs[n],regs[m],1 if op&15==0 else 2)
  elif op>>8==0xc9:regs[0]&=op&255
  elif op>>12==0xe:regs[n]=sx(op&255,8)&0xffffffff
  elif op==0x8030:put(regs[3],regs[0],1)
  else:raise AssertionError((hex(pc),hex(op)))
  if pc==0x5a or (prior==0x5c):return regs[0]
  pc=prior if prior is not None else next_pc
 raise AssertionError('formatter did not finish')
def audit():
 roots=[R/'.deps/joengine/Compiler/COMMON/SGL_302j/LIB_ELF',R/'work']
 root=next((p for p in roots if (p/'LIBSGL.A').is_file() and (p/'LIBSND.A').is_file()),None)
 if root is None:return None
 sg=section(subprocess.check_output(['ar','p',str(root/'LIBSGL.A'),'sglG15.o']),'SLPROG')
 snd=section(subprocess.check_output(['ar','p',str(root/'LIBSND.A'),'snd_main.o']),'.text')
 assert sg[0x5a:0x5c]==bytes.fromhex('6023') # MOV R2,R0 on success, not MOV #0,R0.
 results={name:request(sg,fmt,cmd,args) for name,fmt,cmd,args in [('map_change','b',8,[0]),('dsp_stop','',12,[]),('cdda','bb',128,[0,0]),('volume','b',130,[15])]}
 assert set(results.values())=={0x25a00700}
 assert request(sg,'x',8,[0])==0xfffffffe
 assert snd[0xb0:0xc8]==bytes.fromhex('710c6111611d311c66137604621341094108321861233618')
 def copied(words):
  count=words*2;return count+4-count%4
 assert copied(20)==44 and copied(40)==84
 return {'sdk_revision':'556d081146211b6a1cfa6591d70f9487d406758b','slSoundRequest_raw_success':{k:hex(v) for k,v in results.items()},'slSoundRequest_invalid_format_raw':'0xfffffffe','snd_map_size_unit':'16-bit words','map_bytes':40,'map_words':20,'snd_map_copy_bytes':44,'padded_map_buffer_bytes':44,'passing_40_as_word_count_copy_bytes':84,'slSoundRequest_section_sha256':hashlib.sha256(sg).hexdigest(),'snd_main_text_sha256':hashlib.sha256(snd).hexdigest()}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write-receipt',action='store_true');a=p.parse_args();r=audit()
 if r is None:print('SKIP pinned audio binary audit: SDK archives unavailable (not a runtime result)')
 else:
  if a.write_receipt:(R/'docs/level2-audio-e108-sdk-audit.json').write_text(json.dumps(r,indent=2)+'\n')
  else:assert r==json.loads((R/'docs/level2-audio-e108-sdk-audit.json').read_text())
  print('PASS pinned SH-2 binary audit: map request returns raw R0=0x25a00700; old zero-only test rejects success; SND_Init doubles map words and copies 44 bytes for a 40-byte map')
