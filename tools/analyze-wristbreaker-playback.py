#!/usr/bin/env python3
"""Analyze native observer captures; no source authoring media required."""
from pathlib import Path
import sys,csv,json,subprocess,collections,math,hashlib
import numpy as np
from level1_refinement import read
R=Path(__file__).resolve().parents[1];W=Path(sys.argv[1]);BASE='17445b421bcafd8d5c974d624ddc2a34e768d725'
def asset(name,before):return subprocess.check_output(['git','show',BASE+':'+name],cwd=R) if before else (R/name).read_bytes()
def analyze(folder,before=False):
 p=W/folder;ton=asset('assets/wingsuit/WMUSIC.TON',before);header=asset('src/wingsuit_audio_data.h',before).decode();import re
 toneaddr=int(re.search(r'MF_WS_MUSIC_TON_ADDR (\d+)',header)[1]);sas=set()
 for i in range((int.from_bytes(ton[:2],'big')-8)//2):
  a=int.from_bytes(ton[8+2*i:10+2*i],'big')
  for j in range(ton[a+2]+1):
   l=ton[a+4+j*32:a+36+j*32];sas.add(toneaddr+(l[3]&15)*65536+int.from_bytes(l[4:6],'big'))
 rows=[{k:v if k=='action' else int(v) for k,v in row.items()} for row in csv.DictReader((p/'events.csv').open())]
 first=next(e['frame'] for e in rows if e['action']=='N' and e['owner']==0 and e['sa'] in sas);rows=[e for e in rows if e['frame']>=first]
 expected=[n for n in read(asset('assets/wingsuit/WMUSIC.SEQ',before))[1] if n['kind']=='note'];ons={e['stamp']:e for e in rows if e['action']=='N' and e['owner']==0};ordered=[e for _,e in sorted(ons.items())]
 assert [(e['key']>>8,e['key']&255) for e in ordered]==[(expected[i%len(expected)]['channel'],expected[i%len(expected)]['pitch']) for i in range(len(ordered))],folder+' missing/reordered note-on'
 loop_frames=ordered[len(expected)]['frame']-ordered[0]['frame']
 native_frames_per_tick=loop_frames/541440
 drum_pcm={}
 if not before:
  a=int.from_bytes(ton[10:12],'big')
  for j in range(ton[a+2]+1):
   l=ton[a+4+j*32:a+36+j*32];key=l[0];frames=int.from_bytes(l[8:10],'big');rate=44100/2**((l[25]-key)/12);drum_pcm[key]=(frames,frames/rate*960/.291262)
 forced=collections.Counter();live={};cross=0;early=0;normaloff=0;cut_tails=0;completed_tails=0
 bystamp={e['stamp']:(e,expected[i%len(expected)]) for i,e in enumerate(ordered)}
 for e in rows:
  if e['action']=='N':live[e['slot']]=e
  else:
   prev=live.pop(e['slot'],None)
   if e['pc']==0x319e and e['ecnt']<2097151:forced[str(e['owner']//512)]+=1
   if prev and prev['owner']==0 and e['owner']!=0 and e['ecnt']<2097151:cross+=1
   if e['owner']==0 and e['pc']==0x3d26 and e['stamp'] in bystamp:
    on,n=bystamp[e['stamp']];normaloff+=1;duration=(n['off']-n['on'])*native_frames_per_tick
    if e['frame']-on['frame']<duration-2:early+=1
    if n['channel']==0 and n['pitch'] in drum_pcm:
     frames,nominal=drum_pcm[n['pitch']]
     if n['off']-n['on']>nominal+1:
      if e['ecnt']<2097151 and e['phase']<frames*1024:cut_tails+=1
      else:completed_tails+=1
 peakm=peaks=peakt=0;frame=-1;m=s=0;lastframe=0
 for e in csv.DictReader((p/'slots.csv').open()):
  f=int(e['frame']);lastframe=f
  if f<first:continue
  if f!=frame:peakm=max(peakm,m);peaks=max(peaks,s);peakt=max(peakt,m+s);frame=f;m=s=0
  if int(e['sa']) and int(e['envelope'])<3:
   if int(e['owner'])==0:m+=1
   else:s+=1
 peakm=max(peakm,m);peaks=max(peaks,s);peakt=max(peakt,m+s)
 pcm=np.fromfile(p/'audio.pcm',dtype='<i2').astype(np.int32);music=np.fromfile(p/'stems.music.s32le',dtype='<i4').reshape(-1,2)[first*735:];sfx=np.fromfile(p/'stems.sfx.s32le',dtype='<i4').reshape(-1,2)[first*735:]
 def rms(x):return float(np.sqrt(np.mean(x.astype('f8')**2)))
 result=dict(frames=lastframe+1,first_music_frame=first,notes_per_loop=len(expected),native_loop_frames=loop_frames,native_note_ons=len(ordered),complete_loops=len(ordered)//len(expected),missing_or_reordered_note_ons=0,global_forced_keyoffs_by_control=dict(forced),global_music_interruptions=forced['0'],cross_control_music_steals=cross,normal_music_noteoffs_observed=normaloff,premature_music_noteoffs_over_2_frames=early,ordinary_one_shot_tails_cut=cut_tails,ordinary_one_shots_finished_before_gate=completed_tails,peak_music_slots=peakm,peak_sfx_slots=peaks,peak_combined_slots=peakt,mixed_peak=int(abs(pcm).max()),clipped_samples=int(np.sum(abs(pcm)>=32767)),music_rms=rms(music),music_opening_2s_rms=rms(music[:88200]),music_peak=int(abs(music).max()),sfx_peak=int(abs(sfx).max()),sfx_note_ons_by_control=dict(collections.Counter(e['owner']//512 for e in rows if e['action']=='N' and e['owner'])))
 return result
result=dict(baseline=BASE,core='8926b0c6c347f8c5c755911ddb0ac695420ffbf8',bios='HLE',method='Read-only native KEYON/KEYOFF/owner/PCM stem observations; no emulated RAM writes',captures={})
for folder,before in [('capture-before',True),('capture-after',False),('capture-stress-before',True),('capture-stress',False),('capture-music',False)]:
 if (folder!='capture-music' or '--skip-music' not in sys.argv) and (W/folder/'events.csv').exists():result['captures'][folder]=analyze(folder,before)
a=result['captures']['capture-after'];b=result['captures']['capture-before'];result['music_rms_gain_db']=20*math.log10(a['music_rms']/b['music_rms'])
old=np.memmap(W/'capture-before/audio.pcm',dtype='<i2',mode='r');new=np.memmap(W/'capture-after/audio.pcm',dtype='<i2',mode='r');result['level1_prefix_2200_frames_bit_identical']=bool(np.array_equal(old[:2200*735*2],new[:2200*735*2]))
for folder in ('capture-after','capture-stress','capture-music'):
 if folder in result['captures']:
  x=result['captures'][folder];assert x['global_music_interruptions']==x['cross_control_music_steals']==x['premature_music_noteoffs_over_2_frames']==x['ordinary_one_shot_tails_cut']==x['clipped_samples']==0,(folder,x)
result['limitations']=['Software SCSP and HLE BIOS; hardware/listening approval remains required','Game combat reaches game over; separate real-driver stress keeps all SFX requests active through the full song loop','Bank sizes change CD-read duration; first Level2 music frame differs while the readiness/start protocol is unchanged','The recovered native score has no muted-guitar program events or named GP tracks; no palm mutes or lead classifications were invented','SD3 poly-pressure events do not become new notes; the approved sample kit uses note-on/velocity articulation','Gate timing is evaluated against the measured native sequencer clock; nominal PPQN/tempo converted at60fps overestimates this pinned driver/emulator loop duration by about1.8%, also present in baseline']
(R/'build/WRISTBREAKER-PLAYBACK.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
