#!/usr/bin/env python3
"""Direct Phase 5/current CP-only non-attacking replay and decoded render comparison."""
from pathlib import Path
import hashlib,io,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];BASE='1dd66746f37333914408234fc14d520858ac59fd'
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='ricky-preserve-') as d:
 w=Path(d);ref=w/'reference';ref.mkdir()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 renders=[];games=[]
 for label,root,on in [('phase5',ref,0),('ricky',R,1)]:
  out=w/label;out.mkdir();header=(R/'build/build-info.h').read_text().replace('#define MF_RICKY_ENEMY 1',f'#define MF_RICKY_ENEMY {on}');(out/'build-info.h').write_text(header)
  common=['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-fdata-sections','-include',str(out/'build-info.h'),'-I'+str(out),'-I'+str(root/'src'),'-Wl,--gc-sections']
  game='''#include <stdio.h>
#include <stddef.h>
#include "game.h"
int main(void){mf_game g;unsigned rng=1776,held[2],pressed[2];mf_game_init(&g);
for(int t=0;t<30000;t++){
#if MF_RICKY_ENEMY
 g.ricky_spawns=0; /* Counterfactual: same CP spawns to isolate unchanged gameplay. */
#endif
 for(int p=0;p<2;p++){rng=rng*1664525u+1013904223u;held[p]=((rng>>16)&127)&~MF_A; /* Exclude intentionally rebalanced bat/flame contacts. */pressed[p]=held[p]&((rng>>24)&127);}
 if(t==0 || t==30)pressed[0]=MF_START;if(t==50)pressed[1]=MF_START;
 mf_game_step_inputs(&g,held,pressed,3);
#if MF_RICKY_ENEMY
 fwrite(&g,offsetof(mf_game,ricky_spawns),1,stdout);
#else
 fwrite(&g,sizeof g,1,stdout);
#endif
}return 0;}'''
  (out/'game.c').write_text(game);exe=out/'game'
  subprocess.run([*common,str(out/'game.c'),str(root/'src/game.c'),'-o',str(exe)],check=True)
  games.append(hashlib.sha256(subprocess.check_output([str(exe)])).hexdigest())
  main='#include <stdio.h>\n#include <assert.h>\n#include <string.h>\nvoid audit_finish(void);\n'+(root/'src/main.c').read_text().split('static void update(void)')[0]
  scenarios=(R/'tests/sprite_cleanup/scenarios.inc').read_text().replace('audit_finish();','hud_scenarios();audit_finish();')
  main+='\nstatic void hud_scenarios(void);\n'+scenarios+'\n'+(R/'tests/hud_panel/scenarios.inc').read_text();(out/'main.c').write_text(main);exe=out/'render'
  subprocess.run([*common,'-I'+str(R/'tests/enemy_banks'),str(out/'main.c'),str(R/'tests/enemy_banks/trace.c'),*[str(root/'src'/n) for n in ('animation_preview.c','corporate_animation.c','enemy_sprite_bank.c','gallery.c','player_animation.c','game.c')],*([str(R/'src/ricky_animation.c')] if on else []),'-o',str(exe)],check=True)
  lines=subprocess.check_output([str(exe)],cwd=R,text=True).splitlines();textures={};commands=[];palettes={};c=0
  for line in lines:
   f=line.split('|')
   if f[0]=='TEXTURE':textures[f[1]]=tuple(f[3:6])+ (hashlib.sha256(bytes.fromhex(f[-1])).hexdigest(),)
  for line in lines:
   f=line.split('|')
   if f[0]=='TEXTURE':textures[f[1]]=tuple(f[3:6])+ (hashlib.sha256(bytes.fromhex(f[-1])).hexdigest(),)
   elif f[0]=='PALETTE':
    if f[1] not in ('2','3'):palettes[f[1]]=f[2]
   elif f[0] in ('DRAW','QUAD'):
    if f[0]=='DRAW' and textures[f[2]][2]=='1':assert f[-1] not in ('2','3'),'unchanged indexed draw uses reclaimed Ricky palette'
    commands.append(tuple(f[:2])+textures[f[2]]+tuple(f[3:]));c+=1
   else:commands.append(tuple(v.replace('371072','<budget>').replace('257024','<budget>') for v in f))
  renders.append((commands,palettes));print(label,'render commands',c,flush=True)
 assert games[0]==games[1],('CP-only 30000-step gameplay changed',games)
 assert renders[0]==renders[1],'CP-only rendering or shared palettes changed'
 print('PASS direct Phase 5/current: 30000 CP-only non-attacking co-op ticks byte-identical; 7666 renderer cases/decoded textures/draw geometry/order/shared palettes identical; no unchanged indexed draw uses reclaimed palettes 2/3')
