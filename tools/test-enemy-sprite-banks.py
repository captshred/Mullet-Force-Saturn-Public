#!/usr/bin/env python3
"""Actual boot + bank manager + Corporate Punk loader/renderer lifecycle tests."""
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='mf-bank-lifecycle-') as d:
 w=Path(d);main=(R/'src/main.c').read_text().split('static int depth_key')[0]
 (w/'main.c').write_text('#include <assert.h>\n#include <stdio.h>\n#include <string.h>\n'+main+'\n'+(R/'tests/enemy_banks/lifecycle.inc').read_text())
 exe=w/'lifecycle'
 subprocess.run(['cc','-std=c99','-ffunction-sections','-fdata-sections','-fsanitize=undefined','-fno-sanitize-recover=all','-include',str(R/'build/build-info.h'),'-I'+str(R/'tests/enemy_banks'),'-I'+str(R/'src'),'-I'+str(R/'build'),str(w/'main.c'),str(R/'tests/enemy_banks/trace.c'),*[str(R/'src'/n) for n in ('enemy_sprite_bank.c','corporate_animation.c','animation_preview.c','gallery.c')],'-Wl,--gc-sections','-o',str(exe)],cwd=R,check=True)
 for mode in ('0','busy','fail','handles'):subprocess.run([str(exe),mode],cwd=R,check=True)
 # Compile the real pinned allocator functions, unchanged, independently of the
 # host rendering mock. This catches free_from's surprising private cursor value.
 s=(R/'.deps/joengine/jo_engine/sprites.c').read_text()
 def function(marker):
  start=s.index(marker);a=s.index('{',start);level=1;i=a+1
  while level:
   if s[i]=='{':level+=1
   if s[i]=='}':level-=1
   i+=1
  return s[start:i]
 unit='''#include <assert.h>
#include <stddef.h>
#define JO_MAX_SPRITE 255
#define JO_VDP1_VRAM 0x25c00000u
#define JO_VDP1_TEXTURE_DEF_BASE_ADDRESS 0x10000
#define JO_NULL NULL
#define JO_ZERO(x) ((x)=0)
#define JO_MULT_BY_8(x) ((x)*8)
#define JO_DIV_BY_8(x) ((x)/8)
#define JO_MULT_BY_32(x) ((x)*32)
#define JO_MULT_BY_4(x) ((x)*4)
typedef struct {unsigned short width,height,adr,size;} jo_texture_definition;
typedef struct {void *data;int index,color_mode;} jo_picture_definition;
jo_texture_definition __jo_sprite_def[255];jo_picture_definition __jo_sprite_pic[255];
static unsigned __jo_sprite_addr;static int __jo_sprite_id=-1;
static void jo_dma_copy(void *a,void *b,unsigned n){(void)a;(void)b;(void)n;}
'''
 unit+=function('static  __jo_force_inline unsigned int\t__jo_get_next_sprite_address').replace('__jo_force_inline','inline')+'\n'
 unit+=function('static int                  __internal_jo_sprite_add')+'\n'+function('void                        jo_sprite_free_from')+'\n'
 unit+='''int main(void){int i,id;unsigned end;
 for(i=0;i<138;i++)assert(__internal_jo_sprite_add(0,8,8,2)==i);
 end=__jo_get_next_sprite_address(__jo_sprite_def[137].adr*8,8,8,2);
 for(i=0;i<256;i++){
  id=__internal_jo_sprite_add(0,72,30,2);assert(id==138 && __jo_sprite_def[id].adr*8==end);
  __internal_jo_sprite_add(0,112,36,2);jo_sprite_free_from(138);assert(__jo_sprite_id==137);
  /* It temporarily points after the FIRST freed texture, not at prefix end. */
  assert(__jo_sprite_addr==end+2176);
 }
 assert(__internal_jo_sprite_add(0,8,8,2)==138 && __jo_sprite_def[138].adr*8==end);
 jo_sprite_free_from(0);assert(__jo_sprite_id==-1 && !__jo_sprite_addr);
 return 0;}
'''
 (w/'allocator.c').write_text(unit)
 subprocess.run(['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all',str(w/'allocator.c'),'-o',str(w/'allocator')],check=True)
 subprocess.run([str(w/'allocator')],check=True)
 print('PASS pinned SDK actual add/free/next-address: 256 suffix reloads, first-free cursor behavior, full teardown')
