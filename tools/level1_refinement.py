"""Lossless native SEQ event reader/writer for the Level1-only refinement."""
import struct
BASE='a0982c738f78ac7a00bdbd248c1d5ebe299b6971'

def read(data,song=0):
 count=int.from_bytes(data[:2],'big');assert song<count
 start=struct.unpack_from('>I',data,2+song*4)[0]
 ppqn,nt,off,loopoff=struct.unpack_from('>4H',data,start);header=data[start:start+off]
 p=start+off;tick=gate_ext=delta_ext=0;events=[];program=[0]*16;pan=[64]*16;bend=[64]*16
 while True:
  code=data[p];p+=1
  if code==0x83:break
  if code in (0x88,0x89,0x8a,0x8b):gate_ext+={0x88:512,0x89:2048,0x8a:4096,0x8b:8192}[code];continue
  if code in (0x8c,0x8d,0x8e,0x8f):delta_ext+={0x8c:256,0x8d:512,0x8e:2048,0x8f:4096}[code];continue
  if code<128:
   n,v,g,d=data[p:p+4];p+=4;tick+=d+delta_ext+(256 if code&32 else 0);channel=code&15
   e=dict(kind='note',on=tick,off=tick+g+gate_ext+(256 if code&64 else 0),channel=channel,pitch=n,velocity=v,program=program[channel],pan=pan[channel],bend=bend[channel])
   gate_ext=0
  elif code==0x82:
   tick+=data[p]+delta_ext;p+=1;e=dict(kind='loop',on=tick,payload=bytes([code]))
  elif code&240 in (176,160):
   a,v,d=data[p:p+3];p+=3;tick+=d+delta_ext;channel=code&15;e=dict(kind='event',on=tick,payload=bytes([code,a,v]))
   if code&240==176 and a==10:pan[channel]=v
  elif code&240 in (192,208,224):
   v,d=data[p:p+2];p+=2;tick+=d+delta_ext;channel=code&15;e=dict(kind='event',on=tick,payload=bytes([code,v]))
   if code&240==192:program[channel]=v
   if code&240==224:bend[channel]=v
  else:raise ValueError((p,code))
  delta_ext=0;events.append(e)
 return header,events,tick

def write(header,events):
 stream=bytearray();clock=0
 for e in events:
  t=e['on'];assert t>=clock;delta=t-clock;clock=t
  for size,code in [(4096,0x8f),(2048,0x8e),(512,0x8d),(256,0x8c)]:
   while delta>=size:stream.append(code);delta-=size
  if e['kind']=='note':
   gate=e['off']-t;assert gate>0
   for size,code in [(8192,0x8b),(4096,0x8a),(2048,0x89),(512,0x88)]:
    while gate>=size:stream.append(code);gate-=size
   stream+=bytes([e['channel']|(64 if gate>=256 else 0),e['pitch'],e['velocity'],gate%256,delta])
  else:stream+=e['payload']+bytes([delta])
 stream.append(0x83);data=struct.pack('>HI',1,8)+b'\0\0'+header+stream
 return data+bytes(-len(data)%4)

def signature(n):return tuple(n[k] for k in ('on','off','channel','pitch','velocity'))
def peak(notes,release_ticks=0):
 count=high=0
 for _,d in sorted([(n['on'],1) for n in notes]+[(n['off']+release_ticks,-1) for n in notes]):count+=d;high=max(high,count)
 return high

def curve(note,events):
 result=[(0,note['bend'])]
 for e in events:
  if e['kind']=='event' and e['payload'][0]==0xe0+note['channel'] and note['on']<=e['on']<note['off']:result.append((e['on']-note['on'],e['payload'][1]))
 normalized=[]
 for point in result:
  if not normalized or point[1]!=normalized[-1][1]:normalized.append(point)
 return tuple(normalized)
