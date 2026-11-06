#!/usr/bin/env python3
"""Execute the pinned driver's five command-history instructions; no SCSP emulation."""
from pathlib import Path
import hashlib,struct,re
R=Path(__file__).resolve().parents[1]
p=R/'.deps/joengine/Compiler/COMMON/SGL_302j/INC/SDDRVS.TSK'
b=p.read_bytes()
assert len(b)==26610 and hashlib.sha256(b).hexdigest()=='68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6'
assert b[0x1bd4:0x1bea].hex()=='064000103d40183a31c0041a32ae18383d7c00001838'
assert b[0x17a0:0x17a4].hex()=='526e1838' # Interval timer increments in an ISR.
assert b[0x1bbe:0x1bc2].hex()=='024007f0' # ANDI.W #0x7f0,D0: 128-record ring.
for cursor in [0,0x10,0x7f0,0x800]:
 mem=bytearray(65536);a6=0x7000;a1=0x812e;d0=cursor & struct.unpack_from('>H',b,0x1bc0)[0];pc=0x1bd4
 def word(at):return struct.unpack_from('>H',mem,at)[0]
 def put(at,v):struct.pack_into('>H',mem,at,v&65535)
 put(0x8838,3)
 while pc<0x1bea:
  op=struct.unpack_from('>H',b,pc)[0];pc+=2
  def imm():
   global pc
   value=struct.unpack_from('>H',b,pc)[0];pc+=2;return value
  if op==0x0640:d0=(d0+imm())&65535
  elif op==0x3d40:put(a6+imm(),d0)
  elif op==0x31c0:put(imm(),d0)
  elif op==0x32ae:put(a1,word(a6+imm()))
  elif op==0x3d7c:
   value=imm();put(a6+imm(),value)
  else:raise AssertionError(hex(op))
 assert word(0x41a)==word(0x883a)==((cursor&0x7f0)+16)
 assert word(0x8838)==0 and word(a1)==3
# The native driver source itself is not damaged by the added sprites/state.
header=(p.parent/'SDDRVS.DAT').read_text();header=header[header.index('{')+1:header.index('};')]
embedded=bytes(int(v,16) for v in re.findall(r'0x([0-9a-fA-F]{2})',header))
assert embedded[:len(b)]==b and b[-4:]==b'SEGA'
print('PASS pinned 68K execution: dispatcher +0x1bd4 advances exported cursor041a/working883a, logs and clears interval8838, including cursor wrap; timer8838 is NOT a monotonic ready signal; exact26610-byte driver/SEGA signature preserved')
