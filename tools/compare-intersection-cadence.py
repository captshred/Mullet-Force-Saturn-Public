#!/usr/bin/env python3
"""Read-only render-update cadence A/B using production discs and the same inputs."""
from pathlib import Path
import argparse,struct,subprocess,json,sys
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser()
for n in ('core','include','baseline-cue','baseline-program','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True);assert not any(a.out.iterdir())
helper=(R/'tools/test-coop-balance-runtime.py').read_text();scope={'struct':struct};exec(helper[helper.index('def symbols('):helper.index('s=symbols(')],scope)
# Generate the same production traversal frontend from committed scripts only.
# Execute its source-construction prefix, never its compiler/emulator runner.
wrapper=R/'tools/test-full-detail-runtime.py';ns={'__file__':str(wrapper)}
text=wrapper.read_text();exec(text[:text.index('exec(compile(')],ns)
source=ns['s'];prefix=source[:source.index("unit=a.out/'frontend.c'")]
saved_args=sys.argv[:]
try:
 sys.argv=[str(wrapper),'--core',str(a.core),'--include',str(a.include),'--out',str(a.out/'source-generation')]
 generated={'__file__':str(R/'tools/test-intersection-runtime.py')};exec(prefix,generated)
finally:sys.argv=saved_args
src=generated['src'].replace('static unsigned seen_camera','static FILE *perf_trace;static unsigned seen_camera')
b=src.index('static void video(');e=src.index('static void audio(',b);src=src[:b]+'''static void video(const void *data,unsigned w,unsigned h,size_t pitch){(void)data;(void)w;(void)h;(void)pitch;}
'''+src[e:]
src=src.replace(' fwrite(&frame,4,1,trace);',''' fwrite(&frame,4,1,trace);
 if(frame>=1100){unsigned q[]={frame,read32(ram,VBLANKS),read32(ram,LAST_VBLANK),read32(ram,game_addr+offsetof(mf_game,ticks)),read32(ram,game_addr+offsetof(mf_game,hitstop)),read32(ram,game_addr+offsetof(mf_game,camera)),read32(ram,ASSET_ERROR),read32(ram,PARALLAX_ERROR)};fwrite(q,sizeof(q),1,perf_trace);}
''')
src=src.replace(' for(frame=0;frame<frames;frame++){',''' {char path[512];snprintf(path,sizeof(path),"%s/performance.bin",outdir);perf_trace=fopen(path,"wb");if(!perf_trace)return 3;}
 for(frame=0;frame<frames;frame++){''').replace(' fclose(trace);',' fclose(trace);fclose(perf_trace);')
unit=a.out/'frontend.c';unit.write_text(src);reports={}
for label,cue,elf,owner in [('baseline',a.baseline_cue,a.baseline_program,'_world_block_cache'),('candidate',R/'build/mullet-force.cue',R/'build/game.elf','_world_packed')]:
 sy=scope['symbols'](elf.resolve());addr=lambda name:scope['addr'](sy,name);folder=a.out/label;folder.mkdir();exe=a.out/('frontend-'+label)
 subprocess.run(['cc','-std=c99','-O2','-include',str(R/'build/build-info.h'),'-I'+str(a.include.resolve()),'-I'+str(R/'src'),f'-DASSET_ERROR={addr("_asset_error")}',f'-DPARALLAX_ERROR={addr("_live_error")}',f'-DWORLD_CACHE_POINTER={addr(owner)}',f'-DVBLANKS={addr("_vblanks")}',f'-DLAST_VBLANK={addr("_last_vblank")}',str(unit),'-ldl','-o',str(exe)],check=True)
 with (folder/'run.log').open('w') as log:subprocess.run([str(exe),str(a.core.resolve()),str(cue.resolve()),str(folder),'4400','compare',hex(addr('_game')),hex(addr('_idle_ticks'))],stdout=log,stderr=log,check=True)
 data=(folder/'performance.bin').read_bytes();rows=[struct.unpack_from('<8I',data,i) for i in range(0,len(data),32)];assert len(rows)==3300 and all(r[6]==r[7]==0 for r in rows)
 updates=[r for before,r in zip(rows,rows[1:]) if r[2]!=before[2]];gaps=[b[0]-c[0] for c,b in zip(updates,updates[1:])];lags=sorted(r[1]-r[2] for r in rows)
 reports[label]=dict(frames=len(rows),observed_update_frames=len(updates),update_frames_per_60Hz_second=round(len(updates)/((len(rows)-1)/60),3),max_observed_update_gap_frames=max(gaps),p99_vblank_lag=lags[int(len(lags)*.99)],max_vblank_lag=max(lags),endpoint_reached=max(r[5] for r in rows)==1600,last_camera=rows[-1][5],scope='read-only last_vblank change observations at 60Hz; same physical-controller/camera-feedback schedule; no debug writes; paused/hit-stop simulation ticks are not an FPS measure')
 assert reports[label]['endpoint_reached'] and reports[label]['last_camera']==1280
r=dict(builds=reports,tolerance='At most 1% fewer observed render-update frames (scheduler jitter envelope); actual values reported, not assumed equal',scope='Fresh production HLE A/B, 3300 samples each. This is emulator update cadence, not a hardware GPU timing claim.')
r['observed_update_delta']=reports['candidate']['observed_update_frames']-reports['baseline']['observed_update_frames'];r['within_baseline_cadence']=r['observed_update_delta']>=-max(3,reports['baseline']['observed_update_frames']//100)
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['within_baseline_cadence'],'render cadence regression'
