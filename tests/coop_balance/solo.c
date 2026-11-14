/* Comparable trace across the approved two-slot and candidate three-slot ABI. */
#include <stdio.h>
#include "game.c"
int main(void) {
 mf_game g;mf_game_init(&g);g.started=1;
 unsigned previous=0;
 for(int t=0;t<12000;t++) {
  unsigned h[2]={0,0},p[2]={0,0};int clock=t%360;
  h[0]=(clock<160?MF_RIGHT:MF_LEFT)|(t%97<70?MF_A:0);
  p[0]=h[0]&~previous;previous=h[0];mf_game_step_inputs(&g,h,p,1);
  fwrite(g.players,sizeof(g.players),1,stdout);
  fwrite(g.enemies,2*sizeof(mf_enemy),1,stdout);
  fwrite(&g.camera,sizeof(int),1,stdout);fwrite(&g.score,sizeof(int),1,stdout);
  fwrite(&g.stage_kills,sizeof(int),1,stdout);fwrite(&g.spawn_rng,sizeof(unsigned),1,stdout);
  fwrite(g.punk,2*sizeof(mf_punk_ai),1,stdout);
 }
 return 0;
}
