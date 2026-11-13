#!/usr/bin/env python3
"""Optional TEST-ONLY native eight-bank-reload + Level2 Yabause demonstration.
Normal production source/build are untouched. Real API/SDK/GPU/CD/audio paths;
read-only save-state observations, no emulator RAM writes or readiness bypasses.
"""
from pathlib import Path
import argparse,hashlib,io,json,struct,subprocess,tarfile
R=Path(__file__).resolve().parents[1];BASE='1dd66746f37333914408234fc14d520858ac59fd'
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
p=argparse.ArgumentParser(description=__doc__)
for n in ('core','include','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
assert not any(a.out.iterdir()),'use a fresh output directory'
root=a.out/'source';root.mkdir()
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(root,filter='data')
import shutil
for folder in ('src','tools','make'):
 shutil.copytree(R/folder,root/folder,dirs_exist_ok=True)
shutil.copytree(R/'assets/ricky',root/'assets/ricky')
for n in ('.deps','.git'):(root/n).symlink_to(R/n,target_is_directory=True)
main=(root/'src/main.c').read_text();at=main.index('static void update(void)')
main=main[:at]+(R/'tests/enemy_banks/demo.inc').read_text().replace('mf_corporate_bank_spec','mf_ricky_bank_spec')+'\n'+main[at:]
main=main.replace('    now=vblanks;\n    if(now!=last_input_vblank)', '    now=vblanks;\n    bank_demo_tick(now);\n    if(now!=last_input_vblank)',1)
(root/'src/main.c').write_text(main)
with (a.out/'native.log').open('w') as log:subprocess.run(['bash','tools/build-stage.sh','--native'],cwd=root,stdout=log,stderr=log,check=True)
def symbols(path):
 b=path.read_bytes();off,n=struct.unpack_from('>II',b,8);st=b[off+n*18:];i=0;s={}
 while i<n:
  at=off+i*18;raw=b[at:at+8]
  if raw[:4]==b'\0'*4:
   k=int.from_bytes(raw[4:],'big');name=st[k:].split(b'\0',1)[0].decode(errors='replace')
  else:name=raw.split(b'\0',1)[0].decode(errors='replace')
  if int.from_bytes(b[at+12:at+14],'big',signed=True)>0:s[name]=int.from_bytes(b[at+8:at+12],'big')
  i+=1+b[at+17]
 return s
def addr(s,name):
 m=[v for k,v in s.items() if k==name or k.startswith(name+'.lto_priv.')];assert len(m)==1,(name,m)
 return m[0]
s=symbols(root/'build/game.elf');ws=addr(s,'_shooter')
phase=[v for k,v in s.items() if k.startswith('_phase.lto_priv.') and ws-256<v<ws];assert len(phase)==1
frontend=(R/'tests/runtime/playable-frontend.c').read_text().replace('#include "game.h"','#include "game.h"\n#include "wingsuit.h"\nstatic FILE *bank_trace,*sound_trace;static unsigned seen_generations;')
frontend=frontend.replace('static size_t batch(const int16_t *d,size_t n){(void)d;return n;}', '''static size_t batch(const int16_t *d,size_t n){unsigned i,nz=0,v;for(i=0;i<n*2;i++)if(d[i])nz++;if(sound_trace){fwrite(&frame,4,1,sound_trace);v=n;fwrite(&v,4,1,sound_trace);fwrite(&nz,4,1,sound_trace);}return n;}''')
# Existing X stage shortcut is input Y in this core. Preserve normal controls and
# send it after the repeated bank scenario rather than during its intentional wait.
frontend=frontend.replace(' if(!port){',' if(id==RETRO_DEVICE_ID_JOYPAD_Y && !port && frame>=3000 && frame<3004)return 1;\n if(!port){',1)
b=frontend.index(' if(review_only){if(frame!=299',frontend.index('static void video('));e=frontend.index(' snprintf(path',b)
frontend=frontend[:b]+' if(frame<1000 || frame%20)return;\n'+frontend[e:]
# Read VDP2 CRAM as well as the existing WRAM/VDP1 chunks.
frontend=frontend.replace('const unsigned char *ram=NULL,*vram=NULL;', 'const unsigned char *ram=NULL,*vram=NULL,*cram=NULL;')
frontend=frontend.replace('  pos+=12+len;', '''  if(!memcmp(state+pos,"VDP2",4)){
   unsigned registers=len-0x80000-0x1000-4;if(registers!=0x120)exit(5);
   cram=state+pos+12+registers+0x80000;
  }
  pos+=12+len;''')
frontend=frontend.replace(' fwrite(&hash,4,1,trace);', ''' fwrite(&hash,4,1,trace);
 {unsigned bs=read32(ram,DEMO_STATE),gen=read32(ram,DEMO_GEN),swaps=read32(ram,DEMO_SWAPS),error=read32(ram,DEMO_ERROR),peak=read32(ram,DEMO_PEAK),stage=read32(ram,game_addr+offsetof(mf_game,stage));
  unsigned values[]={frame,bs,gen,swaps,error,peak,read32(ram,SPRITE_ID),stage,read32(ram,WS_ADDRESS+offsetof(mf_wingsuit,ticks)),read32(ram,WS_PHASE),read32(ram,WS_ERROR)};
  fwrite(values,sizeof(values),1,bank_trace);
  if(bs==1 && gen>=1 && gen<=9 && stage==0 && !(seen_generations&(1u<<gen))){
   char path[512];FILE *dump;seen_generations|=1u<<gen;
   snprintf(path,sizeof(path),"%s/prefix-%u.bin",outdir,gen);dump=fopen(path,"wb");if(!dump)exit(3);fwrite(vram+0x10000,224000,1,dump);fclose(dump);
   snprintf(path,sizeof(path),"%s/enemy-%u.bin",outdir,gen);dump=fopen(path,"wb");if(!dump)exit(3);fwrite(vram+0x10000+224000,147072,1,dump);fclose(dump);
   snprintf(path,sizeof(path),"%s/palettes-%u.bin",outdir,gen);dump=fopen(path,"wb");if(!dump || !cram)exit(3);fwrite(cram+2*512,2048,1,dump);fclose(dump);
  }
 }
''')
frontend=frontend.replace(' for(frame=0;frame<frames;frame++){',''' {char path[512];snprintf(path,sizeof(path),"%s/banks.bin",outdir);bank_trace=fopen(path,"wb");snprintf(path,sizeof(path),"%s/audio.bin",outdir);sound_trace=fopen(path,"wb");if(!bank_trace || !sound_trace)return 3;}
 for(frame=0;frame<frames;frame++){''').replace(' fclose(trace);',' fclose(trace);fclose(bank_trace);fclose(sound_trace);')
unit=a.out/'frontend.c';unit.write_text(frontend);exe=a.out/'frontend';folder=a.out/'captures';folder.mkdir()
args=['cc','-std=c99','-O2','-Wall','-Wextra','-include',str(R/'build/build-info.h'),'-I'+str(a.include.resolve()),'-I'+str(R/'src')]
for macro,name in [('DEMO_STATE','_mf_bank_demo_state'),('DEMO_SWAPS','_mf_bank_demo_swaps'),('DEMO_ERROR','_mf_bank_demo_error'),('DEMO_GEN','_mf_bank_demo_generation'),('DEMO_PEAK','_mf_bank_demo_peak'),('SPRITE_ID','___jo_sprite_id'),('WS_ADDRESS','_shooter'),('WS_ERROR','_error')]:args.append(f'-D{macro}={addr(s,name)}')
args+=[f'-DWS_PHASE={phase[0]}',str(unit),'-ldl','-o',str(exe)];subprocess.run(args,check=True)
with (a.out/'emulator.log').open('w') as log:subprocess.run([str(exe),str(a.core.resolve()),str(root/'build/mullet-force.cue'),str(folder),'4200','demo',hex(addr(s,'_game')),hex(addr(s,'_idle_ticks'))],stdout=log,stderr=log,check=True)
b=(folder/'banks.bin').read_bytes();rows=[struct.unpack_from('<11I',b,i) for i in range(0,len(b),44)]
assert max(r[3] for r in rows)==8,'eight swaps not completed'
assert {r[4] for r in rows}=={0} and {r[10] for r in rows}=={0},'bank or Level2 error'
assert all(r[6]==176 for r in rows if r[1]==1 and r[7]==0),'sprite count leaked across a ready bank'
assert {r[5] for r in rows if r[2]}=={371072},'peak allocation changed'
for prefix in ('prefix','enemy','palettes'):
 files=[folder/f'{prefix}-{g}.bin' for g in range(1,10)];assert all(p.exists() for p in files)
 assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in files})==1,prefix+' changed across swap'
level2=[r for r in rows if r[9]==3 and r[8]>0];assert level2 and level2[-1][6]==27
sounds=(folder/'audio.bin').read_bytes();audio=[struct.unpack_from('<III',sounds,i) for i in range(0,len(sounds),12)];state={r[0]:r for r in rows}
nonzero_wait=sum(nz for f,n,nz in audio if f in state and state[f][1] in (2,3))
nonzero_level2=sum(nz for f,n,nz in audio if f in state and state[f][9]==3)
assert nonzero_wait and nonzero_level2,'no nonzero audio evidence during waits/Level2'
report=dict(swaps=8,generations=9,prefix_definitions=138,prefix_bytes=224000,bank_definitions=39,bank_bytes=147072,peak_bytes=371072,free_bytes=87416,prefix_pixel_hash=hashlib.sha256((folder/'prefix-1.bin').read_bytes()).hexdigest(),enemy_pixel_hash=hashlib.sha256((folder/'enemy-1.bin').read_bytes()).hexdigest(),palette2345_hash=hashlib.sha256((folder/'palettes-1.bin').read_bytes()).hexdigest(),level2_last_id=level2[-1][6],level2_ticks=level2[-1][8],nonzero_audio_samples_during_waits=nonzero_wait,nonzero_audio_samples_level2=nonzero_level2,scope='test-only native callback requests real combined suffix changes with fixture actors temporarily absent; core/VDP1/CD/SDK drain, install, failure checks unmodified; physical X triggers normal Level2 transition after swaps; no RAM writes or new art; HLE not hardware/listening proof')
(a.out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
