#!/usr/bin/env python3
"""Private WAV importer. Only converted runtime PCM and metadata are public."""
from pathlib import Path
import argparse,subprocess,struct,hashlib,json,math,re
from level1_refinement import read,write
R=Path(__file__).resolve().parents[1]
BASE='38ed9a690f9349f490b5280992fcef882b32aaaf'
def original(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('private_wav',type=Path);a=p.parse_args()
 # Explicit unity-gain arithmetic downmix; deterministic bandlimited resampling.
 pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(a.private_wav),'-af','pan=mono|c0=0.5*c0+0.5*c1','-ar','11025','-acodec','pcm_s8','-f','s8','-'])
 old=original('assets/cd/FX.TON');table=int.from_bytes(old[:2],'big');first=int.from_bytes(old[8:10],'big');tables=old[table:first];count=(table-8)//2;assert count==8
 vs=[];samples=[]
 for i in range(count):
  at=int.from_bytes(old[8+2*i:10+2*i],'big');v=bytearray(old[at:at+36]);sa=((v[7]&15)<<16)|int.from_bytes(v[8:10],'big');frames=int.from_bytes(v[12:14],'big');samples.append(old[sa:sa+frames*2]);vs.append(v)
 v=bytearray(vs[6]);v[7]=(v[7]&0xc0)|0x10;v[10:12]=bytes(2);v[12:14]=len(pcm).to_bytes(2,'big');v[29]=84;vs.append(v);samples.append(pcm)
 table=8+2*len(vs);vb=table+len(tables);pcmbase=(vb+36*len(vs)+3)&~3;payload=bytearray();headers=[];offsets=[table,table+18,table+28,table+38]
 for i,(v,s) in enumerate(zip(vs,samples)):
  payload+=bytes(-(pcmbase+len(payload))%4);sa=pcmbase+len(payload);v[7]=(v[7]&240)|(sa>>16);v[8:10]=(sa&65535).to_bytes(2,'big');headers.append(v);offsets.append(vb+36*i);payload+=s
  if i==8:payload+=bytes(4)
 ton=struct.pack('>'+str(len(offsets))+'H',*offsets)+tables+b''.join(headers);ton+=bytes(pcmbase-len(ton))+payload;ton+=bytes(-len(ton)%4)
 oldseq=original('assets/cd/FX.SEQ');songs=[]
 for i in range(8):
  at=int.from_bytes(oldseq[2+4*i:6+4*i],'big');end=int.from_bytes(oldseq[6+4*i:10+4*i],'big') if i<7 else len(oldseq);songs.append(oldseq[at:end])
 h,ev,_=read(oldseq,6);gate=math.ceil((len(pcm)/11025+.05)*960);h=bytearray(h);h[8:12]=gate.to_bytes(4,'big')
 ev[1]['payload']=bytes([192,8]);ev[2]['off']=gate;ev[3]['on']=gate;songs.append(write(bytes(h),ev)[8:])
 offsets=[];pos=2+4*len(songs)
 for s in songs:offsets.append(pos);pos+=len(s)
 seq=struct.pack('>H',len(songs))+struct.pack('>9I',*offsets)+b''.join(songs);seq+=bytes(-len(seq)%4)
 seqaddr=0x24580;tonaddr=seqaddr+len(seq);stageaddr=tonaddr+len(ton);stageton=stageaddr+len(original('assets/cd/STAGE.SEQ'));end=stageton+len(original('assets/cd/STAGE.TON'));assert end<=524288
 mp=bytearray(original('assets/cd/CUSTOM.MAP'))
 for off,addr,size in [(16,seqaddr,len(seq)),(24,tonaddr,len(ton)),(32,stageaddr,len(original('assets/cd/STAGE.SEQ'))),(40,stageton,len(original('assets/cd/STAGE.TON')))]:mp[off+1:off+4]=addr.to_bytes(3,'big');mp[off+5:off+8]=size.to_bytes(3,'big')
 for name,data in [('FX.SEQ',seq),('FX.TON',ton),('CUSTOM.MAP',mp)]:(R/'assets/cd'/name).write_bytes(data)
 hdr=original('src/music_data.h').decode()
 for key,val in dict(MF_FX_SEQ_BYTES=len(seq),MF_FX_TON_BYTES=len(ton),MF_FX_TON_ADDR=tonaddr,MF_STAGE_SEQ_ADDR=stageaddr,MF_STAGE_TON_ADDR=stageton,MF_CUSTOM_SFX_TICKS='{25,11,47,8,7,28,32,49,'+str(math.ceil(len(pcm)/11025*60)+4)+'}').items():hdr=re.sub(r'(#define '+key+r') .*',lambda m:m[1]+' '+str(val),hdr)
 (R/'src/music_data.h').write_text(hdr)
 report=dict(baseline=BASE,source_sha256=sha(a.private_wav.read_bytes()),conversion='ffmpeg arithmetic stereo mean, bandlimited resample to11025Hz, signed PCM8; no normalization, trimming, fades, compression or time stretch',frames=len(pcm),sample_rate=11025,bits=8,new_pcm_bytes=len(pcm),new_pcm_sha256=sha(pcm),old_pcm_bytes=len(samples[6]),old_pcm_sha256=sha(samples[6]),sound_ram_high_water=end,sound_ram_free=524288-end,old_program=6,new_program=8,old_pcm_runtime_address=tonaddr+(((headers[6][7]&15)<<16)|int.from_bytes(headers[6][8:10],'big')),new_pcm_runtime_address=tonaddr+(((headers[8][7]&15)<<16)|int.from_bytes(headers[8][8:10],'big')),outputs={n:dict(bytes=len(d),sha256=sha(d)) for n,d in [('FX.SEQ',seq),('FX.TON',ton),('CUSTOM.MAP',mp)]})
 (R/'assets/sfx/human-death-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
