from pathlib import Path
import csv,json,collections,numpy as np
R=Path(__file__).resolve().parents[1];report=json.loads((R/'assets/music/level1-custom-report.json').read_text());address={report['tone_address']+s['tone_offset']:s['role'] for s in report['samples']};roles=collections.Counter();first={};musicmax=sfxmax=totalmax=0;held=sf=0;prev=None;receipts={};wraps=collections.Counter();phase={};framesfirstchord=[];stampnotes=[]
with (R/'build/level1-playback/slots.csv').open() as f:
 for row in csv.DictReader(f):
  r={k:int(v) for k,v in row.items()};frame=r['frame']
  if prev!=frame:
   musicmax=max(musicmax,held);sfxmax=max(sfxmax,sf);totalmax=max(totalmax,held+sf);held=sf=0;prev=frame
  if r['stamp'] and r['stamp'] not in receipts:
   receipts[r['stamp']]=(frame,r['owner'],r['key'],r['sa'])
   if r['owner']==0 and r['key']==38:framesfirstchord.append(frame)
  if r['envelope']<3 and r['sa']:
   if r['owner']==0:
    held+=1;role=address.get(r['sa'],'unknown');roles[role]+=1;first.setdefault(role,frame)
    key=(r['slot'],r['stamp'])
    if key in phase and r['phase']<phase[key]:wraps[role]+=1
    phase[key]=r['phase']
   else:sf+=1
raw=(R/'build/level1-playback/audio.pcm').read_bytes();x=np.frombuffer(raw,dtype='<i2').astype(float)
summary=dict(emulator='libretro Yabause',core_commit='8926b0c6c347f8c5c755911ddb0ac695420ffbf8',bios='HLE',frames=prev+1,first_music_frame=min(frame for frame,owner,key,sa in receipts.values() if owner==0),observed_native_music_peak=musicmax,observed_native_sfx_peak=sfxmax,observed_native_total_peak=totalmax,observed_music_roles=dict(roles),first_role_frames=first,observed_phase_wraps=dict(wraps),pcm_peak=int(max(abs(x))),pcm_clipped_samples=int(sum(abs(x)>=32767)),pcm_rms=float(np.sqrt(np.mean(x*x))),pcm_sha256=__import__('hashlib').sha256(raw).hexdigest(),music_receipts=sum(owner==0 for frame,owner,key,sa in receipts.values()),first_guitar_key_receipt_frames=framesfirstchord,limitations=['Read-only frame-sampled driver/native-SCSP observation; not complete event receipts','HLE BIOS; does not establish real-Saturn behavior or listening approval','Pause/resume and mixed two-player SFX exercised by controller inputs; no emulated RAM writes'])
initial={38,301,562,825,1062,1325,1586,1849,2074}
groups=collections.defaultdict(set)
for frame,owner,key,sa in receipts.values():
 if owner==0:groups[frame].add(key)
loops=[f for f in sorted(groups) if f>summary['first_music_frame']+100 and initial.issubset(groups[f]|groups.get(f+1,set()))]
summary['observed_loop_restart_frame']=loops[0] if loops else None
assert summary['observed_loop_restart_frame'] is not None
assert set(roles)==set(s['role'] for s in report['samples'])-{'closed_hat'}
assert summary['pcm_peak']>0 and summary['pcm_clipped_samples']==0
summary['tested_audio_outputs']=report['outputs']
summary.pop('first_guitar_key_receipt_frames')
print(json.dumps(summary,indent=2));(R/'build/LEVEL1-EMULATOR.json').write_text(json.dumps(summary,indent=2)+'\n')
