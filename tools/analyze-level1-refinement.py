from pathlib import Path
import csv,json,collections,sys,math,hashlib,subprocess,argparse
import numpy as np
R=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('capture_root',type=Path);args=parser.parse_args();W=args.capture_root.resolve();sys.path.insert(0,str(R/'tools'));from level1_refinement import read
old_sequence=subprocess.check_output(['git','show','a0982c738f78ac7a00bdbd248c1d5ebe299b6971:assets/cd/STAGE.SEQ'],cwd=R);original=json.load(open(R/'assets/music/level1-custom-report.json'));ref=json.load(open(R/'assets/music/level1-refinement-report.json'));DE=2097151

def event_rows(path):
 return [{k:v if k=='action' else int(v) for k,v in row.items()} for row in csv.DictReader(path.open())]

def analyze(name,sequence,toneaddr):
 path=W/name;rows=event_rows(path/'events.csv');roles={toneaddr+s['tone_offset']:s['role'] for s in original['samples']};programs={toneaddr+s['tone_offset']:s['program'] for s in original['samples']};receipts={};globaloff=[];global_roles=collections.Counter();sfx_ons=collections.Counter();cross=[];live={};first=[]
 for e in rows:
  slot=e['slot'];owner=e['owner']//512
  if e['action']=='N':
   if owner==0:receipts[e['stamp']]=(e['key']>>8,e['key']&255,programs.get(e['sa'],-1));first.append(e['frame'])
   else:sfx_ons[owner]+=1
   live[slot]=e
  else:
   prev=live.pop(slot,None)
   if owner==0 and e['pc']==0x319e and e['ecnt']<DE:globaloff.append(e);global_roles[roles.get(e['sa'],'unknown')]+=1
   if prev and prev['owner']==0 and e['owner']!=0 and e['ecnt']<DE:cross.append(e)
 expected=[(n['channel'],n['pitch'],n['program']) for n in read(sequence)[1] if n['kind']=='note'];observed=[v for _,v in sorted(receipts.items())]
 assert observed==[expected[i%len(expected)] for i in range(len(observed))],('Missing/reordered native music note-on',name)
 peak_music=peak_sfx=peak_total=0;frame=-1;m=s=0;lastframe=0
 for e in csv.DictReader((path/'slots.csv').open()):
  f=int(e['frame']);lastframe=f
  if f!=frame:peak_music=max(peak_music,m);peak_sfx=max(peak_sfx,s);peak_total=max(peak_total,m+s);m=s=0;frame=f
  if int(e['sa']) and int(e['envelope'])<3:
   if int(e['owner'])==0:m+=1
   else:s+=1
 pcm=np.fromfile(path/'audio.pcm',dtype='<i2').astype(np.int32)
 music=np.fromfile(path/'stems.music.s32le',dtype='<i4').reshape(-1,2).astype(float);sfx=np.fromfile(path/'stems.sfx.s32le',dtype='<i4').reshape(-1,2).astype(float)
 begin=first[0]*735;opening=music[begin:begin+88200];song=music[begin:];firstsfx=next(e['frame'] for e in rows if e['action']=='N' and e['owner'])
 assert name=='driver-stress-capture' or firstsfx>=first[0]+120
 def rms(x):return float(np.sqrt(np.mean(x*x)))
 result=dict(frames=lastframe+1,first_music_frame=first[0],first_sfx_frame=firstsfx,native_music_note_ons=len(observed),expected_notes_per_loop=len(expected),complete_loops_observed=len(observed)//len(expected),missing_or_reordered_note_ons=0,global_music_interruptions=len(globaloff),global_interruptions_by_role=dict(global_roles),cross_control_music_steals=len(cross),peak_music_slots=peak_music,peak_sfx_slots=peak_sfx,peak_combined_slots=peak_total,sfx_note_ons_by_control=dict(sfx_ons),mixed_pcm_peak=int(abs(pcm).max()),mixed_pcm_clipped_samples=int(np.sum(abs(pcm)>=32767)),music_opening_rms=rms(opening),music_opening_peak=int(abs(opening).max()),music_combat_rms=rms(song),music_combat_peak=int(abs(song).max()),sfx_stem_peak=int(abs(sfx).max()))
 return result,rows,music,sfx

before,brows,bmusic,bsfx=analyze('compare-before',old_sequence,original['tone_address']);after,arows,amusic,asfx=analyze('compare-final',(R/'assets/cd/STAGE.SEQ').read_bytes(),ref['tone_address']);stress,srows,_,_=analyze('driver-stress-capture',(R/'assets/cd/STAGE.SEQ').read_bytes(),ref['tone_address'])
assert after['global_music_interruptions']==stress['global_music_interruptions']==0
assert after['cross_control_music_steals']==stress['cross_control_music_steals']==0
assert after['mixed_pcm_clipped_samples']==stress['mixed_pcm_clipped_samples']==0
oldfirst=np.flatnonzero(np.max(abs(bsfx),axis=1)>0)[0];newfirst=np.flatnonzero(np.max(abs(asfx),axis=1)>0)[0]
sfx_first_match=np.array_equal(bsfx[oldfirst:oldfirst+4410],asfx[newfirst:newfirst+4410]);assert sfx_first_match,'SFX gain/character mismatch'
assert set(stress['sfx_note_ons_by_control'])==set(range(1,7))

wmusic=(R/'assets/wingsuit/WMUSIC.TON').read_bytes();waddr=376912;wsas=set()
for i in range((int.from_bytes(wmusic[:2],'big')-8)//2):
 v=int.from_bytes(wmusic[8+2*i:10+2*i],'big')+4;wsas.add(waddr+((wmusic[v+3]&15)<<16)+int.from_bytes(wmusic[v+4:v+6],'big'))
trans=[]
for name in ['transition-before','transition-after']:
 rows=event_rows(W/name/'events.csv');first=next(e['frame'] for e in rows if e['action']=='N' and e['owner']==0 and e['sa'] in wsas)
 events=[(e['frame']-first,e['action'],e['owner'],e['key'],e['sa'],e['tl']) for e in rows if e['frame']>=first]
 pcm=np.fromfile(W/name/'audio.pcm',dtype='<i2').reshape(-1,2);trans.append((first,events,pcm))
a,b=trans;end=min(len(a[2])-a[0]*735,len(b[2])-b[0]*735);slicea=a[2][a[0]*735+2205:a[0]*735+end];sliceb=b[2][b[0]*735+2205:b[0]*735+end]
stable_a=[e for e in a[1] if e[0]>=3];stable_b=[e for e in b[1] if e[0]>=3]
assert len(stable_a)==len(stable_b)
parameters_equal=[e[1:] for e in stable_a]==[e[1:] for e in stable_b]
assert parameters_equal
max_jitter=max(abs(x[0]-y[0]) for x,y in zip(stable_a,stable_b))
transition=dict(ordered_note_effect_and_gain_parameters_identical=parameters_equal,max_event_frame_boundary_difference=max_jitter,before_first_level2_music_frame=a[0],after_first_level2_music_frame=b[0],native_event_trace_identical=a[1]==b[1],aligned_pcm_identical=np.array_equal(slicea,sliceb),compared_pcm_frames=len(slicea))
result=dict(baseline_commit='a0982c738f78ac7a00bdbd248c1d5ebe299b6971',core_commit='8926b0c6c347f8c5c755911ddb0ac695420ffbf8',bios='HLE',tested_audio_outputs=ref['outputs'],method='Read-only SCSP KEYON/KEYOFF observer with68K PC and slot ownership; isolated music/SFX stems taken as unchanged mixer contributions; original audio buffers are never modified',before=before,after=after,stress=stress,music_opening_rms_gain_db=20*math.log10(after['music_opening_rms']/before['music_opening_rms']),music_combat_rms_gain_db=20*math.log10(after['music_combat_rms']/before['music_combat_rms']),first_sfx_100ms_bit_identical=sfx_first_match,level2_transition=transition,limitations=['HLE BIOS/software SCSP; owner hardware/listening approval remains required','Input-driven combat plus driver-only stress harness; the latter is a separate test image, not the delivered game','Runtime PCM and per-frame traces are authoring-free native captures; source WAV/GP/MIDI not included'])
(R/'build/LEVEL1-REFINEMENT-PLAYBACK.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
