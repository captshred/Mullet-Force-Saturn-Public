
/* Read the legacy SCSP implementation used by the pinned libretro build. */
void retro_mf_scsp_state(unsigned *out)
{
   out[0] = IsM68KRunning;
   out[1] = out[2] = out[3] = out[4] = out[5] = 0;
   for (unsigned i = 0; i < 32; ++i) {
      const slot_t *slot = &scsp.slot[i];
      unsigned bit = 1u << i;
      if (slot->key) out[1] |= bit;
      if (slot->ecnt < SCSP_ENV_DE) out[2] |= bit;
      if (slot->ecurp != SCSP_ENV_RELEASE) out[3] |= bit;
      if (!slot->eincr && slot->ecnt < SCSP_ENV_DE) out[4] |= bit;
      unsigned eg = 0x1f - (slot->env >> (SCSP_ENV_HB - 5));
      if (slot->ecnt >= SCSP_ENV_DE && ((eg ^ 0x1c) & 0x18)) out[5] |= bit;
   }
}
