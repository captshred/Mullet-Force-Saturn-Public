#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='ricky-tests-') as d:
 w=Path(d);header=R/'build/build-info.h'
 common=['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-fdata-sections','-include',str(header),'-I'+str(R/'src'),'-I'+str(R/'build'),'-Wl,--gc-sections']
 exe=w/'combat';subprocess.run([*common,str(R/'tests/ricky/combat.c'),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 exe=w/'balance';subprocess.run([*common,str(R/'tests/ricky/balance.c'),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 exe=w/'polish-charge';subprocess.run([*common,str(R/'tests/ricky/polish-charge.c'),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 main=(R/'src/main.c').read_text().split('static int depth_key')[0]
 life=(R/'tests/enemy_banks/lifecycle.inc').read_text().replace('mf_corporate_bank_spec','mf_ricky_bank_spec').replace('==151','==176').replace('?151:','?176:').replace('257024','371072').replace('MF_ENEMY_BANK_CORPORATE','2').replace('bank_mock_fail_after=2;','bank_mock_fail_after=argc>1 && argv[1][1]>=\'0\' && argv[1][1]<=\'9\'?atoi(argv[1]+1):2;')
 # Exercise all 25 pose resources in both directions and both slot roots after boot.
 life=life.replace('    memcpy(defs,', '''    for(int pose=0;pose<25;pose++)for(int a=0;a<2;a++)for(int facing=-1;facing<=1;facing+=2)
        assert(mf_ricky_draw_pose(pose,facing,100+a*120,200,200));
    memcpy(defs,''')
 (w/'main.c').write_text('#include <assert.h>\n#include <stdlib.h>\n#include <stdio.h>\n#include <string.h>\n'+main+'\n'+life)
 exe=w/'lifecycle';subprocess.run([*common,'-I'+str(R/'tests/enemy_banks'),str(w/'main.c'),str(R/'tests/enemy_banks/trace.c'),*[str(R/'src'/n) for n in ('enemy_sprite_bank.c','corporate_animation.c','ricky_animation.c','animation_preview.c','gallery.c')],'-o',str(exe)],check=True)
 for mode in ('0','busy','fail','f14','f26','f38','handles'):
  p=subprocess.run([str(exe),mode],cwd=R,capture_output=True,text=True)
  assert not p.returncode,p.stderr+p.stdout[-3000:]
  print(p.stdout.splitlines()[-1])

 # Compile the actual renderer with the same decoded texture/draw recorder.
 unit=w/'polish-render.c';unit.write_text('#include <assert.h>\n#include <stdio.h>\n#include <string.h>\n'+(R/'src/main.c').read_text().split('static void update(void)')[0]+'\n'+(R/'tests/ricky/polish-render.inc').read_text())
 exe=w/'polish-render';subprocess.run([*common,'-I'+str(R/'tests/enemy_banks'),str(unit),str(R/'tests/ricky/polish-trace.c'),*[str(R/'src'/n) for n in ('animation_preview.c','corporate_animation.c','enemy_sprite_bank.c','gallery.c','player_animation.c','game.c','ricky_animation.c')],'-o',str(exe)],check=True)
 result=subprocess.run([str(exe)],cwd=R,text=True,capture_output=True);assert not result.returncode,result.stdout[-2000:]+result.stderr
 lines=result.stdout.splitlines();groups={};key=None
 for line in lines:
  f=line.split('|')
  if f[0] in ('ENEMIES','FLAME'):key=tuple(map(int,f[1:]));groups[(f[0],key)]=[]
  elif key is not None and f[0]=='DRAW':groups[next(reversed(groups))].append(f)
 for (kind,key),draws in groups.items():
  if kind=='ENEMIES':
   a,flash=key
   for slot in range(2):
    wanted=(3 if (flash>>slot)&1 else 2) if slot==a else (5 if (flash>>slot)&1 else 4)
    enemy=[d for d in draws if (152<=int(d[2])<=176 if slot==a else 138<=int(d[2])<=151)]
    assert enemy and all(int(d[-1])==wanted for d in enemy),(key,slot,wanted,enemy)
  else:
   a,mode,flame=key;fires=[d for d in draws if int(d[2])==flame]
   assert len(fires)==(1 if mode in (1,2) else 0),(key,fires)
   if mode==1:
    off=groups[('FLAME',(a,0,flame))]
    assert [d[:-1] for d in draws if int(d[2])!=flame]==[d[:-1] for d in off],'hurt sprite changed under flame' # Direct RGB body/shadow draws ignore palette state.
 print('PASS CP/Ricky independent and simultaneous red flashes, 25 poses, unmodified base palettes; visible hurt/blink flame matches collision eligibility')
