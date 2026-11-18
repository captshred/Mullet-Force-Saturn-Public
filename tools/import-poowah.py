#!/usr/bin/env python3
"""Replace only the protected death PCM; retain16-bit depth when it fits."""
from pathlib import Path
import subprocess,struct,json,hashlib,math,re,wave,argparse
from level1_refinement import read,write
R=Path(__file__).resolve().parents[1];BASE='653b5f4206e58e9aa8e4c540ce08fa89f9db595a'
def old(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('private_wav',type=Path);a=p.parse_args()
 with wave.open(str(a.private_wav)) as w:ch,width,rate,n=w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()
 assert(ch,width,rate)==(1,2,44100)
 pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(a.private_wav),'-ac','1','-ar','11025','-acodec','pcm_s16be','-f','s16be','-']);frames=len(pcm)//2
 ton=bytearray(old('assets/cd/FX.TON'));at=int.from_bytes(ton[24:26],'big')+4;sa=((ton[at+3]&15)<<16)|int.from_bytes(ton[at+4:at+6],'big');removed=bytes(ton[sa:sa+10725]);ton=ton[:sa]+pcm+bytes(4);ton+=bytes(-len(ton)%4);ton[at+3]&=239;ton[at+8:at+10]=frames.to_bytes(2,'big')
 src=old('assets/cd/FX.SEQ');songs=[];gate=math.ceil((frames/11025+.05)*960)
 # Copy original songs0..7 as bytes: no second velocity boost, re-encoding or timing changes.
 for i in range(8):
  start=int.from_bytes(src[2+4*i:6+4*i],'big');end=int.from_bytes(src[6+4*i:10+4*i],'big');songs.append(src[start:end])
 h,e,_=read(src,8);h=bytearray(h);h[8:12]=gate.to_bytes(4,'big');e[2]['off']=gate;e[3]['on']=gate;songs.append(write(bytes(h),e)[8:]);offsets=[];pos=38
 for s in songs:offsets.append(pos);pos+=len(s)
 seq=struct.pack('>H9I',9,*offsets)+b''.join(songs);seq+=bytes(-len(seq)%4)
 sq=148864;fx=sq+len(seq);stage=fx+len(ton);tone=stage+len(old('assets/cd/STAGE.SEQ'));end=tone+len(old('assets/cd/STAGE.TON'));assert end<=524288
 mp=bytearray(old('assets/cd/CUSTOM.MAP'))
 for off,addr,size in [(16,sq,len(seq)),(24,fx,len(ton)),(32,stage,len(old('assets/cd/STAGE.SEQ'))),(40,tone,len(old('assets/cd/STAGE.TON')))]:mp[off+1:off+4]=addr.to_bytes(3,'big');mp[off+5:off+8]=size.to_bytes(3,'big')
 out=[('FX.SEQ',seq),('FX.TON',ton),('CUSTOM.MAP',mp)]
 for name,b in out:(R/'assets/cd'/name).write_bytes(b)
 hdr=old('src/music_data.h').decode()
 for k,v in dict(MF_FX_SEQ_BYTES=len(seq),MF_FX_TON_BYTES=len(ton),MF_FX_TON_ADDR=fx,MF_STAGE_SEQ_ADDR=stage,MF_STAGE_TON_ADDR=tone,MF_DEATH_MIN_TICKS=math.ceil(frames/11025*60)).items():hdr=re.sub(r'(#define '+k+r') .*',lambda m:m[1]+' '+str(v),hdr)
 hdr=hdr.replace('{25,11,47,8,7,28,32,49,63}','{25,11,47,8,7,28,32,49,'+str(math.ceil(frames/11025*60)+4)+'}');(R/'src/music_data.h').write_text(hdr)
 report=dict(baseline_executable=BASE,source_sha256=sha(a.private_wav.read_bytes()),source_channels=ch,source_bits=width*8,source_rate=rate,source_frames=n,source_seconds=n/rate,frames=frames,sample_rate=11025,bits=16,pcm_bytes=len(pcm),pcm_sha256=sha(pcm),removed_ugh_pcm_bytes=len(removed),removed_ugh_pcm_sha256=sha(removed),conversion='mono PCM16 preserved; deterministic bandlimited44100->11025Hz resample, big-endian PCM16; no gain/normalization/trim/fade/compression/stretch',gate_ticks=gate,protection_min_ticks=math.ceil(frames/11025*60),velocity=110,priority=31,sound_ram_high_water=end,sound_ram_free=524288-end,pcm_runtime_address=fx+sa,outputs={name:dict(bytes=len(b),sha256=sha(b)) for name,b in out})
 (R/'assets/sfx/poowah-report.json').write_text(json.dumps(report,indent=2)+'\n')
 p=R/'assets/music/report.json';j=json.loads(old('assets/music/report.json'));j['outputs'].update(report['outputs']);j['poowah_swap']=report;j['sound_ram_high_water']=end
 for x in j['sound_ram_regions']:
  if x['name'] in ['FX.SEQ','FX.TON','STAGE.SEQ','STAGE.TON']:
   x['start']={'FX.SEQ':sq,'FX.TON':fx,'STAGE.SEQ':stage,'STAGE.TON':tone}[x['name']];x['size']=len((R/'assets/cd'/x['name']).read_bytes());x['end']=x['start']+x['size']
 j['sound_ram_unallocated']=524288-sum(x['size'] for x in j['sound_ram_regions']);p.write_text(json.dumps(j,indent=2)+'\n')
 p=R/'assets/public-runtime-lock.json';j=json.loads(old('assets/public-runtime-lock.json'));j.update({'assets/cd/'+name:v for name,v in report['outputs'].items()});p.write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
