#!/usr/bin/env python3
"""Optional controller-only Yabause audio capture; pinned to libretro/yabause 8926b0c.
Requires its built core/headers, COFF-capable sh-elf-nm and NumPy/Pillow.
No BIOS download, RAM writes or game hooks. --single asserts no whoosh/CONNECT overlap.
"""
from pathlib import Path
import argparse,subprocess,os,re,struct,json,hashlib,collections
import numpy as np
from playable_runtime_validation import trace
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
for n in ['core','include','build','out']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--frontend',type=Path,default=R/'tests/runtime/custom-sfx-frontend.c');p.add_argument('--scenario',choices=['jab','jab-hit','bat','torch'],default='bat');p.add_argument('--single',action='store_true');a=p.parse_args()
out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
frontend=out/'frontend'
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-DMF_JAB_COHESION=1','-I'+str(a.include.resolve()),'-I'+str(R/'src'),str(a.frontend),'-ldl','-o',str(frontend)],check=True)
text=subprocess.check_output(['sh-elf-nm','--target=coff-sh',str(a.build/'game.elf')],text=True)
symbols={n:int(v,16) for v,n in re.findall(r'^([0-9a-f]+) . (\S+)$',text,re.M)}
env=dict(os.environ)
if a.scenario=='torch':env['MF_CUSTOM_TORCH']='1'
elif a.scenario=='bat':
 env['MF_CUSTOM_COMBAT_SCENARIO']='1'
 if a.single:env['MF_CUSTOM_ONE_ATTACKER']='1'
else:
 if a.scenario=='jab-hit':env['MF_CUSTOM_JAB_HITS']='1'
 if a.single:env['MF_CUSTOM_SINGLE']='1'
args=[str(frontend),str(a.core.resolve()),str((a.build/'mullet-force.cue').resolve()),str(out),'1400','run',hex(symbols['_game']),hex(symbols['_idle_ticks']),'1','1']
with (out/'run.log').open('w') as log:subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
report=json.loads((R/'assets/music/report.json').read_text());tone=(R/'assets/cd/FX.TON').read_bytes()
base=next(v['start'] for v in report['sound_ram_regions'] if v['name']=='FX.TON');addresses={}
for i in range(8):
 l=struct.unpack_from('>H',tone,8+2*i)[0]+4;sa=((tone[l+3]&15)<<16)|struct.unpack_from('>H',tone,l+4)[0];addresses[base+sa]=i
b=(out/'scsp.bin').read_bytes();assert len(b)==1105*5060
peak=0;overlap=[];counts=collections.Counter();starts=collections.Counter();last=set();transitions=[]
for off in range(0,len(b),5060):
 frame=int.from_bytes(b[off:off+4],'little');raw=b[off+4:off+4100];inside=b[off+4100:off+5060];active=[];present=set();n=0
 for i in range(32):
  s=raw[i*32:(i+1)*32];ctrl=int.from_bytes(s[2:4],'little');sa=((ctrl&15)<<16)|int.from_bytes(s[:2],'little');v=addresses.get(sa)
  if int.from_bytes(inside[30*i+5:30*i+9],'little')<2097151:
   n+=1
   if v is not None:active.append(v);present.add((i,v));counts[v]+=1
 for slot,voice in present-last:starts[voice]+=1;transitions.append([frame,slot,voice])
 last=present;peak=max(peak,n)
 if 6 in active and (5 in active or 7 in active):overlap.append(frame)
assert peak<=32
if a.single:assert not overlap,overlap
if a.scenario=='torch':assert starts[3]>0 and starts[4]>0
else:
 assert starts[7 if a.scenario=='bat' else 5]>0
 if a.scenario!='jab':assert starts[6]>0
samples=np.fromfile(out/'audio.pcm',dtype='<i2').astype(np.int32);rails=int(np.sum((samples>=32767)|(samples<=-32768)));assert not rails
results=dict(scenario=a.scenario,single_attacker=a.single,frames=1400,core_sha256=hashlib.sha256(a.core.read_bytes()).hexdigest(),bin_sha256=hashlib.sha256((a.build/'mullet-force.bin').read_bytes()).hexdigest(),peak_active_slots=peak,custom_voice_starts=dict(starts),custom_active_frames=dict(counts),global_whoosh_connect_overlap_frames=overlap,output_peak=int(np.max(np.abs(samples))),rail_samples=rails,transitions=transitions,scope='Global overlap between different players is permitted. Single-attacker scenarios assert none. No listening or hardware verification.')
(out/'validation.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
