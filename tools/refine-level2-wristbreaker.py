#!/usr/bin/env python3
"""Optional private-MIDI importer; public builds use committed native assets."""
from pathlib import Path
import sys,struct,collections,bisect,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
if len(sys.argv)!=2:raise SystemExit('Usage: python tools/refine-level2-wristbreaker.py PRIVATE_DRUM_MIDI')
import level1_refinement as seq,midi
BASE='17445b421bcafd8d5c974d624ddc2a34e768d725'
def orig(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def voice(b,i):
 a=int.from_bytes(b[8+2*i:10+2*i],'big');v=b[a:a+4];layers=[bytearray(b[a+4+32*j:a+36+32*j]) for j in range(v[2]+1)];return v,layers
def sample(b,layer):
 sa=(layer[3]&15)*65536+int.from_bytes(layer[4:6],'big');n=int.from_bytes(layer[8:10],'big')*(1 if layer[3]&16 else 2);return sa,b[sa:sa+n+4]
def repack(b,voices):
 table=8+len(voices)*2;oldtable=int.from_bytes(b[:2],'big');oldfirst=int.from_bytes(b[8:10],'big');tables=b[oldtable:oldfirst];assert len(tables)==42
 offsets=[table,table+18,table+28,table+38];vb=table+42;p=vb;voc=[]
 for vh,ls in voices:offsets.append(p);p+=4+32*len(ls)
 pcmbase=(p+3)&~3;pcm=bytearray();byaddr={};repacked=[]
 for vh,ls in voices:
  for layer in ls:
   oldsa,raw=sample(b,layer)
   if oldsa not in byaddr:
    pcm+=bytes(-(pcmbase+len(pcm))%4);byaddr[oldsa]=pcmbase+len(pcm);pcm+=raw
   sa=byaddr[oldsa];layer[3]=(layer[3]&240)|(sa>>16);layer[4:6]=(sa&65535).to_bytes(2,'big')
  repacked.append(bytes(vh)+b''.join(ls))
 out=struct.pack('>'+str(len(offsets))+'H',*offsets)+tables+b''.join(repacked);out+=bytes(pcmbase-len(out))+pcm;out+=bytes(-len(out)%4)
 return out,byaddr
h,events,end=seq.read(orig('assets/wingsuit/WMUSIC.SEQ'));notes=[x for x in events if x['kind']=='note'];l=[n for n in notes if n['program']==0 and n['pan']==0];r=[n for n in notes if n['program']==0 and n['pan']==127]
def key(n):return tuple(n[k] for k in ('on','off','pitch','velocity','program'))+(seq.curve(n,events),)
counts=collections.Counter(key(n) for n in l);removed=set();unique=[]
for n in r:
 k=key(n)
 if counts[k]:removed.add(id(n));counts[k]-=1
 else:unique.append(n)
kept=[n for n in notes if id(n) not in removed];needed=set()
for ch in range(16):
 bends=[(i,e) for i,e in enumerate(events) if e['kind']=='event' and e['payload'][0]==224+ch];times=[e['on'] for i,e in bends]
 for n in kept:
  if n['channel']!=ch:continue
  a=bisect.bisect_right(times,n['on'])-1;b=bisect.bisect_left(times,n['off']+165);needed.update(i for i,e in bends[max(a,0):b])
out=[];state={}
for i,e in enumerate(events):
 if id(e) in removed:continue
 e=e.copy()
 if e['kind']=='event':
  p=e['payload'];c=p[0]&15;typ=p[0]&240
  if typ==224 and i not in needed:continue
  if typ==176:
   if p[1]==123:p=bytes([p[0],32,1])
   elif p[1]==10 and p[2] in (0,127):p=bytes([p[0],10,64])
   # CC7 retains relative authored balance; scale 88/80 up to127/115.
   elif p[1]==7:p=bytes([p[0],7,round(p[2]*127/88)])
  k=tuple(p[:2]) if typ in (176,160) else (p[0],)
  if state.get(k)==p and e['on'] not in (0,end):continue
  state[k]=p;e['payload']=p
 out.append(e)
# Verify every retained musical pitch-control curve before/after exactly.
# Pan/gain are separately authorized changes; note pitches/gates/dynamics unchanged.
newread=seq.read(seq.write(h,out))[1];newnotes=[n for n in newread if n['kind']=='note']
assert [seq.signature(n) for n in kept]==[seq.signature(n) for n in newnotes]
assert all(seq.curve(a,events)==seq.curve(b,newread) for a,b in zip(kept,newnotes))
report=json.loads(orig('assets/music/level1-custom-report.json'));mapping=report['mapping'];mapping['51']='ride';samples={x['role']:x for x in report['samples']}
_,ppqn,tr=midi.read(sys.argv[1]);es=midi.merged(tr);dn,*errors=midi.notes(es);assert errors[-2:]==[0,0];assert ppqn==480
assert all(t==291262 for _,t in midi.tempo_map(es))
# Distinct keys for all simultaneous hits prevent key-scoped off of a prior
# drum tail from stopping a later hit. A native key-split kit uses shared PCM.
aliases={};active={};dout=[];dr=[];nextkey=24
for a,b,c,k,v in dn:
 on=a*2;role=mapping[str(k)];s=samples[role];duration=s['frames']/s['rate'];duration=min(duration,.1) if k==50 else min(duration,.16) if k==64 else duration
 # Native gate timers round earlier than PCM completion. Ordinary one-shots
 # get 50ms plus2% scheduling allowance; playback still stops at sample LEA.
 # Approved muted-crash/short-hat articulations retain their deliberate choke.
 gate_seconds=duration if k in (50,64) else duration*1.02+.05
 off=on+round(gate_seconds*960/.291262);pool=aliases.setdefault(role,[]);key=next((key for key in pool if active.get(key,0)<=on),None)
 if key is None:key=nextkey;nextkey+=1;pool.append(key)
 active[key]=off;item=dict(kind='note',on=on,off=off,channel=0,pitch=key,velocity=v);dr.append(item);dout.append(item)
# Permit natural last-hit tails across the unchanged loop boundary.
for key in active:
 hits=[n for n in dr if n['pitch']==key]
 assert hits[-1]['off']<=end+hits[0]['on'],'Alias overlaps its next loop'
# Channel0 is unused in the recovered score; no extra sequencer/timer.
setup=[dict(kind='event',on=0,payload=bytes(p)) for p in [(176,32,1),(192,1),(176,7,127),(176,10,64),(176,11,127),(224,64)]]
all_events=sorted(setup+out+dout,key=lambda e:e['on']);sequence=seq.write(h,all_events)
bank=orig('assets/cd/STAGE.TON');openv,openls=voice(bank,0);bassv,bassls=voice(bank,2);kit=[]
for role,keys in aliases.items():
 for key in keys:
  _,ls=voice(bank,samples[role]['program']);layer=ls[0];layer[0]=layer[1]=key;layer[25]+=key-samples[role]['root'];assert layer[25]<128;kit.append(layer)
# Original native score bend range is6, unlike Level1's range12. Copy PCM and
# layers unchanged, retaining six-semitone effective bend interpretation.
openv=bytes([6])+openv[1:];bassv=bytes([6])+bassv[1:]
tone,_=repack(bank,[(openv,openls),(bytes([0,0,len(kit)-1,0]),kit),(bassv,bassls)])
oldfx=orig('assets/wingsuit/WDEATH.TON');fx,fxsa=repack(oldfx,[voice(oldfx,i) for i in range(4)])
seqaddr=148864;fxaddr=seqaddr+84;musicaddr=fxaddr+len(fx);toneaddr=musicaddr+len(sequence);fireaddr=toneaddr+len(tone);endaddr=fireaddr+38224
print(json.dumps(dict(removed=len(removed),unique=len(unique),sequence=len(sequence),tone=len(tone),sfx=len(fx),drum_keys=len(kit),highwater=endaddr,free=524288-endaddr,held_peak=seq.peak(kept+dr),release_peak=seq.peak(kept+dr,165)),indent=2))
assert endaddr<=524288

# Preserve the SFX sample bytes/guards and every parameter except relocated SA.
for i in range(4):
 ov,ol=voice(oldfx,i);nv,nl=voice(fx,i);assert ov==nv
 assert sample(oldfx,ol[0])[1]==sample(fx,nl[0])[1]
 a=ol[0];b=nl[0];assert all(a[j]==b[j] for j in range(32) if j not in (3,4,5));assert a[3]&240==b[3]&240
outputs={}
def save(name,data):
 (R/name).write_bytes(data);outputs[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
save('assets/wingsuit/WMUSIC.SEQ',sequence);save('assets/wingsuit/WMUSIC.TON',tone);save('assets/wingsuit/WDEATH.TON',fx)
fxseq=bytearray(orig('assets/wingsuit/WDEATH.SEQ'));pos=fxseq.index(bytes([176,123,0]));fxseq[pos+1]=32;save('assets/wingsuit/WDEATH.SEQ',bytes(fxseq))
def update_map(name):
 b=bytearray(orig('assets/wingsuit/'+name))
 for offset,address,size in [(24,fxaddr,len(fx)),(32,musicaddr,len(sequence)),(40,toneaddr,len(tone)),(48,fireaddr,38224)]:
  if offset>=len(b)-8:continue
  b[offset+1:offset+4]=address.to_bytes(3,'big');b[offset+5:offset+8]=size.to_bytes(3,'big')
 save('assets/wingsuit/'+name,bytes(b))
for name in ('WMUSIC.MAP','WFIRE.MAP'):update_map(name)
b=bytearray(orig('assets/wingsuit/WDEATH.MAP'));b[29:32]=len(fx).to_bytes(3,'big');save('assets/wingsuit/WDEATH.MAP',bytes(b))
import re
header=orig('src/wingsuit_audio_data.h').decode();values={'TON_BYTES':len(fx),'MUSIC_SEQ_ADDR':musicaddr,'MUSIC_SEQ_BYTES':len(sequence),'MUSIC_TON_ADDR':toneaddr,'MUSIC_TON_BYTES':len(tone),'FIRE_TON_ADDR':fireaddr}
for i,name in [(2,'ATTACK'),(3,'LOOP')]:
 a=int.from_bytes(fx[8+2*i:10+2*i],'big');_,ls=voice(fx,i);sa,_=sample(fx,ls[0]);values['FLAME_'+name+'_LAYER_ADDR']=fxaddr+a+4;values['FLAME_'+name+'_PCM_ADDR']=fxaddr+sa
for k,v in values.items():header=re.sub(r'(#define MF_WS_'+k+r') \S+',lambda m:m[1]+' '+str(v),header)
save('src/wingsuit_audio_data.h',header.encode())
source=orig('src/wingsuit_audio.c').decode();assert source.count('SND_SetSeqVl(0,127,0)')==1;source=source.replace('SND_SetSeqVl(0,127,0)','SND_SetSeqVl(0,108,0)');save('src/wingsuit_audio.c',source.encode())
manifest=json.loads(orig('assets/wingsuit/manifest.json'))
for path,info in list(outputs.items()):
 name=Path(path).name
 if path.startswith('assets/wingsuit/') and name in manifest['files']:manifest['files'][name].update(info)
manifest['audio_refinement_report']='assets/wingsuit/wristbreaker-refinement.json'
save('assets/wingsuit/manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())
result=dict(baseline=BASE,removed_rhythm_events=len(removed),unique_right_events=len(unique),left_events=len(l),right_events=len(r),kept_melodic_events=len(kept),drum_hits=len(dn),mapping=mapping,drum_note_counts=dict(collections.Counter(n[3] for n in dn)),drum_key_aliases=aliases,sound_ram_high_water=endaddr,sound_ram_free=524288-endaddr,music_held_peak_before=seq.peak(notes),melodic_held_peak_after=seq.peak(kept),music_held_peak_after=seq.peak(kept+dr),music_50ms_release_peak=seq.peak(kept+dr,165),sequence_bytes=len(sequence),tone_bytes=len(tone),music_volume=108,original_bend_range=6,level1_bend_range=12,sfx_pcm_unchanged=True,level1_unchanged=True,unloaded_unused_samples=['muted_guitar','closed_hat'],one_shot_gate_allowance='50ms plus2% beyond PCM duration; short articulations50/64 unchanged',source_midi_sha256=hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),drum_performance_sha256=hashlib.sha256(json.dumps([(n[0]*2,n[2],n[3],n[4]) for n in dn],separators=(',',':')).encode()).hexdigest(),outputs=outputs)
result['compiled_drum_performance_sha256']=hashlib.sha256(json.dumps(sorted((n[0]*2,mapping[str(n[3])],n[4]) for n in dn),separators=(',',':')).encode()).hexdigest()
(R/'assets/wingsuit/wristbreaker-refinement.json').write_text(json.dumps(result,indent=2)+'\n')
