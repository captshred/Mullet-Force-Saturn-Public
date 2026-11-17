#!/usr/bin/env python3
"""Refine the approved runtime files only; no GP/MIDI/WAV authoring input."""
from pathlib import Path
import subprocess,json,hashlib,struct,re,collections
from level1_refinement import BASE,read,write,signature,peak,curve
R=Path(__file__).resolve().parents[1]
def original(name):return subprocess.check_output(['git','show',BASE+':'+name],cwd=R)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 src=original('assets/cd/STAGE.SEQ');header,events,end=read(src);notes=[e for e in events if e['kind']=='note']
 left=[n for n in notes if n['pan']==35 and n['program'] in (0,1)];right=[n for n in notes if n['pan']==93 and n['program'] in (0,1)]
 assert (len(left),len(right))==(2025,2023)
 def key(n):return tuple(n[k] for k in ('on','off','pitch','velocity','program'))
 left_keys={key(n):n for n in left};removed=[];unique=[]
 for n in right:
  other=left_keys.get(key(n))
  if other is not None and curve(other,events)==curve(n,events):removed.append(n)
  else:unique.append(n)
 assert len(removed)==2017 and len(unique)==6,'Unexpected unique musical material: review before changing'
 remove_ids={id(n) for n in removed};new=[];bank_resets=pan_changes=channel_changes=0
 for e in events:
  if id(e) in remove_ids:continue
  e=e.copy()
  if e['kind']=='event':
   p=e['payload']
   if p[0]&240==176:
    c,controller,value=p
    if controller==10 and value in (35,93):value=64;pan_changes+=1
    if controller==7:assert value==112;value=127;channel_changes+=1
    if controller==123:assert e['on']==end;controller=32;value=1;bank_resets+=1
    e['payload']=bytes([c,controller,value])
  new.append(e)
 sequence=write(header,new)
 # Preserve SFX stream size, all gates, notes, programs, tempo and event clocks.
 # CC123 is global in this pinned driver. Re-selecting the already selected bank0
 # at the same timestamp is benign, supported, and scoped to that SFX context.
 fx=bytearray(original('assets/cd/FX.SEQ'));sfx_replacements=0
 for song in range(int.from_bytes(fx[:2],'big')):
  start=struct.unpack_from('>I',fx,2+4*song)[0];off=struct.unpack_from('>H',fx,start+4)[0];nextstart=struct.unpack_from('>I',fx,2+4*(song+1))[0] if song+1<int.from_bytes(fx[:2],'big') else len(fx)
  positions=[i for i in range(start+off,nextstart-3) if fx[i:i+3]==bytes([0xb0,123,0])];assert len(positions)==1
  fx[positions[0]+1]=32;sfx_replacements+=1
  oldh,olde,oldt=read(original('assets/cd/FX.SEQ'),song);newh,newe,newt=read(bytes(fx),song)
  assert oldh==newh and oldt==newt
  assert [signature(n) for n in olde if n['kind']=='note']==[signature(n) for n in newe if n['kind']=='note']
 tone=bytearray(original('assets/cd/STAGE.TON'));old_tone=bytes(tone);tl_targets=[0,0,0,2,4,14,14,18,16,18,7,7,7];tl_changes=[]
 for i,target in enumerate(tl_targets):
  voice=int.from_bytes(tone[8+2*i:10+2*i],'big');offset=voice+4+15;before=tone[offset];assert target<=before;tone[offset]=target;tl_changes.append(dict(program=i,offset=offset,before=before,after=target,boost_db=(before-target)*.375))
 permitted={e['offset'] for e in tl_changes};assert all(a==b or i in permitted for i,(a,b) in enumerate(zip(old_tone,tone)))
 seqaddr=332104;toneaddr=seqaddr+len(sequence);mp=bytearray(original('assets/cd/CUSTOM.MAP'));mp[37:40]=len(sequence).to_bytes(3,'big');mp[41:44]=toneaddr.to_bytes(3,'big')
 outputs={}
 for name,data in [('STAGE.SEQ',sequence),('STAGE.TON',bytes(tone)),('FX.SEQ',bytes(fx)),('CUSTOM.MAP',bytes(mp))]:
  (R/'assets/cd'/name).write_bytes(data);outputs[name]=dict(bytes=len(data),sha256=sha(data))
 h=original('src/music_data.h').decode()
 for key,value in {'MF_MUSIC_VOLUME':108,'MF_STAGE_SEQ_BYTES':len(sequence),'MF_STAGE_TON_ADDR':toneaddr}.items():h=re.sub(r'(#define '+key+r') \S+',lambda m:m[1]+' '+str(value),h)
 (R/'src/music_data.h').write_text(h)
 result_events=read(sequence)[1];result_notes=[n for n in result_events if n['kind']=='note'];expected=[signature(n) for n in notes if id(n) not in remove_ids]
 assert [signature(n) for n in result_notes]==expected
 assert [signature(n) for n in result_notes if n['channel']>=12]==[signature(n) for n in notes if n['channel']>=12]
 assert all(n['pan']==(64 if old['pan'] in (35,93) else old['pan']) for n,old in zip(result_notes,[x for x in notes if id(x) not in remove_ids]))
 report=dict(baseline_tag='the-one-level1-custom-audio-definitive',baseline_commit=BASE,source_seq_sha256=sha(src),removed_rhythm='redundant notes of right rhythm guitar, original pan93',retained_rhythm='complete left rhythm guitar, original pan35, now centered64',left_notes=len(left),right_notes=len(right),removed_identical_notes=len(removed),right_unique_notes_preserved=[{k:n[k] for k in ('on','off','pitch','velocity','program')} for n in unique],before_music_notes=len(notes),after_music_notes=len(result_notes),drum_notes=sum(n['channel']>=12 for n in result_notes),before_music_held_peak=peak(notes),after_music_held_peak=peak(result_notes),before_music_50ms_release_peak=peak(notes,66),after_music_50ms_release_peak=peak(result_notes,66),rhythm_held_before=peak(left+right),rhythm_held_after=peak(left+unique),music_volume_before=100,music_volume_after=108,channel_volume_before=112,channel_volume_after=127,instrument_tl_changes=tl_changes,sfx_gain_changed=False,sfx_panic_events_replaced=sfx_replacements,music_global_cleanup_events_replaced=bank_resets,pcm_payload_unchanged=True,loops_roots_envelopes_unchanged=True,sound_ram_high_water=toneaddr+len(tone),sound_ram_free=524288-toneaddr-len(tone),sequence_address=seqaddr,tone_address=toneaddr,outputs=outputs,dropout_cause='SFX terminal CC123 dispatches to global all-notes-off at3172, releasing all32 slots. Replaced with same-tick same-bank select; driver and SFX scheduling unchanged.')
 (R/'assets/music/level1-refinement-report.json').write_text(json.dumps(report,indent=2)+'\n')
 master=json.loads(original('assets/music/report.json'));master['outputs'].update(outputs);master['level1_refinement_report']='assets/music/level1-refinement-report.json';master['architecture']='SDDRVS2.10 Level1 mono rhythm/music gain/global-SFX-panic correction; runtime PCM preserved';master['sound_ram_regions'][-2].update(size=len(sequence),end=toneaddr);master['sound_ram_regions'][-1].update(start=toneaddr,end=toneaddr+len(tone));master['sound_ram_high_water']=report['sound_ram_high_water'];master['sound_ram_unallocated']=report['sound_ram_free'];master['music_held_peak']=report['after_music_held_peak'];master.pop('sfx_reservation',None);master['voice_policy']='Unchanged native allocation; scoped SFX bank selectors instead of global panic; duplicate-rhythm capacity recovered';(R/'assets/music/report.json').write_text(json.dumps(master,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['removed_identical_notes','after_music_notes','before_music_held_peak','after_music_held_peak','before_music_50ms_release_peak','after_music_50ms_release_peak','sfx_panic_events_replaced','sound_ram_high_water','sound_ram_free']},indent=2))
if __name__=='__main__':main()
