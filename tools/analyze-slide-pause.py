#!/usr/bin/env python3
"""Analyze read-only native traces for music order, pause and stage ownership."""
from pathlib import Path
import csv,json,sys,re,subprocess,collections
import numpy as np
from level1_refinement import read
R=Path(__file__).resolve().parents[1];W=Path(sys.argv[1]);BASE='d97b5a9e77f418d16f22e408690f038f727e1828'
def sas(path,address):
 b=(R/path).read_bytes();p={}
 for i in range((int.from_bytes(b[:2],'big')-8)//2):
  v=int.from_bytes(b[8+2*i:10+2*i],'big')
  for j in range(b[v+2]+1):
   l=b[v+4+j*32:v+36+j*32];p[address+(l[3]&15)*65536+int.from_bytes(l[4:6],'big')]=i
 return p
def const(path,key):return int(re.search(r'#define '+key+r' (0x[0-9a-fA-F]+|\d+)',(R/path).read_text())[1],0)
L1=sas('assets/cd/STAGE.TON',const('src/music_data.h','MF_STAGE_TON_ADDR'));L2=sas('assets/wingsuit/WMUSIC.TON',const('src/wingsuit_audio_data.h','MF_WS_MUSIC_TON_ADDR'))
expected1=[(n['channel'],n['pitch'],n['program']) for n in read((R/'assets/cd/STAGE.SEQ').read_bytes())[1] if n['kind']=='note']
expected2=[(n['channel'],n['pitch'],n['program']) for n in read((R/'assets/wingsuit/WMUSIC.SEQ').read_bytes())[1] if n['kind']=='note']
def rows(folder):return [{k:v if k=='action' else int(v) for k,v in e.items()} for e in csv.DictReader((W/folder/'events.csv').open())]
def music(es,tones,expected,lo=0,hi=999999):
 ons={e['stamp']:e for e in es if lo<=e['frame']<hi and e['action']=='N' and e['owner']==0 and e['sa'] in tones};ordered=[e for _,e in sorted(ons.items())]
 assert [(e['key']>>8,e['key']&255,tones[e['sa']]) for e in ordered]==[expected[i%len(expected)] for i in range(len(ordered))]
 return ordered
def pause(folder,first,last):
 es=rows(folder);ons=music(es,L1,expected1,0,17000 if folder=='pause-loop' else 3100 if folder=='pause-short' else 15500)
 active=[e for e in ons if first<=e['frame']<last];sfx=[e for e in es if e['action']=='N' and e['owner'] and first<=e['frame']<last]
 assert active and not sfx
 pc=collections.Counter(hex(e['pc']) for e in es if e['action']=='F' and e['owner']==0 and first<=e['frame']<last)
 assert not any(e['action']=='F' and e['owner']==0 and e['pc']==0x319e and e['ecnt']<2097151 for e in es)
 pcm=np.fromfile(W/folder/'audio.pcm',dtype='<i2').astype('i4');assert not np.any(abs(pcm)>=32767)
 return dict(music_note_ons=len(ons),music_note_ons_while_paused=len(active),sfx_note_ons_while_paused=len(sfx),missing_or_reordered_music_note_ons=0,music_noteoff_pcs_while_paused=dict(pc),mixed_peak=int(abs(pcm).max()),clipped_samples=0),ons,es
long,ons,es=pause('pause-loop',2305,16300);assert len([e for e in ons if 2305<=e['frame']<16300])>len(expected1)
hashes=[e['world_hash'] for e in csv.DictReader((W/'pause-loop/video.csv').open()) if 2350<=int(e['frame'])<16250];assert len(hashes)==13900 and len(set(hashes))==1
long['identical_paused_world_frames']=len(hashes);long['complete_music_loop_during_pause']=True
short,short_ons,se=pause('pause-short',2305,2500)
first2=next(e['frame'] for e in se if e['action']=='N' and e['owner']==0 and e['sa'] in L2);music(se,L2,expected2,first2)
assert not any(e['action']=='N' and e['owner']==0 and e['sa'] in L1 and e['frame']>=first2 for e in se)
short.update(level2_first_music_frame=first2,level1_notes_after_level2_start=0,transition_passed=True)
late={}
for folder in ('pause-loop','pause-loop-repeat','baseline-late','pause-loop-baseline'):
 # Baseline L2 has the original bank address, distinct from current shifted bank.
 tones=L2 if folder in ('pause-loop','pause-loop-repeat') else sas('assets/wingsuit/WMUSIC.TON',352124)
 late[folder]=any(e['action']=='N' and e['owner']==0 and e['sa'] in tones and e['frame']>17000 for e in rows(folder))
assert late['pause-loop']==late['pause-loop-repeat'],'Late transition repeat disagrees'
assert late['pause-loop'] or not late['baseline-late'],'Candidate late transition failed while approved unpaused late transition passed'
result=dict(baseline=BASE,core='8926b0c6c347f8c5c755911ddb0ac695420ffbf8',bios='HLE',method='Read-only native note/owner/PCM traces and video hashes; no emulated RAM writes',long_pause=long,short_pause_and_transition=short,late_handoff_success=late,late_handoff_limitation=('E108 after a late handoff is reproduced on approved D97 without pausing and on candidate after full-loop pause; unchanged startup code. This required late scenario does NOT pass; no claim of hardware validation.' if not late['pause-loop'] else 'Late transition passed in this capture'),level2=json.loads((W/'level2-playback.json').read_text()))
if (W/'pause-driver/events.csv').exists():
 driver,dons,des=pause('pause-driver',430,15000);driver['complete_music_loop_during_pause']=len([e for e in dons if 430<=e['frame']<15000])>len(expected1)
 before=[e for e in des if e['action']=='N' and e['owner']==1536 and e['frame']<430];assert before
 driver['explosion_note_on_before_pause_frame']=before[0]['frame'];driver['pause_request_test_clock']=315
 result['native_driver_sustain_explosion_pause']=driver
(R/'docs/slide-pause-playback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
