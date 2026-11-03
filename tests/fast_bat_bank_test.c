/* Exercise the actual renderer, loader and historical planted selection. */
#define main historical_bank_test
#include "sequence_bank_test.c"
#undef main
int main(void)
{
 mf_game g,copy;int a,phase,face,t,boot;
 assert(historical_bank_test()==0);boot=count;
 memset(&g,0,sizeof(g));
 for(a=0;a<2;a++)for(phase=0;phase<4;phase++)for(face=-1;face<=1;face+=2){
  mf_player *p=&g.players[a];p->active=1;p->health=100;p->facing=face;p->attack=0;p->bat=0;
  g.dash[a].dir=face;g.dash[a].anim=phase*MF_RUN_FRAME_HOLD*MF_DASH_ANIM_NUM;
  assert(!mf_combat_prototype_draw(&g,a,100,202,230));g.dash[a].dir=0;g.running_bat[a].active=1;
  for(t=1;t<=12;t++){
   int k,n=0;p->attack=t;p->bat=MF_BAT_RUNNING;draws=0;copy=g;
   assert(mf_combat_prototype_draw(&g,a,100,202,230));assert(!memcmp(&g,&copy,sizeof(g)) && count==boot && !flip);
   if(t<4){assert(draws==4);for(k=0;k<3;k++)assert(drawn_ids[k+1]==resource_ids[run_parts[a][phase][k].resource]);}
   else if(t<9){const mf_polish_piece *q=seq_lower[a];for(;q->resource>=0;q++)assert(drawn_ids[n++]==ca_ids[q->resource]);q=seq_upper[a][1];for(;q->resource>=0;q++)assert(drawn_ids[n++]==ca_ids[q->resource]);assert(n==draws);}
   else {assert(draws==3);for(k=0;k<3;k++)assert(drawn_ids[k]==resource_ids[polish_parts[a][0][k].resource]);}
   for(k=0;k<draws;k++)assert(draw_flips[k]==(face<0));
  }
 }
 puts("PASS actual fast renderer: exact carry in all eight phases/mirrors, horizontal key1 grip, quick guard, zero uploads/bytes, immutable game state; historical planted path retained");return 0;
}
