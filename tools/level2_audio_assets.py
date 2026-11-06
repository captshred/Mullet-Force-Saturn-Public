"""Build the split Flame bank from private split WAVs and committed Shot PCM.

Public builds use the committed bank. No original WAV/archive is published.
"""
from pathlib import Path
import struct,hashlib,json,wave,io,zipfile
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit'
def digest(b):return hashlib.sha256(b).hexdigest()
def rounded(n,d=2):return (n+d//2)//d if n>=0 else -((-n+d//2)//d)
def voice(data,i):
 off=struct.unpack_from('>H',data,8+2*i)[0];v=bytearray(data[off:off+36]);sa=((v[7]&15)<<16)|int.from_bytes(v[8:10],'big');n=int.from_bytes(v[12:14],'big')*2
 return v,data[sa:sa+n]
def seam_metrics(x,a,b):
 end=len(x)-b
 return dict(trim_start=a,trim_end=b,frames=end-a,first=x[a],last=x[end-1],
             jump=x[a]-x[end-1],left_slope=x[end-1]-x[end-2],right_slope=x[a+1]-x[a],
             slope_difference=(x[a+1]-x[a])-(x[end-1]-x[end-2]))
def prepare_loop(x):
 # Search the nearby authoring window, rather than trusting a suggested cut.
 # At most 8 PCM16 counts of endpoint/slope error; preserve direction, then
 # choose the least trimming. A 4-byte cyclic lookahead is stored separately.
 candidates=[]
 for a in range(257):
  for b in range(513):
   m=seam_metrics(x,a,b)
   if abs(m['jump'])<=8 and abs(m['slope_difference'])<=8 and m['left_slope']*m['right_slope']>0:candidates.append(m)
 assert candidates,'no sufficiently clean nearby seam'
 m=min(candidates,key=lambda m:(m['trim_start']+m['trim_end'],abs(m['jump'])+abs(m['slope_difference']),m['trim_start']))
 return x[m['trim_start']:len(x)-m['trim_end']],dict(m,raw=seam_metrics(x,0,0),search_start=[0,256],search_end=[0,512],max_endpoint_error=8,max_slope_error=8,candidates=len(candidates),crossfade_frames=0)
def import_bank(archive):
 z=zipfile.ZipFile(archive);oldreport=json.loads((A/'audio.json').read_text());sources={'Shot.wav':oldreport['sources']['Shot.wav']};pcm=[]
 for name,frames,expected in [('Flame attack.wav',27975,'bfc55dc8ae2e4fed1362cf6ff60402ad42d61d018f704818010baac9c5615866'),('Flame loop.wav',13256,'222fd540adb224c11186ac07188957a086c0bc211b93e60916773283425274a5')]:
  names=[n for n in z.namelist() if Path(n).name==name and '__MACOSX' not in n];assert len(names)==1
  raw=z.read(names[0]);assert digest(raw)==expected
  with wave.open(io.BytesIO(raw)) as w:
   assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes(),w.getcomptype())==(2,2,44100,frames,'NONE')
   vals=struct.unpack('<'+str(frames*2)+'h',w.readframes(frames))
  mono=[rounded(vals[i]+vals[i+1]) for i in range(0,len(vals),2)]
  info=dict(source_sha256=expected,source_frames=frames,source_rate=44100,source_channels=2,rate=44100,bits=16,channels=1,downmix='nearest integer (L+R)/2, symmetric ties away from zero; no resample or gain change',before_seam_sha256=digest(struct.pack('>'+str(frames)+'h',*mono)))
  if name=='Flame loop.wav':mono,seam=prepare_loop(mono);info.update(seam=seam,loop_start=0,loop_end=len(mono),lea_convention='exclusive sample count; cyclic guard at LEA duplicates LSA',guard_frames=2)
  b=struct.pack('>'+str(len(mono))+'h',*mono);info.update(frames=len(mono),pcm_bytes=len(b),pcm_sha256=digest(b),peak=max(map(abs,mono)))
  sources[name]=info;pcm.append(b)
 old=(R/'assets/cd/FX.TON').read_bytes();expl,explpcm=voice(old,2)
 shot,shotpcm=voice((A/'WDEATH.TON').read_bytes(),1)
 assert digest(shotpcm)=='dc25ce5eead8a8ed620e44c0cdc9ca47dbadb8b647cf9a5a86dc241b74232de2'
 offsets=struct.unpack_from('>4H',old);firstvoice=struct.unpack_from('>H',old,8)[0]
 tables=[old[offsets[i]:offsets[i+1] if i<3 else firstvoice] for i in range(4)]
 assert list(map(len,tables))==[18,10,10,4]
 hdr=8+4*2;new_offsets=[];p=hdr
 for b in tables:new_offsets.append(p);p+=len(b)
 vos=[p+i*36 for i in range(4)];base=p+144
 voices=[expl,shot,bytearray(expl),bytearray(expl)];samples=[explpcm,shotpcm,*pcm];payload=bytearray();sample_info=[]
 roles=['explosion','shot','flame_attack','flame_loop'];toneaddr=148948
 for i,(v,b) in enumerate(zip(voices,samples)):
  payload+=bytes((-(base+len(payload)))%4);sa=base+len(payload)
  if i<2:
   v[7]=(v[7]&0xf0)|(sa>>16);v[8:10]=(sa&65535).to_bytes(2,'big')
  else:
   # Layer control/SA is a packed big-endian longword; LSA/LEA are samples.
   struct.pack_into('>I',v,6,((1 if i==3 else 0)<<21)|sa)
   struct.pack_into('>HHHH',v,10,0,len(b)//2,0x001f,0x001f)
   v[29]=61 if i==3 else 60 # Different keys allow the tiny transition overlap.
  sample_info.append(dict(voice=i,role=roles[i],voice_offset=vos[i],layer_offset=vos[i]+4,tone_offset=sa,scsp_addr=toneaddr+sa,bytes=len(b),frames=len(b)//2,rate=22050 if i==0 else 44100,sha256=digest(b),loop=i==3,lsa=0,lea=len(b)//2,base_note=v[29],guard_frames=2 if i==3 else 0))
  payload+=b
  if i==3:payload+=b[:4] # Interpolation guard at SA+LEA equals SA+LSA.
 ton=struct.pack('>8H',*new_offsets,*vos)+b''.join(tables)+b''.join(voices)+payload;ton+=bytes(-len(ton)%4)
 seq=(A/'WDEATH.SEQ').read_bytes();assert len(seq)==84 and digest(seq)=='3672e4b1aa681bbe1dec774086fc4f6b8488e6e3be9bec352f869c94246e7c63'
 seqaddr=148864
 def entry(t,addr,n):return bytes([t<<4])+addr.to_bytes(3,'big')+b'\x80'+n.to_bytes(3,'big')
 mp=(R/'assets/cd/CUSTOM.MAP').read_bytes()[:16]+entry(1,seqaddr,len(seq))+entry(0,toneaddr,len(ton))+b'\xff'*8
 files={}
 for n,b in [('WDEATH.MAP',mp),('WDEATH.SEQ',seq),('WDEATH.TON',ton)]:
  (A/n).write_bytes(b);files[n]={'bytes':len(b),'sha256':digest(b)}
 report=dict(architecture='split Flame Attack one-shot -> dedicated whole-sample hardware loop',canonical='assets/cd/FX.TON voice 2 / FX.SEQ song 2 / MF_WORLD_IMPACT',sources=sources,samples=sample_info,tables=dict(zip(['mixer','velocity','peg','plfo'],new_offsets)),seq_addr=seqaddr,tone_addr=toneaddr,scsp_high_water=toneaddr+len(ton),reserved_before_seq=seqaddr,scsp_free=524288-toneaddr-len(ton),files=files,shot_guard_ticks=34,explosion_guard_ticks=49,sdk_sequence_controls=8,physical_slots=32,attack_to_loop_ticks=38,attack_note=60,loop_note=61,controls={'flame':[0,1],'shot':[2,3],'explosion':[4,5,6,7]})
 (A/'audio.json').write_text(json.dumps(report,indent=2)+'\n')
 flame_report=dict(report);flame_report['files']={n:v for n,v in json.loads((A/'flame-audio.json').read_text())['files'].items() if n.startswith(('WFL','WFO'))};flame_report['files'].update(files)
 (A/'flame-audio.json').write_text(json.dumps(flame_report,indent=2)+'\n')
 h='#ifndef MF_WS_AUDIO_DATA_H\n#define MF_WS_AUDIO_DATA_H\n'
 constants=[('SEQ_BYTES',len(seq)),('TON_BYTES',len(ton)),('MAP_BYTES',len(mp)),('SEQ_ADDR',seqaddr),('TON_ADDR',toneaddr),('SHOT_TICKS',34),('EXP_TICKS',49),('SHOT_VOLUME',96),('FLAME_VOLUME',80),('FLAME_HANDOFF_TICKS',38)]
 for i,label in [(2,'ATTACK'),(3,'LOOP')]:
  x=sample_info[i];constants.extend([(f'FLAME_{label}_PROGRAM',i),(f'FLAME_{label}_LAYER_ADDR',toneaddr+vos[i]+4),(f'FLAME_{label}_PCM_ADDR',x['scsp_addr']),(f'FLAME_{label}_FRAMES',x['frames']),(f'FLAME_{label}_NOTE',x['base_note'])])
 for n,v in constants:h+=f'#define MF_WS_{n} {v}\n'
 (R/'src/wingsuit_audio_data.h').write_text(h+'#endif\n')
 manifest=json.loads((A/'manifest.json').read_text());manifest['files'].update(files);(A/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ('files','sources','samples')}))
if __name__=='__main__':
 import sys
 assert len(sys.argv)==2
 import_bank(sys.argv[1])
