from pathlib import Path
import csv,json,array,sys
R=Path(__file__).resolve().parents[1];D=Path(sys.argv[1]) if len(sys.argv)>1 else R/'build/poowah-captures';sys.path.insert(0,str(R/'tools'));from level1_refinement import read
ughsa=332184;out={}
for name in ('driver','transition'):
 p=D/name;rs=[{k:(v if k=='action' else int(v)) for k,v in x.items()} for x in csv.DictReader((p/'events.csv').open())];ns=[r for r in rs if r['action']=='N'];ugh=[r for r in ns if r['sa']==ughsa and r['owner']>>9==7];states={(r['stamp'],r['slot']):dict(start=r['frame'],phase=0,live=False,end=None) for r in ugh};peak=0;frame=-1;count=0
 for x in csv.DictReader((p/'slots.csv').open()):
  r={k:int(v) for k,v in x.items()}
  if r['frame']!=frame:peak=max(peak,count);count=0;frame=r['frame']
  if r['ecnt']<2097151:count+=1
  s=states.get((r['stamp'],r['slot']))
  if s and r['sa']==ughsa and r['frame']>=s['start']:
   s['phase']=max(s['phase'],r['phase']/1024)
   if r['ecnt']<2097151:s['live']=True
   elif s['live'] and s['end'] is None:s['end']=r['frame']
 complete=[s for s in states.values() if s['end'] is not None and s['phase']>=8420];assert all(s['end'] is not None or s['start']+46>=frame for s in states.values()),name
 for n in ugh:
  s=states[(n['stamp'],n['slot'])];assert not [r for r in rs if r['action']=='F' and r['stamp']==n['stamp'] and r['slot']==n['slot'] and n['frame']<=r['frame']<(s['end'] if s['end'] is not None else frame+1)]
 a=array.array('h');a.frombytes((p/'audio.pcm').read_bytes());clips=sum(v in (-32768,32767) for v in a);assert clips==0,(name,clips)
 music=[r for r in ns if r['owner']>>9==0];stage2=next((r['frame'] for r in music if r['sa']<389156),None)
 if stage2:
  l2=[r for r in music if r['frame']>=stage2];_,ev,_=read((R/'assets/wingsuit/WMUSIC.SEQ').read_bytes());notes=[n for n in ev if n['kind']=='note'];assert all((r['key']>>8,r['key']&127)==(notes[i]['channel'],notes[i]['pitch']) for i,r in enumerate(l2));assert not [r for r in rs if r['action']=='F' and r['owner']>>9==0 and r['frame']>=stage2 and r['pc']!=15654]
 else:
  _,ev,_=read((R/'assets/cd/STAGE.SEQ').read_bytes());notes=[n for n in ev if n['kind']=='note'];assert all((r['key']>>8,r['key']&127)==(notes[i%len(notes)]['channel'],notes[i%len(notes)]['pitch']) for i,r in enumerate(music));assert not [r for r in rs if r['action']=='F' and r['owner']>>9==0 and r['pc']!=15654]
 out[name]=dict(death_plays=len(ugh),death_completed=len(complete),death_in_progress_at_capture_end=len(states)-len(complete),peak_native_active_slots_per_vblank=peak,mixed_pcm_peak=max(map(abs,a)),clipped_samples=clips,music_ons=len(music),level2_start_frame=stage2,level2_music_ons=len(l2) if stage2 else None,death_intervals=list(states.values()))
print(json.dumps(out,indent=2));(R/'docs/poowah-native.json').write_text(json.dumps(out,indent=2)+'\n')
