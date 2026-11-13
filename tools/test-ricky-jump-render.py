#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='jump-render-') as d:
 w=Path(d);unit=w/'render.c';unit.write_text('#include <assert.h>\n#include <stdio.h>\n#include <string.h>\n'+(R/'src/main.c').read_text().split('static void update(void)')[0]+'\n'+(R/'tests/ricky/jump-render.inc').read_text());exe=w/'render'
 subprocess.run(['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-fdata-sections','-include',str(R/'build/build-info.h'),'-I'+str(R/'src'),'-I'+str(R/'build'),'-I'+str(R/'tests/enemy_banks'),str(unit),str(R/'tests/ricky/polish-trace.c'),*[str(R/'src'/n) for n in ('animation_preview.c','corporate_animation.c','enemy_sprite_bank.c','gallery.c','player_animation.c','game.c','ricky_animation.c')],'-Wl,--gc-sections','-o',str(exe)],check=True)
 lines=subprocess.check_output([str(exe)],cwd=R,text=True).splitlines();key=None;count=0
 for line in lines:
  f=line.split('|')
  if f[0]=='JUMP':key=tuple(map(int,f[1:]))
  elif f[0]=='DRAW' and key and int(f[2]) in (168,169):
   slot,facing,state,flash=key;pose=17 if state==4 else 16
   assert int(f[2])==152+pose
   assert int(f[4])==150-(28 if facing>0 else 36) if pose==17 else int(f[4])==150-(22 if facing>0 else 26)
   assert int(f[5])==200-(12 if state==4 else 0)-(100 if pose==17 else 61)
   assert int(f[-1])==(3 if flash else 2) and int(f[7])==(facing<0)
   count+=1
 assert count==24,count
 print(lines[-1])
