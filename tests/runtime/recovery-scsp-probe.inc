/* Append to the SHA-pinned Yabause scsp.c for read-only native observation.
   Observe envelope/phase advancement; cached driver EG is unreliable in HLE. */
unsigned retro_recovery_slot(unsigned n,unsigned field){
 slot_t *s=&scsp.slot[n&31];
 switch(field){case 0:return s->sa;case 1:return s->fcnt;case 2:return s->ecurp;case 3:return s->keyx;case 4:return s->tl;default:return (unsigned)s->env;}
}
