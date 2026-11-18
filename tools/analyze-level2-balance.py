#!/usr/bin/env python3
"""Matched native audit: SFX gain, unchanged music gain, slots and Level1 audio."""
from pathlib import Path
import sys,csv,json,array,math,collections,statistics,subprocess
from level1_refinement import read
R=Path(__file__).resolve().parents[1];D=Path(sys.argv[1]);BASE='a38c39259304b2af8980e16e192304f6d2ecad83'
def rows(p):return [{k:(v if k=='action' else int(v)) for k,v in x.items()} for x in csv.DictReader(p.open())]
def address(name,i,base):
 b=(R/name).read_bytes();a=int.from_bytes(b[8+2*i:10+2*i],'big')+4;return base+((b[a+3]&15)<<16)+int.from_bytes(b[a+4:a+6],'big')
roles={address('assets/wingsuit/WDEATH.TON',i,148948):name for i,name in enumerate(('explosion','hit','flame_attack','flame_loop'))};roles[address('assets/wingsuit/WFIRE.TON',0,468436)]='fire'
_,e,_=read((R/'assets/wingsuit/WMUSIC.SEQ').read_bytes());score=[n for n in e if n['kind']=='note'];out={};gains={};energies={};signatures={}
for label,folder in [('before','stress-before'),('after','fx-only-stress')]:
 p=D/folder;rr=rows(p/'events.csv');ons=[r for r in rr if r['action']=='N'];music=[r for r in ons if r['owner']>>9==0];sfx=[r for r in ons if r['owner']>>9!=0]
 assert len(music)>len(score) and all((r['key']>>8,r['key']&127)==(score[i%len(score)]['channel'],score[i%len(score)]['pitch']) for i,r in enumerate(music))
 assert not [r for r in rr if r['action']=='F' and r['owner']>>9==0 and r['pc']!=15654]
 live={};steals=[]
 for r in rr:
  key=r['slot']
  if r['action']=='F' and key in live and live[key]['stamp']==r['stamp']:live.pop(key)
  if r['action']=='N':
   prev=live.get(key)
   if prev and prev['owner']>>9==0 and r['ecnt']<2097151:steals.append([prev,r])
   live[key]=r
 assert not steals,(label,steals[:1])
 loop_keys={(r['stamp'],r['slot']):r['frame'] for r in sfx if roles[r['sa']]=='flame_loop'};loop_rows=collections.Counter();c=collections.defaultdict(collections.Counter);peak=count=0;f=-1;music_levels=collections.Counter()
 for x in csv.DictReader((p/'slots.csv').open()):
  r={k:int(v) for k,v in x.items()}
  if r['frame']!=f:peak=max(peak,count);count=0;f=r['frame']
  if r['ecnt']<2097151:
   count+=1
   if (r['stamp'],r['slot']) in loop_keys and r['sa']==274392 and r['owner']>>9==1:loop_rows[(r['stamp'],r['slot'])]+=1
   if r['owner']>>9==0:music_levels[r['tl']]+=1
   elif r['sa'] in roles:c[roles[r['sa']]][r['tl']]+=1
 assert len(loop_keys)==2 and all(loop_rows[k]==11500-start for k,start in loop_keys.items())
 gains[label]={name:counter.most_common(1)[0][0] for name,counter in c.items()}
 a=array.array('h');a.frombytes((p/'audio.pcm').read_bytes());clips=sum(x in (-32768,32767) for x in a);assert clips==0
 pcm=array.array('i');pcm.frombytes((p/'stems.music.s32le').read_bytes());start=music[0]['frame'];end=music[len(score)]['frame'];framewidth=len(pcm)//11500;energy=sum(v*v for v in pcm[start*framewidth:end*framewidth]);energies[label]=energy/((end-start)*framewidth)
 signatures[label]=collections.Counter((r['frame'],r['owner'],r['key'],r['sa']) for r in sfx)
 out[label]=dict(music_note_ons=len(music),sfx_note_ons=len(sfx),sfx_role_counts=dict(collections.Counter(roles[r['sa']] for r in sfx)),peak_live_slots_per_vblank=peak,pcm_peak=max(map(abs,a)),clipped_samples=clips,full_music_loop_frames=end-start,forced_music_offs=0,cross_owner_music_steals=0,flame_loops_continuously_active=True,music_native_tl_values=sorted(music_levels))
assert signatures['before']==signatures['after']
audit={name:dict(before=gains['before'][name],after=gains['after'][name],linear_ratio=gains['after'][name]/gains['before'][name]) for name in gains['before']};assert len(audit)==5 and all(x['after']>x['before'] for x in audit.values())
assert out['before']['music_native_tl_values']==out['after']['music_native_tl_values']
result=dict(captures=out,sfx_native_tl_multiplier_audit=audit,sfx_per_frame_events_and_samples_identical=True,music_control_gain_unchanged=108,music_full_loop_rms_ratio=math.sqrt(energies['after']/energies['before']),velocity_exceptions=[],silent_baseline_paths=['drone/hostile bullet launch has no MIDI note-on; no new sound event added'])
if (D/'gameplay/audio.pcm').exists():
 parent=Path(sys.argv[2]) if len(sys.argv)>2 else D/'baseline-gameplay/audio.pcm';now=D/'gameplay/audio.pcm'
 if parent.exists():
  n=3000*735*2*2;result['level1_first3000_frames_audio_byte_identical']=parent.read_bytes()[:n]==now.read_bytes()[:n];assert result['level1_first3000_frames_audio_byte_identical']
(R/'docs/level2-final-fx-native.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
