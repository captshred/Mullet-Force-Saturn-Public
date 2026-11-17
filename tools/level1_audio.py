"""Private-authoring importer helpers; public builds consume committed SEQ/TON only.

GPIF units/slide flags are interpreted from the format, with alphaTab's GPIF
reader used as an interpretation reference (not bundled or copied).
"""
from pathlib import Path
from fractions import Fraction as F
import xml.etree.ElementTree as ET
import zipfile,struct,math,hashlib,json,collections

PPQN=480
TEMPO=365854
BASE='0242cbb0e92959b27e83aaf7d0ae9c75e135f3a7'
ROUTING={36:'kick',38:'snare',39:'snare',40:'snare',41:'low_tom',43:'low_tom',45:'mid_tom',47:'mid_tom',48:'high_tom',49:'crash',50:'crash',52:'china',53:'ride',55:'crash',57:'crash',59:'ride',60:'open_hat',64:'open_hat'}

def digest(b): return hashlib.sha256(b).hexdigest()
def seconds(tick): return tick*TEMPO/(PPQN*1000000)
def ticks(sec): return round(sec*PPQN*1000000/TEMPO)
def prop(note,name,default=None):
 p=note.get('props',{}).get(name)
 return default if p is None else next(iter(p.values()),default)

def read_gp(path):
 with zipfile.ZipFile(path) as z: root=ET.fromstring(z.read('Content/score.gpif'))
 groups={g:{e.get('id'):e for e in root.find(g)} for g in ('Bars','Voices','Beats','Notes','Rhythms')}
 tempos=root.findall('./MasterTrack/Automations/Automation[Type="Tempo"]')
 assert len(tempos)==1 and tempos[0].findtext('Bar')=='0' and tempos[0].findtext('Value')=='164 2','Unexpected GP tempo map'
 lengths={'Whole':F(4),'Half':F(2),'Quarter':F(1),'Eighth':F(1,2),'16th':F(1,4),'32nd':F(1,8),'64th':F(1,16)}
 at=F(0);rows=[];meters=[]
 for barno,mb in enumerate(root.find('MasterBars')):
  assert mb.find('Repeat') is None,'Repeat expansion requires review'
  num,den=map(int,mb.findtext('Time').split('/'));meters.append((int(at*PPQN),num,den))
  for track,bid in enumerate(mb.findtext('Bars').split()):
   for voice,vid in enumerate(groups['Bars'][bid].findtext('Voices').split()):
    if vid=='-1':continue
    offset=F(0)
    for beatid in groups['Voices'][vid].findtext('Beats').split():
     beat=groups['Beats'][beatid];rh=groups['Rhythms'][beat.find('Rhythm').get('ref')];duration=lengths[rh.findtext('NoteValue')]
     dot=rh.find('AugmentationDot');tup=rh.find('PrimaryTuplet')
     if dot is not None:duration*=2-F(1,2**int(dot.get('count')))
     if tup is not None:duration*=F(int(tup.get('den')),int(tup.get('num')))
     for nid in (beat.findtext('Notes') or '').split():
      n=groups['Notes'][nid];props={p.get('name'):{e.tag:e.text or '' for e in p} for p in n.findall('./Properties/Property')};tie=n.find('Tie')
      rows.append(dict(track=track,voice=voice,bar=barno+1,on=int((at+offset)*PPQN),off=int((at+offset+duration)*PPQN),beat_off=int((at+offset+duration)*PPQN),pitch=int(props['Midi']['Number']),string=int(props['String']['String']),props=props,tie={} if tie is None else tie.attrib,dynamic=beat.findtext('Dynamic'),vibrato=n.findtext('Vibrato'),accent=n.findtext('Accent'),segments=[]))
     offset+=duration
  at+=F(num*4,den)
 active={};notes=[]
 for n in sorted(rows,key=lambda n:(n['on'],n['track'],n['string'])):
  key=(n['track'],n['voice'],n['string'])
  if n['tie'].get('destination')=='true':
   previous=active[key];assert previous['off']==n['on'];previous['off']=n['off'];previous['segments'].append(n)
  else:
   notes.append(n);active[key]=n
 return notes,int(at*PPQN),meters,rows

def peak(intervals):
 value=high=0
 for _,d in sorted([(a,1) for a,b in intervals]+[(b,-1) for a,b in intervals]):value+=d;high=max(high,value)
 return high

def encode_seq(notes,events,end):
 # Direct gated SEQ encoding retains simultaneous duplicate notes without MIDI
 # off-pair ambiguity. Every emitted note owns its own gate; no source mutation.
 output=[];ordinal=0
 def add(t,payload):
  nonlocal ordinal
  output.append((t,ordinal,payload));ordinal+=1
 for c in range(16):
  add(0,bytes([0xb0+c,32,1]));add(0,bytes([0xb0+c,7,112]));add(0,bytes([0xb0+c,11,127]));add(0,bytes([0xe0+c,64]))
 for t,c,kind,value in events:add(t,bytes([kind+c,value]))
 for n in notes:
  # Program/bend/pan immediately precede this attack, including simultaneous
  # notes sharing a percussion channel but selecting different instruments.
  a=n['on'];add(a,bytes([0xc0+n['channel'],n['program']]))
  add(a,bytes([0xb0+n['channel'],10,n.get('pan',64)]))
  add(a,('note',n))
 for c in range(16):add(end,bytes([0xb0+c,123,0]));add(end,bytes([0xe0+c,64]))
 output.sort(key=lambda e:(e[0],e[1]));stream=bytearray([0x82,0]);clock=0;cache={}
 for t,_,payload in output:
  if isinstance(payload,bytes):
   key=(payload[0],payload[1]) if payload[0]&240==176 else (payload[0],)
   if cache.get(key)==payload and t!=end:continue
   cache[key]=payload
  assert clock<=t<=end
  delta=t-clock;clock=t
  for size,code in [(4096,0x8f),(2048,0x8e),(512,0x8d),(256,0x8c)]:
   while delta>=size:stream.append(code);delta-=size
  if isinstance(payload,tuple):
   n=payload[1];gate=n['off']-n['on'];assert gate>0
   for size,code in [(8192,0x8b),(4096,0x8a),(2048,0x89),(512,0x88)]:
    while gate>=size:stream.append(code);gate-=size
   status=n['channel'] | (64 if gate>=256 else 0)
   stream.extend([status,n['pitch'],n['velocity'],gate%256,delta])
  else:stream+=payload+bytes([delta])
 assert clock==end
 stream+=bytes([0x82,0,0x83]);song=struct.pack('>HHHHII',PPQN,1,16,8,end,TEMPO)+stream
 result=struct.pack('>HI',1,8)+b'\0\0'+song
 return result+bytes(-len(result)%4)

def build_ton(samples):
 # Same known-good one-layer TON layout as the existing builder. PCMS is bit4
 # of the packed SCSP loop/address control byte; PCM8 is signed linear PCM.
 count=len(samples);table=8+2*count;mix=bytes(18);velocity=struct.pack('bbBbbBbbBb',25,16,54,9,49,102,19,93,122,43)
 tables=mix+velocity+bytes(10)+bytes(4);voicebase=table+len(tables);pcmbase=(voicebase+36*count+3)&~3
 payload=bytearray();voices=[]
 for s in samples:
  payload+=bytes(-(pcmbase+len(payload))%4);sa=pcmbase+len(payload);s['tone_offset']=sa
  layer=bytearray(32);layer[1]=127;layer[3]=(32 if s['loop'] else 0)|(16 if s['bits']==8 else 0)|(sa>>16);struct.pack_into('>HHH',layer,4,sa&65535,s.get('lsa',0),s['frames'])
  # Instant attack, sustain, fast native release; recorded decay stays in PCM.
  struct.pack_into('>HH',layer,10,31,31);layer[15]=s['tl'];layer[24]=7<<5
  octave=round(12*math.log2(44100/s['rate']));assert s['rate'] in (11025,22050,44100)
  layer[25]=s['root']+octave;assert layer[25]<128
  voices.append(bytes([12,0,0,0])+layer);payload+=s['pcm']
  guard=s['pcm'][s.get('lsa',0)*(s['bits']//8):][:4] if s['loop'] else bytes(4);payload+=guard
 offsets=[table,table+18,table+28,table+38]+[voicebase+36*i for i in range(count)]
 result=struct.pack('>'+str(len(offsets))+'H',*offsets)+tables+b''.join(voices)
 result+=bytes(pcmbase-len(result))+payload
 return result+bytes(-len(result)%4)
