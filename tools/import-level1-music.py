#!/usr/bin/env python3
"""Import private Drop Zone sources into Level1-only native runtime assets.
Never invoked by public builds. Usage: python tools/import-level1-music.py PRIVATE_SOURCE_DIR
"""
from pathlib import Path
import sys,json,math,struct,collections
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from level1_audio import *
import midi,seq
R=Path(__file__).resolve().parents[1]

SPECS=[
 ('open_guitar','Guitar:Bass/Guitars - Open.wav',22050,16,48,.28,True,8),
 ('muted_guitar','Guitar:Bass/Guitars - Mute.wav',11025,8,48,1.054,False,9),
 ('bass','Guitar:Bass/Bass.wav',11025,16,36,.38,True,3),
 ('kick','Drums/Kick.wav',11025,16,36,.4054,False,8),
 ('snare','Drums/Snare.wav',22050,8,38,.45,False,10),
 ('closed_hat','Drums/Hihat Closed.wav',22050,8,42,.25,False,22),
 ('open_hat','Drums/Hihat Open.wav',22050,8,46,.55,False,22),
 ('crash','Drums/Cymbal.wav',22050,8,49,.80,False,24),
 ('ride','Drums/Ride.wav',22050,8,51,.80,False,22),
 ('china','Drums/China.wav',22050,8,52,.80,False,24),
 ('high_tom','Drums/Tom 1.wav',11025,8,48,.5675,False,13),
 ('mid_tom','Drums/Tom 2.wav',11025,8,47,.5675,False,13),
 ('low_tom','Drums/Tom 3.wav',11025,8,43,.5675,False,13),
]

def prepare(source):
 samples=[]
 for role,relative,rate,bits,root,limit,loop,tl in SPECS:
  path=source/'MF_Instrument_Samples'/relative;sr,raw=wavfile.read(path);assert raw.dtype==np.int16 and sr==44100
  mono=raw.astype(float).mean(axis=1)/32768;signal=resample_poly(mono,1,sr//rate);original_frames=len(signal)
  # Preserve initial attacks. Only the runtime copy is resampled/truncated.
  signal=signal[:min(len(signal),int(rate*limit))];lsa=0;loop_info=None
  if loop:
   # Search phase/slope-coherent boundaries with 64-frame context. Root note is
   # supplied by the author, never inferred from distorted-guitar harmonics.
   period=rate/(440*2**((root-69)/12));candidates=[]
   for a in range(round(rate*.10),round(rate*.19),8):
    for cycles in range(4,13):
     ideal=a+round(period*cycles)
     for b in range(ideal-3,ideal+4):
      if b+64>=len(signal) or b-a<128:continue
      before=signal[b-32:b+32];after=signal[a-32:a+32];den=np.sqrt(np.mean(after**2))+1e-9
      score=np.sqrt(np.mean((before-after)**2))/den + abs(np.sqrt(np.mean(signal[a:a+64]**2))-np.sqrt(np.mean(signal[b-64:b]**2)))/den
      candidates.append((float(score),a,b))
   score,lsa,end=min(candidates);signal=signal[:end].copy()
   # Smooth the last 32 samples towards the cyclic lookahead; attack untouched.
   fade=32;w=np.linspace(0,1,fade,endpoint=False);signal[-fade:]=(1-w)*signal[-fade:]+w*signal[lsa-fade:lsa]
   loop_info=dict(start=lsa,end=end,context_error_before_crossfade=score,crossfade_frames=fade)
  else:
   fade=min(round(rate*.012),len(signal));signal[-fade:]*=np.linspace(1,0,fade)
  # Gentle per-family scaling leaves PCM headroom; TON TL sets musical balance.
  gain=min(1.7,.78/(np.max(np.abs(signal))+1e-12));signal*=gain
  quant=32768 if bits==16 else 128;values=np.rint(signal*quant);assert values.min()>=-quant and values.max()<quant
  pcm=values.astype('>i2' if bits==16 else 'i1').tobytes()
  samples.append(dict(role=role,program=len(samples),root=root,rate=rate,bits=bits,frames=len(signal),source_frames=len(raw),source_sha256=digest(path.read_bytes()),original_resampled_frames=original_frames,loop=loop,lsa=lsa,tl=tl,gain=gain,peak=float(np.max(abs(signal))),loop_info=loop_info,pcm=pcm))
 return samples

def melodic_notes(gp):
 # Independent pitch lanes prevent a bend/slide on one string retuning a chord.
 busy=[0]*12;out=[];bends=[];next_string={}
 for n in reversed(gp):
  key=(n['track'],n['string']);n['next_string']=next_string.get(key);next_string[key]=n
 for n in gp:
  free=[c for c,t in enumerate(busy) if t<=n['on']];assert free,'More than 12 held melodic voices'
  c=free[0];busy[c]=n['off'];program=2 if n['track']==2 else 1 if 'PalmMuted' in n['props'] else 0
  pitch=n['pitch'];velocity={'PPP':16,'PP':32,'P':48,'MP':64,'MF':76,'F':96,'FF':112,'FFF':127}[n['dynamic']]
  if n['accent']:velocity=min(127,velocity+12)
  # Dead notes and legato attacks use finite/softer articulation; no fake source
  # samples. Pinch timbre is approximated with a harmonic transposition.
  off=n['off']
  if 'Muted' in n['props']:off=min(off,n['on']+ticks(.055));velocity=round(velocity*.65)
  if 'HopoDestination' in n['props']:velocity=round(velocity*.85)
  if 'Harmonic' in n['props']:
   fret=float(prop(n,'HarmonicFret','12'));partial=max(2,round(1/(1-2**(-fret/12))))
   pitch=min(127,pitch+round(12*math.log2(partial)));velocity=round(velocity*.85)
  item=dict(on=n['on'],off=off,channel=c,pitch=pitch,velocity=velocity,program=program,pan=[35,93,64,48,80][n['track']],track=n['track'],kind='melodic')
  out.append(item);points=[]
  for segment in [n,*n['segments']]:
   start=segment['on'];end=segment['beat_off'];p=segment['props'];curve=[(start,0.0),(end,0.0)]
   if 'Bended' in p:
    def value(key,default):return float(p.get(key,{'Float':default})['Float'])
    # GPIF 50 units represent one semitone; offsets are percentages of beat.
    curve=[(start+(end-start)*value('BendOriginOffset',0)/100,value('BendOriginValue',0)/50),
           (start+(end-start)*value('BendMiddleOffset1',50)/100,value('BendMiddleValue',0)/50),
           (start+(end-start)*value('BendMiddleOffset2',50)/100,value('BendMiddleValue',0)/50),
           (start+(end-start)*value('BendDestinationOffset',100)/100,value('BendDestinationValue',0)/50)]
    curve=sorted(curve);curve=[(start,curve[0][1]),*curve,(end,curve[-1][1])]
   for t in range(start,min(end,off),12):
    amount=float(np.interp(t,[a for a,b in curve],[b for a,b in curve]))
    if segment['vibrato']:amount+=.16*math.sin(2*math.pi*5.5*seconds(t-start))
    points.append((t,amount))
  flags=int(prop(n,'Slide','0'));nxt=n['next_string']
  if flags:
   if flags&2 and nxt is not None:target=nxt['pitch']-n['pitch']
   elif flags&(4|64):target=-10
   elif flags&8:target=10
   else:raise ValueError(('Unsupported slide flags',flags))
   begin=n['on']+round((off-n['on'])*.65)
   points=[(t,b+(target*max(0,(t-begin)/max(1,off-begin)))) for t,b in points]
  last=None
  for t,b in points:
   assert abs(b)<=12,('Pitch gesture outside TON range',b)
   value=max(0,min(127,round(64+b*64/12)))
   if value!=last:bends.append((t,c,0xe0,value));last=value
 return out,bends

def drums(source,samples,end):
 fmt,ppqn,tracks=midi.read(source/'Drop Zone Drums.mid');assert ppqn==PPQN
 es=midi.merged(tracks);ns,overlap,stray,unclosed=midi.notes(es);assert not stray and not unclosed
 assert all(us==TEMPO for t,us in midi.tempo_map(es))
 byrole={s['role']:s for s in samples};out=[];removed=[];shortened=[]
 for index,(a,b,c,n,v) in enumerate(ns):
  if a>=end:removed.append((a,c,n,v));continue
  role=ROUTING[n];s=byrole[role];duration=s['frames']/s['rate']
  if n==50:duration=min(duration,.10)
  if n==64:duration=min(duration,.16)
  active=[x for x in out if x['off']>a];same=[x for x in active if x['role']==role]
  # Two overlapping voices per drum preserve retriggers and same-tick doubles.
  victims=[]
  if len(same)>=2:victims.append(min(same,key=lambda x:x['on']))
  remaining=[x for x in active if x not in victims]
  if len(remaining)>=8:
   victims.append(min(remaining,key=lambda x:(0 if x['role'] in ('crash','ride','china','open_hat') else 1,x['on'])))
  for x in victims:
   assert x['on']<a,('Simultaneous attacks exceed drum budget',a)
   shortened.append(dict(on=x['on'],old_off=x['off'],new_off=a,role=x['role']));x['off']=a
  # Both source hat articulations are open; future closed-hat routes choke them.
  if role=='closed_hat':
   for x in active:
    if x['role']=='open_hat':x['off']=a
  occupied={x['channel'] for x in out if x['off']>a and x['role']==role};channel=next(c for c in (12,13,14,15) if c not in occupied)
  out.append(dict(on=a,off=min(end,a+ticks(duration)),channel=channel,pitch=s['root'],velocity=v,program=s['program'],role=role,kind='drum',source_channel=c,source_note=n,source_off=b))
 return out,dict(source_hits=len(ns),retained_hits=len(out),cropped_hits=len(removed),cropped_event_sha256=digest(json.dumps(removed,separators=(',',':')).encode()),same_key_overlaps=overlap,shortened_tail_count=len(shortened),retained_event_sha256=digest(json.dumps([(n['on'],n['source_channel'],n['source_note'],n['velocity']) for n in out],separators=(',',':')).encode()))

def main(source):
 samples=prepare(source);gp,end,meters,rows=read_gp(source/'Drop Zone.gp');assert end==279840 and len(gp)==5120
 melody,bends=melodic_notes(gp);percussion,drumreport=drums(source,samples,end);notes=melody+percussion
 ton=build_ton(samples);sequence=encode_seq(notes,bends,end);decoded=seq.decode(sequence)
 expected=sorted((n['on'],n['off'],n['channel'],n['pitch'],n['velocity']) for n in notes)
 assert sorted(decoded['notes'])==expected and decoded['end']==end and decoded['loops']==[0,end]
 assert peak([(n['on'],n['off']) for n in percussion])<=8
 seqaddr=332104;toneaddr=seqaddr+len(sequence);assert toneaddr+len(ton)<=524288,('RAM overflow',len(sequence),len(ton))
 mp=bytearray((R/'assets/cd/CUSTOM.MAP').read_bytes());mp[32:40]=bytes([0x11])+seqaddr.to_bytes(3,'big')+b'\x80'+len(sequence).to_bytes(3,'big');mp[40:48]=bytes([1])+toneaddr.to_bytes(3,'big')+b'\x80'+len(ton).to_bytes(3,'big')
 outputs={}
 for name,data in [('STAGE.SEQ',sequence),('STAGE.TON',ton),('CUSTOM.MAP',bytes(mp))]:
  (R/'assets/cd'/name).write_bytes(data);outputs[name]=dict(bytes=len(data),sha256=digest(data))
 h=R/'src/music_data.h';text=h.read_text()
 import re
 for key,value in {'MF_STAGE_SEQ_BYTES':len(sequence),'MF_STAGE_TON_BYTES':len(ton),'MF_STAGE_SEQ_ADDR':seqaddr,'MF_STAGE_TON_ADDR':toneaddr,'MF_MUSIC_VOLUME':100,'MF_MUSIC_PRIORITY':8,'MF_SFX_PRIORITY':31}.items():text=re.sub(r'(#define '+key+r') \S+',lambda m:m[1]+' '+str(value),text)
 h.write_text(text)
 report=dict(baseline=BASE,root_notes={'open_guitar':48,'muted_guitar':48,'bass':36},source_policy='GP range; retain drum onsets/velocities; crop only events at/after endpoint; no shifts or quantization',ppqn=PPQN,tempo_microseconds=TEMPO,end_tick=end,duration_seconds=seconds(end),gp_note_occurrences=len(rows),gp_attacks=len(gp),melodic_events=len(melody),bend_events=len(bends),mapping=ROUTING,drums=drumreport,samples=[{k:v for k,v in s.items() if k!='pcm'} for s in samples],outputs=outputs,sequence_address=seqaddr,tone_address=toneaddr,sound_ram_high_water=toneaddr+len(ton),sound_ram_free=524288-toneaddr-len(ton),held_melodic_peak=peak([(n['on'],n['off']) for n in melody]),drum_peak=peak([(n['on'],n['off']) for n in percussion]),music_held_peak=peak([(n['on'],n['off']) for n in notes]),sfx_priority=31,music_priority=8,limitations=['Pinch harmonics approximated with fret-derived harmonic-partial transposition of the supplied guitar sample','HOPO has a softer sample retrigger rather than seamless sample-position-preserving legato','Pick slides use a downward pitch sweep; a single pitched sample cannot reproduce scraped-string noise','Cymbal/hat runtime tails are reduced to fit sound RAM; all shortened overlap gates counted','Native allocator must prefer releasing voices under saturation; logical peak is not an audible/hardware slot trace'])
 (R/'assets/music/level1-custom-report.json').write_text(json.dumps(report,indent=2)+'\n')
 # Independent preservation report retains all gameplay SFX hashes unchanged.
 old=json.loads((R/'assets/music/report.json').read_text());old_outputs=old['outputs'];old_outputs.update(outputs)
 regions=[dict(name=n,start=a,size=b,end=a+b) for n,a,b in [('driver/work',0,45056),('transfer/work',45056,4096),('DSP reserved',49152,65600),('DSP program reserved',114752,1344),('PCM/work reserve',116096,32768),('FX.SEQ',148864,328),('FX.TON',149192,182912),('STAGE.SEQ',seqaddr,len(sequence)),('STAGE.TON',toneaddr,len(ton))]]
 current=dict(architecture='SDDRVS 2.10 native Level1 custom PCM/SEQ/TON; private authoring, public runtime assets',level1_custom_report='assets/music/level1-custom-report.json',outputs=old_outputs,sound_ram_regions=regions,sound_ram_high_water=toneaddr+len(ton),sound_ram_unallocated=524288-toneaddr-len(ton),music_held_peak=report['music_held_peak'],drum_tail_cap=8,sfx_reservation=10,release_policy='RR31; driver can retire released musical voices under pressure; physical audibility unverified')
 (R/'assets/music/report.json').write_text(json.dumps(current,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['gp_attacks','melodic_events','bend_events','sound_ram_high_water','sound_ram_free','held_melodic_peak','drum_peak','music_held_peak']},indent=2));print('SEQ',len(sequence),'TON',len(ton),'drums',len(percussion))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
