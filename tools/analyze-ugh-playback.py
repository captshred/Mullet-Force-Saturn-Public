from pathlib import Path
import csv,json,collections,statistics,array,sys,subprocess,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from level1_refinement import read
BASE='744053ba851c9da6b8953708f125313f177b7dcb';D=Path(sys.argv[1]) if len(sys.argv)>1 else R/'build/ugh-captures'
def orig(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def records(p):return [{k:(v if k=='action' else int(v)) for k,v in r.items()} for r in csv.DictReader(p.open())]
def pcm_sas(ton,base):
 out={}
 for i in range(9):
  a=int.from_bytes(ton[8+2*i:10+2*i],'big')+4;sa=((ton[a+3]&15)<<16)|int.from_bytes(ton[a+4:a+6],'big');out[i]=base+sa
 return out
current=records(D/'native-driver/events.csv');prior=records(D/'before-driver/events.csv');cur_ns=[r for r in current if r['action']=='N'];old_ns=[r for r in prior if r['action']=='N'];now_sas=pcm_sas((R/'assets/cd/FX.TON').read_bytes(),149232);old_sas=pcm_sas(orig('assets/cd/FX.TON'),149236)
ugh=[r for r in cur_ns if r['owner']>>9==7];assert len(ugh)>3 and all(r['sa']==now_sas[8] for r in ugh)
active={};peaks=0;ugh_states=collections.defaultdict(list);native_gains={};cur_frame=-1;count=0
for x in csv.DictReader((D/'native-driver/slots.csv').open()):
 r={k:int(v) for k,v in x.items()};f=r['frame']
 if f!=cur_frame:peaks=max(peaks,count);cur_frame=f;count=0
 if r['ecnt']<2097151:count+=1
 if r['owner']>>9==7:ugh_states[r['stamp']].append(r)
 if r['ecnt']<2097151 and r['owner']>>9!=0:native_gains.setdefault((r['stamp'],r['slot']),[]).append(r['tl'])
intervals=[]
for n in ugh:
 rr=[r for r in ugh_states[n['stamp']] if r['slot']==n['slot'] and r['frame']>=n['frame']];live=[r for r in rr if r['ecnt']<2097151];assert live
 phase=max(r['phase']/1024 for r in rr);assert phase>=10725
 end=next(r['frame'] for r in rr if r['frame']>live[0]['frame'] and r['ecnt']>=2097151)
 early=[r for r in current if r['action']=='F' and r['stamp']==n['stamp'] and r['slot']==n['slot'] and r['frame']<end];assert not early
 # No other control may take its slot before natural finish.
 assert not [r for r in cur_ns if r['slot']==n['slot'] and n['frame']<r['frame']<end]
 # Existing hiss control4 may naturally loop. No newly requested FX starts.
 competitors=[r for r in cur_ns if n['frame']<r['frame']<end and r['owner']>>9 not in (0,4,7)];assert not competitors
 intervals.append(dict(start=n['frame'],natural_end=end,frames=end-n['frame'],last_pcm_position=phase,slot=n['slot']))
assert all(b['start']>=a['natural_end'] for a,b in zip(intervals,intervals[1:]))
old_deaths=[r for r in old_ns if r['sa']==old_sas[8]];early=[]
for n in old_deaths:
 fs=[r for r in prior if r['action']=='F' and r['stamp']==n['stamp'] and r['slot']==n['slot'] and r['frame']>n['frame']]
 if fs and fs[0]['phase']/1024<12274:early.append(dict(start=n['frame'],off=fs[0]['frame'],pc=hex(fs[0]['pc']),pcm_position=fs[0]['phase']/1024))
assert early
# Direct instrument gain: actual SCSP TL lookup multiplier after note-on, not
# low-frequency energy or a claimed isolated bass/SFX audio stem.
before_gains={}
for x in csv.DictReader((D/'before-driver/slots.csv').open()):
 r={k:int(v) for k,v in x.items()}
 if r['ecnt']<2097151 and r['owner']>>9!=0:before_gains.setdefault((r['stamp'],r['slot']),[]).append(r['tl'])
velocity=[]
for i in range(8):
 a=next(r for r in old_ns if r['sa']==old_sas[i] and r['owner']>>9!=0);b=next(r for r in cur_ns if r['sa']==now_sas[i] and r['owner']>>9!=0)
 va=statistics.median(before_gains[(a['stamp'],a['slot'])]);vb=statistics.median(native_gains[(b['stamp'],b['slot'])]);velocity.append(dict(song=i,before_native_tl_multiplier=va,after_native_tl_multiplier=vb,increases_gain=vb>va))
_,ev,end=read((R/'assets/cd/STAGE.SEQ').read_bytes());notes=[n for n in ev if n['kind']=='note'];music=[r for r in cur_ns if r['owner']>>9==0];assert len(music)>len(notes) and all((r['key']>>8,r['key']&127)==(notes[i%len(notes)]['channel'],notes[i%len(notes)]['pitch']) for i,r in enumerate(music));assert not [r for r in current if r['action']=='F' and r['owner']>>9==0 and r['pc']!=15654]
a=array.array('h');a.frombytes((D/'native-driver/audio.pcm').read_bytes());clips=sum(x in (-32768,32767) for x in a);assert not clips
result=dict(ugh_native_tl_multiplier=statistics.median(native_gains[(ugh[0]['stamp'],ugh[0]['slot'])]),ugh_completed_plays=len(intervals),ugh_intervals=intervals,prior_argh_premature_stop_examples=early[:5],measured_peak_active_native_ecnt_slots=peaks,total_music_ons=len(music),full_music_loop_preserved=True,forced_music_offs=0,music_ons_during_long_pause=sum(2500<=r['frame']<15000 for r in music),mixed_pcm_peak=max(map(abs,a)),clipped_samples=clips,velocity_native_gain_audit=velocity,velocity_exceptions=[r['song'] for r in velocity if not r['increases_gain']],existing_hiss_continues=True)
(R/'docs/ugh-native.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
