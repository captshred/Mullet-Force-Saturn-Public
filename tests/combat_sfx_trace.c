#include <stdio.h>
#include <stddef.h>
#include "game.h"
static unsigned rng=5279;
static unsigned random_next(void){rng=rng*1664525u+1013904223u;return rng;}
int main(void){mf_game g;unsigned last[2]={0,0};int i;mf_game_init(&g);
for(i=0;i<16000;i++){
 unsigned held[2],edge[2];int j;
 for(j=0;j<2;j++){held[j]=random_next()&127u;if(i%450==0)held[j]|=MF_START;edge[j]=held[j]&~last[j];last[j]=held[j];}
 mf_game_step_inputs(&g,held,edge,(i%997==0)?1u:3u);
 {mf_game copy=g;size_t n;
 copy.events&=31;
#ifdef BASELINE
 n=sizeof(copy);
#else
 n=offsetof(mf_game,burn_owner);
#endif
 fwrite(&copy,n,1,stdout);}
}return 0;}
