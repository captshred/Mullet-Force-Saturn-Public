"""Import approved private WAVs into the committed Level 2 SCSP bank."""
from pathlib import Path
import struct,hashlib,json,math,wave,io,zipfile
R=Path(__file__).resolve().parents[1]
A=R/'assets/wingsuit'
def digest(b):return hashlib.sha256(b).hexdigest()
def rounded(n,d):return (n+d//2)//d if n>=0 else -((-n+d//2)//d)
def voice(data,i):
 off=struct.unpack_from('>H',data,8+2*i)[0];v=bytearray(data[off:off+36]);sa=((v[7]&15)<<16)|int.from_bytes(v[8:10],'big');n=int.from_bytes(v[12:14],'big')*2
 return v,data[sa:sa+n]
def import_bank(archive):
 z=zipfile.ZipFile(archive);sources={};pcm=[]
 for name,frames in [('Shot.wav',22403),('Flame.wav',41239)]:
  names=[n for n in z.namelist() if Path(n).name==name and '__MACOSX' not in n];assert len(names)==1
  raw=z.read(names[0])
  with wave.open(io.BytesIO(raw)) as w:
   assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(2,2,44100,frames)
   vals=struct.unpack('<'+str(frames*2)+'h',w.readframes(frames))
  mono=[rounded(vals[i]+vals[i+1],2) for i in range(0,len(vals),2)]
  info={'source_sha256':digest(raw),'source_frames':frames,'source_rate':44100,'source_channels':2,'rate':44100,'bits':16,'channels':1,'frames':frames,'pcm_bytes':frames*2,'downmix':'nearest integer (L+R)/2, symmetric ties away from zero; no resample or gain change','before_seam_sha256':digest(struct.pack('>'+str(frames)+'h',*mono))}
  if name=='Flame.wav':
   # Preserve requested [27981,41239) loop. Blend only its final 128 samples
   # toward the original samples immediately preceding loop start; the wrap
   # then equals an original adjacent-sample boundary, without shifting region.
   start=27981;n=128;original=mono[:]
   for i in range(n):mono[frames-n+i]=rounded(original[frames-n+i]*(n-i-1)+original[start-n+i]*(i+1),n)
   info.update(loop_start=start,loop_end=frames,seam_samples=n,seam_seconds=n/44100,seam='tail-only linear crossfade to pre-loop boundary; attack and loop start unchanged',boundary_delta_before=original[start]-original[-1],boundary_delta_after=mono[start]-mono[-1])
  b=struct.pack('>'+str(frames)+'h',*mono);info.update(pcm_sha256=digest(b),peak=max(map(abs,mono)))
  sources[name]=info;pcm.append(b)
 old=(R/'assets/cd/FX.TON').read_bytes();expl,explpcm=voice(old,2)
 # Copy every complete shared table, rather than the former zero offsets.
 offsets=struct.unpack_from('>4H',old);firstvoice=struct.unpack_from('>H',old,8)[0]
 tables=[old[offsets[i]:offsets[i+1] if i<3 else firstvoice] for i in range(4)]
 assert list(map(len,tables))==[18,10,10,4]
 hdr=8+3*2;new_offsets=[];p=hdr
 for b in tables:new_offsets.append(p);p+=len(b)
 vos=[p+i*36 for i in range(3)];base=p+108
 voices=[expl,bytearray(expl),bytearray(expl)];samples=[explpcm,*pcm];payload=bytearray();sample_info=[]
 for i,(v,b) in enumerate(zip(voices,samples)):
  payload+=bytes((-len(payload))%4);sa=base+len(payload)
  v[7]=(v[7]&0xf0)|(sa>>16);v[8:10]=(sa&65535).to_bytes(2,'big')
  if i:
   v[7]=(v[7]&0x9f)|(0x20 if i==2 else 0);v[10:12]=(27981 if i==2 else 0).to_bytes(2,'big');v[12:14]=(len(b)//2).to_bytes(2,'big');v[29]=60
  sample_info.append({'voice':i,'tone_offset':sa,'bytes':len(b),'frames':len(b)//2,'rate':22050 if i==0 else 44100,'sha256':digest(b)})
  payload+=b
 ton=struct.pack('>7H',*new_offsets,*vos)+b''.join(tables)+b''.join(voices)+payload;ton+=bytes(-len(ton)%4)
 oldseq=(R/'assets/cd/FX.SEQ').read_bytes();a,b=struct.unpack_from('>II',oldseq,10);explsong=oldseq[a:b].replace(b'\xc0\x02\x00',b'\xc0\x00\x00')
 gate=math.ceil((22403/44100+1/60)*960);rem=gate;ext=bytearray()
 while rem>=512:ext.append(0x88);rem-=512
 stream=bytes([0xb0,32,0,0,0xc0,1,0])+ext+bytes([0x40 if rem>=256 else 0,60,110,rem%256,0])+bytes([0x8c])*(gate//256)+bytes([0xb0,123,0,gate%256,0x83])
 shotsong=struct.pack('>4H2I',480,1,16,0,gate,500000)+stream;shotsong+=bytes(-len(shotsong)%4)
 seq=struct.pack('>H2I',2,12,12+len(explsong))+bytes(2)+explsong+shotsong
 seqaddr=0x24580;toneaddr=seqaddr+len(seq)
 def entry(t,addr,n):return bytes([t<<4])+addr.to_bytes(3,'big')+b'\x80'+n.to_bytes(3,'big')
 mp=(R/'assets/cd/CUSTOM.MAP').read_bytes()[:16]+entry(1,seqaddr,len(seq))+entry(0,toneaddr,len(ton))+b'\xff'*8
 files={}
 for n,b in [('WDEATH.MAP',mp),('WDEATH.SEQ',seq),('WDEATH.TON',ton)]:
  (A/n).write_bytes(b);files[n]={'bytes':len(b),'sha256':digest(b)}
 for x in sample_info:x['scsp_addr']=toneaddr+x['tone_offset']
 report={'canonical':'assets/cd/FX.TON voice 2 / FX.SEQ song 2 / MF_WORLD_IMPACT','sources':sources,'samples':sample_info,'tables':dict(zip(['mixer','velocity','peg','plfo'],new_offsets)),'seq_addr':seqaddr,'tone_addr':toneaddr,'scsp_high_water':toneaddr+len(ton),'reserved_before_seq':seqaddr,'scsp_free':524288-toneaddr-len(ton),'files':files,'shot_guard_ticks':math.ceil(22403/44100*60)+3,'explosion_guard_ticks':49,'sdk_sequence_controls':8,'physical_slots':32}
 (A/'audio.json').write_text(json.dumps(report,indent=2)+'\n')
 h='#ifndef MF_WS_AUDIO_DATA_H\n#define MF_WS_AUDIO_DATA_H\n'
 for n,v in [('SEQ_BYTES',len(seq)),('TON_BYTES',len(ton)),('MAP_BYTES',len(mp)),('SEQ_ADDR',seqaddr),('TON_ADDR',toneaddr),('SHOT_TICKS',report['shot_guard_ticks']),('EXP_TICKS',49),('SHOT_VOLUME',96),('FLAME_VOLUME',80)]:h+=f'#define MF_WS_{n} {v}\n'
 (R/'src/wingsuit_audio_data.h').write_text(h+'#endif\n')
 manifest=json.loads((A/'manifest.json').read_text());manifest['files'].update(files);(A/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ('files','sources')}))
if __name__=='__main__':
 import sys
 assert len(sys.argv)==2
 import_bank(sys.argv[1])
