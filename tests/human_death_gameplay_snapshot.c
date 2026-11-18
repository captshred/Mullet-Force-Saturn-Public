/* Compare full production game state; omit only the newly added audio flags. */
#include <stdio.h>
#include <stdint.h>
#include "game.h"
static uint64_t hash=1469598103934665603ULL;
static void digest(const void *p,unsigned n){const unsigned char *b=p;while(n--){hash^=*b++;hash*=1099511628211ULL;}}
int main(void){mf_game g;unsigned prev[2]={0},h[2],p[2];int t,i;mf_game_init(&g);
 for(t=0;t<24000;t++){
  for(i=0;i<2;i++){h[i]=0;if(t==0 || (i==1 && t==40))h[i]=MF_START;
   if(t>50){if(t%240<130)h[i]|=i?MF_LEFT:MF_RIGHT;if(t%25<2)h[i]|=MF_A;if(t%140<3)h[i]|=MF_B;if(t%900>700)h[i]|=MF_A;}
   p[i]=h[i]&~prev[i];prev[i]=h[i];}
  mf_game_step_inputs(&g,h,p,3);g.events&=~(MF_COMBAT_HEAVY_HIT(0)|MF_COMBAT_HEAVY_HIT(1)|MF_COMBAT_HUMAN_DEATH(0)|MF_COMBAT_HUMAN_DEATH(1));digest(&g,sizeof(g));
 }
 printf("%016llx\n",(unsigned long long)hash);return 0;}
