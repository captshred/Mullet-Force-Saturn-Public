#!/usr/bin/env python3
"""Import private MF SFX2.zip into public runtime bank. Requires ffmpeg.
Reuses obsolete voices 0/2 and replaces bat 7. Other voices/music stay exact.
Run once per new source archive; source WAVs are never written into assets/.
"""
from pathlib import Path
import argparse,hashlib,json,math,struct,subprocess,tempfile,zipfile
R=Path(__file__).resolve().parents[1]
def digest(b): return hashlib.sha256(b).hexdigest()
def voices(data):
 result=[]
 for i in range((struct.unpack_from('>H',data)[0]-8)//2):
  off=struct.unpack_from('>H',data,8+2*i)[0];v=bytearray(data[off:off+36]);assert v[2]==0
  sa=((v[7]&15)<<16)|struct.unpack_from('>H',v,8)[0];n=struct.unpack_from('>H',v,12)[0]
  result.append((v,data[sa:sa+n*2]))
 return result

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('archive',type=Path);args=ap.parse_args()
 cd=R/'assets/cd';old=(cd/'FX.TON').read_bytes();vs=voices(old);report=[]
 with zipfile.ZipFile(args.archive) as z,tempfile.TemporaryDirectory() as td:
  for slot,name,target in [(0,'nonkill_1.wav',.40),(2,'explode_1.wav',.40),(7,'NEWBAT.wav',.38)]:
   matches=[n for n in z.namelist() if Path(n).name==name and not n.startswith('__MACOSX/')];assert len(matches)==1
   source=z.read(matches[0]);inp=Path(td)/name;inp.write_bytes(source)
   raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(inp),'-ac','1','-ar','22050','-f','s16be','-'])
   vals=list(struct.unpack('>'+str(len(raw)//2)+'h',raw));peak=max(map(abs,vals));active=[i for i,v in enumerate(vals) if abs(v)>=max(1,peak*.0001)]
   a=max(0,active[0]-8);b=min(len(vals),active[-1]+49);vals=[v*min(1,i/8,(b-a-1-i)/48) for i,v in enumerate(vals[a:b])]
   gain=32767*target/max(map(abs,vals));pcm=b''.join(struct.pack('>h',round(v*gain)) for v in vals)
   v=bytearray(vs[5][0]);v[4+0x19]=72 # key 60 => half unity clock = 22050 Hz
   struct.pack_into('>H',v,12,len(vals));vs[slot]=(v,pcm)
   report.append(dict(file=name,voice=slot,source_sha256=digest(source),sample_rate=22050,frames=len(vals),duration_seconds=len(vals)/22050,trim_frames=[a,b],peak=max(abs(round(v*gain)) for v in vals),pcm_sha256=digest(pcm),conversion='ffmpeg mono + bandlimited 2:1 resample, PCM16 big endian, normalized, 8/48-frame edge fades'))
 base=struct.unpack_from('>H',old,8)[0]+36*len(vs);out=bytearray(old[:base]);payload=bytearray()
 for i,(v,pcm) in enumerate(vs):
  sa=base+len(payload);v[7]=(v[7]&240)|(sa>>16);struct.pack_into('>H',v,8,sa&65535)
  off=struct.unpack_from('>H',old,8+2*i)[0];out[off:off+36]=v;payload+=pcm
 out+=payload;out+=bytes(-len(out)%4);(cd/'FX.TON').write_bytes(out)
 oldseq=(cd/'FX.SEQ').read_bytes();count=struct.unpack_from('>H',oldseq)[0];songs=[];ticks=[]
 for i in range(count):
  a=struct.unpack_from('>I',oldseq,2+4*i)[0];b=struct.unpack_from('>I',oldseq,6+4*i)[0] if i+1<count else len(oldseq)
  duration=(len(vs[i][1])//2)/(22050 if i in (0,2,7) else 44100);ticks.append(math.ceil(duration*60)+3)
  if i in (0,2,7):
   gate=math.ceil((duration+1/60)*960);assert gate<16384
   # Sega SEQ uses extension events, not MIDI variable-length quantities.
   rem=gate;ext=bytearray()
   while rem>=512:ext.append(0x88);rem-=512
   ctl=0x40 if rem>=256 else 0
   stream=bytes([0xb0,32,0,0,0xc0,i,0])+ext+bytes([ctl,60,110,rem%256,0])
   stream+=bytes([0x8c])*(gate//256)+bytes([0xb0,123,0,gate%256,0x83])
   song=struct.pack('>HHHHII',480,1,16,0,gate,500000)+stream;song+=bytes(-len(song)%4)
  else: song=oldseq[a:b]
  songs.append(song)
 ptr=(2+count*4+3)&~3;seq=bytearray(struct.pack('>H',count))
 for song in songs:seq+=struct.pack('>I',ptr);ptr+=len(song)
 seq+=bytes(-len(seq)%4);seq+=b''.join(songs);(cd/'FX.SEQ').write_bytes(seq)
 fxaddr=(0x24580+len(seq)+3)&~3;stageaddr=(fxaddr+len(out)+3)&~3;toneaddr=stageaddr+len((cd/'STAGE.SEQ').read_bytes());end=toneaddr+len((cd/'STAGE.TON').read_bytes());assert end<=524288
 mp=bytearray((cd/'CUSTOM.MAP').read_bytes())
 for off,addr,size in [(16,0x24580,len(seq)),(24,fxaddr,len(out)),(32,stageaddr,len((cd/'STAGE.SEQ').read_bytes())),(40,toneaddr,len((cd/'STAGE.TON').read_bytes()))]:mp[off+1:off+4]=addr.to_bytes(3,'big');mp[off+5:off+8]=size.to_bytes(3,'big')
 (cd/'CUSTOM.MAP').write_bytes(mp)
 p=R/'src/music_data.h';s=p.read_text();import re
 for key,value in dict(MF_CUSTOM_SFX_TICKS='{'+','.join(map(str,ticks))+'}',MF_FX_SEQ_BYTES=len(seq),MF_FX_TON_BYTES=len(out),MF_FX_TON_ADDR=hex(fxaddr),MF_STAGE_SEQ_ADDR=hex(stageaddr),MF_STAGE_TON_ADDR=hex(toneaddr)).items():s=re.sub(r'(#define '+key+r') .*',r'\g<1> '+str(value),s)
 p.write_text(s)
 p=R/'assets/music/report.json';r=json.loads(p.read_text());original_locks={}
 for i in [1,3,4,5,6]:
  v,pcm=voices(old)[i];v[7]&=240;v[8:10]=bytes(2);original_locks[str(i)]=dict(voice_sha256=digest(v),pcm_sha256=digest(pcm))
 r['sfx_update_2']=dict(original_voice_locks=original_locks,samples=report,before_high_water=420000,after_high_water=end,contiguous_free=524288-end,replaced_voices=[0,2,7],unchanged_voices=[1,3,4,5,6]);r['sound_ram_regions']=[dict(x) for x in r['sound_ram_regions']]
 for x in r['sound_ram_regions']:
  if x['name'] in ['FX.SEQ','FX.TON','STAGE.SEQ','STAGE.TON']:
   x['start']={'FX.SEQ':0x24580,'FX.TON':fxaddr,'STAGE.SEQ':stageaddr,'STAGE.TON':toneaddr}[x['name']];x['size']=len((cd/x['name']).read_bytes());x['end']=x['start']+x['size']
 r['sound_ram_high_water']=end;r['sound_ram_unallocated']=524288-sum(x['size'] for x in r['sound_ram_regions'])
 for name in r['outputs']:
  data=(cd/name).read_bytes();r['outputs'][name]=dict(bytes=len(data),sha256=digest(data))
 p.write_text(json.dumps(r,indent=2)+'\n')
 p=R/'assets/public-runtime-lock.json';locks=json.loads(p.read_text())
 for name in ['FX.SEQ','FX.TON','CUSTOM.MAP']:
  data=(cd/name).read_bytes();locks['assets/cd/'+name]=dict(bytes=len(data),sha256=digest(data))
 p.write_text(json.dumps(locks,indent=2)+'\n');print(json.dumps(r['sfx_update_2'],indent=2))
if __name__=='__main__':main()
