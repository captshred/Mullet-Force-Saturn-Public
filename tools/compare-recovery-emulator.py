#!/usr/bin/env python3
"""Compare native receipts/mixer state and PCM, without claiming bit equivalence."""
from pathlib import Path
import csv,json,array,math,hashlib,argparse
p=argparse.ArgumentParser();p.add_argument('golden',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
def analyze(path):
 last={};seen=set();on=[];holds={0:set(),1:set()};wraps={0:0,1:0};phases={};levels={};sounding=set()
 for r in csv.DictReader((path/'slots.csv').open()):
  f,slot,owner,key,eg,stamp,sa,phase,env,kb,tl,out=map(int,r.values());ident=(owner,key,stamp);control=owner>>9
  if f>1000 and stamp and stamp not in seen:
   on.append((f,stamp,control,key));seen.add(stamp)
  last[slot]=ident
  if f>1150 and env<3 and sa:
   sounding.add(control);levels.setdefault(str(control),set()).add(tl)
  if 1220<=f<=1300 and owner==512 and key in (61,317) and env==2:
   player=key>>8;assert sa==281592,(path,'wrong Loop PCM',sa)
   holds[player].add(f)
   if player in phases and phase<phases[player]:wraps[player]+=1
   phases[player]=phase
 for player in range(2):assert len(holds[player])==81 and wraps[player]>=3,(path,player,'missing native sustain',len(holds[player]),wraps[player])
 assert sounding==set(range(8)),(path,'missing native voice/control',sounding)
 on.sort();music=[key for f,stamp,c,key in on if c==0]
 assert len(music)>200
 pcm=array.array('h',(path/'audio.pcm').read_bytes());peak=max(map(abs,pcm));assert peak<32767
 return {'music_receipt_count':len(music),'first_music_frame':next(f for f,stamp,c,key in on if c==0),'sounding_controls':sorted(sounding),'dual_flame_native_sustain_frames':[len(holds[i]) for i in range(2)],'dual_flame_phase_wraps':wraps,'music_sequence':music,'pcm_peak':peak,'pcm_rms':math.sqrt(sum(v*v for v in pcm)/len(pcm)),'pcm_sha256':hashlib.sha256(pcm.tobytes()).hexdigest(),'levels':{k:sorted(v) for k,v in levels.items()}}
g=analyze(a.golden);c=analyze(a.candidate)
common=0
for x,y in zip(g['music_sequence'],c['music_sequence']):
 if x!=y:break
 common+=1
assert common>=100,('music receipt mismatch',common)
for r in [g,c]:r.pop('music_sequence')
report={'core_commit':'8926b0c6c347f8c5c755911ddb0ac695420ffbf8','frames_per_image':2200,'method':'Identical controller input; read-only driver receipt and native legacy SCSP mixer-state observation. No emulated RAM/instruction changes.','golden':g,'candidate':c,'common_music_note_prefix':common,'limitations':['Short gameplay smoke, not whole-score or long-duration emulator stress.','Executables and PCM are not byte-identical; exact private source reconstruction is not claimed.', 'Frame-sampled slot assignments can observe driver updates mid-write; later sampled note identities are not a whole-score receipt proof.','Original gameplay/Flame STOP diagnostic uses cached EG, which is unreliable in this HLE core; native decay-sustain/phase proves the sampled hold.','Owner WebRetro approval remains required.']}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
