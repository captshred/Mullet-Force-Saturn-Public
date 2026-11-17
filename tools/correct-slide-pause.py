#!/usr/bin/env python3
"""Targeted native runtime correction; reads no private authoring files."""
from pathlib import Path
import subprocess,json,hashlib,struct
from level1_refinement import read,write,signature,curve
R=Path(__file__).resolve().parents[1];BASE='d97b5a9e77f418d16f22e408690f038f727e1828'
def original(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def corrected(data):
 h,events,end=read(data);notes=[n for n in events if n['kind']=='note'];out=[dict(e) for e in events];affected=[];used=set()
 for n in notes:
  c=curve(n,events)
  if not(n['program']==0 and n['channel'] in (4,5) and n['off']-n['on']==960 and len(c)>2 and c[0]==(0,64) and c[-1] in ((480,85),(480,32))):continue
  assert all(t>240 for t,v in c[1:])
  a=n['on']+240;b=n['on']+720
  assert not any(m is not n and m['channel']==n['channel'] and m['on']<b and m['off']>a for m in notes),'Slide shares an active pitch lane'
  affected.append(dict(channel=n['channel'],note_on=n['on'],note_off=n['off'],pitch=n['pitch'],destination_bend=c[-1][1],measure=n['on']//3840+1,beat_offset_ticks=n['on']%3840,hold_ticks=240,before_movement_ticks=240,after_movement_ticks=480,original_curve=c))
  for i,e in enumerate(events):
   if e['kind']=='event' and e['payload'][0]==224+n['channel'] and a<e['on']<=n['on']+480:
    assert i not in used;used.add(i);out[i]['on']=a+2*(e['on']-a)
  # Explicit neutral anchor marks the end of the preserved initial hold.
  out.append(dict(kind='event',on=a,payload=bytes([224+n['channel'],64])))
 assert len(affected)==203
 out.sort(key=lambda e:e['on']);result=write(h,out);nh,ne,nt=read(result)
 assert h==nh and end==nt
 assert [signature(n) for n in notes]==[signature(n) for n in ne if n['kind']=='note']
 return result,affected
if __name__=='__main__':
 src=original('assets/wingsuit/WMUSIC.SEQ');data,affected=corrected(src);(R/'assets/wingsuit/WMUSIC.SEQ').write_bytes(data)
 old_size=len(src);new_size=len(data);delta=new_size-old_size
 # Only the music stream length and subsequent contiguous bank addresses move.
 for name in ('WMUSIC.MAP','WFIRE.MAP'):
  b=bytearray(original('assets/wingsuit/'+name));b[37:40]=new_size.to_bytes(3,'big')
  for off in (40,48):
   if off<len(b)-8:b[off+1:off+4]=(int.from_bytes(b[off+1:off+4],'big')+delta).to_bytes(3,'big')
  (R/'assets/wingsuit'/name).write_bytes(b)
 import re
 h=original('src/wingsuit_audio_data.h').decode()
 for key in ('MUSIC_SEQ_BYTES','MUSIC_TON_ADDR','FIRE_TON_ADDR'):
  h=re.sub(r'(#define MF_WS_'+key+r') (\d+)',lambda m:m[1]+' '+str(int(m[2])+delta),h)
 (R/'src/wingsuit_audio_data.h').write_text(h)
 report=dict(baseline=BASE,affected_note_trajectories=len(affected),chord_onsets=len({a['note_on'] for a in affected}),hold_ms=240*.291262/960*1000,before_movement_ms=240*.291262/960*1000,after_movement_ms=480*.291262/960*1000,sequence_bytes=new_size,sequence_delta=delta,sound_ram_high_water=506192+delta,sound_ram_free=18096-delta,affected=affected)
 assert report['sound_ram_free']>=0
 (R/'docs/slide-pause-report.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='affected'})
