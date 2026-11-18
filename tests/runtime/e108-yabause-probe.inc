
/* Read-only startup probe, appended to the pinned Yabause libretro frontend. */
#include "scsp.h"

unsigned retro_mf_high_ram(unsigned address)
{
   return HighWramMemoryReadLong(address);
}

unsigned retro_mf_sound_ram(unsigned address)
{
   return SoundRamReadWord(address);
}

void retro_mf_cpu(unsigned *out)
{
   m68kregs_struct audio;
   sh2regs_struct main;
   M68KGetRegisters(&audio);
   SH2GetRegisters(MSH2, &main);
   out[0] = audio.PC;
   out[1] = audio.SR;
   out[2] = audio.A[7];
   out[3] = main.PC;
   out[4] = main.R[15];
   out[5] = main.SR.all;
}
