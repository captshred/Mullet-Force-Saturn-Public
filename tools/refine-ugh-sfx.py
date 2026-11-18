#!/usr/bin/env python3
"""Import private UGH with approved PCM8 conversion; boost only FX songs0..7."""
from pathlib import Path
import subprocess,struct,hashlib,json,math,re,wave,argparse
from level1_refinement import read,write
R=Path(__file__).resolve().parents[1];BASE='744053ba851c9da6b8953708f125313f177b7dcb'
def old(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('private_wav',type=Path);a=p.parse_args()
 with wave.open(str(a.private_wav)) as w:channels,width,rate,frames=w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()
 assert (channels,width,rate)==(2,2,44100)
 pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(a.private_wav),'-af','pan=mono|c0=0.5*c0+0.5*c1','-ar','11025','-acodec','pcm_s8','-f','s8','-'])
 ton=bytearray(old('assets/cd/FX.TON'));at=int.from_bytes(ton[24:26],'big')+4;sa=((ton[at+3]&15)<<16)|int.from_bytes(ton[at+4:at+6],'big');oldn=int.from_bytes(ton[at+8:at+10],'big');assert oldn==12274
 argh=bytes(ton[sa:sa+oldn]);ton=ton[:sa]+pcm+bytes(4);ton+=bytes(-len(ton)%4);ton[at+8:at+10]=len(pcm).to_bytes(2,'big')
 src=old('assets/cd/FX.SEQ');songs=[];audit=[];gate=math.ceil((len(pcm)/11025+.05)*960)
 for i in range(9):
  h,e,end=read(src,i)
  for n in e:
   if n['kind']=='note' and i<8:
    v=n['velocity'];n['velocity']=min(127,max(1,(v*115+50)//100));audit.append(dict(song=i,original=v,new=n['velocity']))
  if i==8:
   h=bytearray(h);h[8:12]=gate.to_bytes(4,'big');e[2]['off']=gate;e[3]['on']=gate
  songs.append(write(bytes(h),e)[8:])
 pos=38;offsets=[]
 for s in songs:offsets.append(pos);pos+=len(s)
 seq=struct.pack('>H9I',9,*offsets)+b''.join(songs);seq+=bytes(-len(seq)%4)
 seqaddr=148864;tonaddr=seqaddr+len(seq);stageaddr=tonaddr+len(ton);stageton=stageaddr+len(old('assets/cd/STAGE.SEQ'));end=stageton+len(old('assets/cd/STAGE.TON'));assert end<=524288
 mp=bytearray(old('assets/cd/CUSTOM.MAP'))
 for off,addr,size in [(16,seqaddr,len(seq)),(24,tonaddr,len(ton)),(32,stageaddr,len(old('assets/cd/STAGE.SEQ'))),(40,stageton,len(old('assets/cd/STAGE.TON')))]:mp[off+1:off+4]=addr.to_bytes(3,'big');mp[off+5:off+8]=size.to_bytes(3,'big')
 outputs=[('FX.SEQ',seq),('FX.TON',ton),('CUSTOM.MAP',mp)]
 for name,data in outputs:(R/'assets/cd'/name).write_bytes(data)
 hdr=old('src/music_data.h').decode()
 for k,v in dict(MF_FX_SEQ_BYTES=len(seq),MF_FX_TON_BYTES=len(ton),MF_FX_TON_ADDR=tonaddr,MF_STAGE_SEQ_ADDR=stageaddr,MF_STAGE_TON_ADDR=stageton).items():hdr=re.sub(r'(#define '+k+r') .*',lambda m:m[1]+' '+str(v),hdr)
 hdr=hdr.replace('{25,11,47,8,7,28,32,49,71}','{25,11,47,8,7,28,32,49,'+str(math.ceil(len(pcm)/11025*60)+4)+'}')
 hdr=hdr.replace('#endif',f'#define MF_DEATH_MIN_TICKS {math.ceil(len(pcm)/11025*60)}\n#endif');(R/'src/music_data.h').write_text(hdr)
 report=dict(baseline_executable=BASE,source_sha256=sha(a.private_wav.read_bytes()),source_channels=channels,source_rate=rate,source_bits=width*8,source_frames=frames,source_seconds=frames/rate,frames=len(pcm),sample_rate=11025,bits=8,pcm_bytes=len(pcm),pcm_sha256=sha(pcm),removed_argh_bytes=oldn,removed_argh_sha256=sha(argh),conversion='arithmetic mean of stereo channels, bandlimited11025Hz resample, signed PCM8; no gain, normalization, trimming, fades or compression',program=8,velocity=110,velocity_rounding='nearest integer, half upward',velocity_audit=audit,sound_ram_high_water=end,sound_ram_free=524288-end,pcm_runtime_address=tonaddr+sa,outputs={n:dict(bytes=len(b),sha256=sha(b)) for n,b in outputs})
 (R/'assets/sfx/ugh-report.json').write_text(json.dumps(report,indent=2)+'\n')
 p=R/'assets/music/report.json';j=json.loads(old('assets/music/report.json'));j['outputs'].update(report['outputs']);j['ugh_refinement']=report;j['sound_ram_high_water']=end
 for x in j['sound_ram_regions']:
  if x['name'] in ['FX.SEQ','FX.TON','STAGE.SEQ','STAGE.TON']:
   x['start']={'FX.SEQ':seqaddr,'FX.TON':tonaddr,'STAGE.SEQ':stageaddr,'STAGE.TON':stageton}[x['name']];x['size']=len((R/'assets/cd'/x['name']).read_bytes());x['end']=x['start']+x['size']
 j['sound_ram_unallocated']=524288-sum(x['size'] for x in j['sound_ram_regions']);p.write_text(json.dumps(j,indent=2)+'\n')
 p=R/'assets/public-runtime-lock.json';j=json.loads(old('assets/public-runtime-lock.json'));j.update({'assets/cd/'+n:v for n,v in report['outputs'].items()});p.write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
