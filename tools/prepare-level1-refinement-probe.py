#!/usr/bin/env python3
"""Build a pinned, read-only native SCSP observer. No emulated memory writes."""
from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[1];core=R/'.deps/refinement-yabause';pin='8926b0c6c347f8c5c755911ddb0ac695420ffbf8'
if not (core/'.git').exists():subprocess.run(['git','clone','https://github.com/libretro/yabause.git',str(core)],check=True)
subprocess.run(['git','checkout','--detach',pin],cwd=core,check=True)
# Only these observer-owned files in this dedicated ignored test checkout.
subprocess.run(['git','restore','yabause/src/scsp.c','yabause/src/libretro/libretro.c'],cwd=core,check=True)
from pathlib import Path
src=core/'yabause/src/scsp.c'
s=src.read_text();insert=s.index('////////////////////////////////////////////////////////////////\n// Key ON/OFF event handler')
probe='''
/* Read-only observer; no emulated RAM/register mutations. */
static unsigned mf_probe_frame;
static FILE *mf_probe_file;
extern unsigned short SoundRamReadWord(unsigned int);
void retro_level1_frame(unsigned n){mf_probe_frame=n;}
static void mf_probe_event(char action, slot_t *slot){
 unsigned index=(unsigned)(slot-&scsp.slot[0]);
 if(!mf_probe_file){const char *p=getenv("MF_AUDIO_TRACE");if(!p)return;mf_probe_file=fopen(p,"w");if(!mf_probe_file)return;fprintf(mf_probe_file,"frame,action,slot,pc,owner,key,stamp,sa,envelope,ecnt,tl,phase\\n");}
 fprintf(mf_probe_file,"%u,%c,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\\n",mf_probe_frame,action,index,M68K->GetPC(),SoundRamReadWord(0x8006+64*index),SoundRamReadWord(0x8002+64*index),SoundRamReadWord(0x803e +64*index),slot->sa,slot->ecurp,(unsigned)slot->ecnt,slot->tl,slot->fcnt);
}
'''
s=s[:insert]+probe+s[insert:]
s=s.replace('      SCSPLOG ("key on slot %d.', '      mf_probe_event(\'N\',slot);\n      SCSPLOG ("key on slot %d.')
s=s.replace('      SCSPLOG ("key off slot %d', '      mf_probe_event(\'F\',slot);\n      SCSPLOG ("key off slot %d')
src.write_text(s)

from pathlib import Path
p=core/'yabause/src/scsp.c';s=p.read_text()
needle='   scsp_bufL = bufL;\n   scsp_bufR = bufR;'
replacement='''   static s32 beforeL[8192],beforeR[8192],musicL[8192],musicR[8192],sfxL[8192],sfxR[8192];
   static FILE *music_file,*sfx_file;static int stem_checked;
   unsigned si;int stems;
   if(!stem_checked){const char *prefix=getenv("MF_AUDIO_STEMS");stem_checked=1;if(prefix){char name[2048];snprintf(name,sizeof(name),"%s.music.s32le",prefix);music_file=fopen(name,"wb");snprintf(name,sizeof(name),"%s.sfx.s32le",prefix);sfx_file=fopen(name,"wb");}}
   stems=music_file && sfx_file && len<=8192;
   if(stems){memset(musicL,0,len*4);memset(musicR,0,len*4);memset(sfxL,0,len*4);memset(sfxR,0,len*4);}
   scsp_bufL = bufL;
   scsp_bufR = bufR;'''
assert needle in s;s=s.replace(needle,replacement,1)
needle='''      // SCSPLOG("update : VL=%d  VR=%d CNT=%.8X STEP=%.8X\\n", slot->disll, slot->dislr, slot->fcnt, slot->finc);

      scsp_slot_update_p'''
assert needle in s;s=s.replace(needle,'''      if(stems){memcpy(beforeL,bufL,len*4);memcpy(beforeR,bufR,len*4);}

      scsp_slot_update_p''',1)
needle='''      [(slot->dislr == 31) ? 0 : 1](slot);
   }

   if (cdda_out_left > 0)'''
replacement='''      [(slot->dislr == 31) ? 0 : 1](slot);
      if(stems){unsigned owner=SoundRamReadWord(0x8006 +64*(unsigned)(slot-&scsp.slot[0]));for(si=0;si<len;si++){if(owner==0){musicL[si]+=bufL[si]-beforeL[si];musicR[si]+=bufR[si]-beforeR[si];}else{sfxL[si]+=bufL[si]-beforeL[si];sfxR[si]+=bufR[si]-beforeR[si];}}}
   }
   if(stems){for(si=0;si<len;si++){fwrite(musicL+si,4,1,music_file);fwrite(musicR+si,4,1,music_file);fwrite(sfxL+si,4,1,sfx_file);fwrite(sfxR+si,4,1,sfx_file);}}

   if (cdda_out_left > 0)'''
assert needle in s;s=s.replace(needle,replacement,1);p.write_text(s)

with (core/'yabause/src/scsp.c').open('a') as f:f.write((R/'tests/runtime/recovery-scsp-probe.inc').read_text())
with (core/'yabause/src/libretro/libretro.c').open('a') as f:f.write('\nextern unsigned short SoundRamReadWord(unsigned int);\nunsigned retro_recovery_word(unsigned addr){return SoundRamReadWord(addr); }\n')
subprocess.run(['make','-C',str(core/'yabause/src/libretro'),'-j2'],check=True)
