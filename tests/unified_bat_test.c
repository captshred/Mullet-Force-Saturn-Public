/* Real simulation plus real renderer; only Saturn I/O is mocked. */
#define main bank_suite
#include "sequence_bank_test.c"
#undef main
#define main gameplay_suite
#include "fast_bat_test.c"
#undef main
int main(void)
{
 mf_game early,late;int a,f,i,k,ids[64],flips[64],n,boot;
 assert(bank_suite()==0);boot=count;
 for(a=0;a<2;a++)for(f=-1;f<=1;f+=2){
  unsigned d=direction(f);
  init(&early,f);step(&early,a,0,0);step(&early,a,d,d);step(&early,a,0,0);late=early;
  /* Deliberately leave the renderer at an unrelated old run pose. */
  ca_last_run[a]=3;
  step(&early,a,d|MF_A,d|MF_A);
  step(&late,a,d,d);step(&late,a,d|MF_A,MF_A);
  assert(early.players[a].bat==MF_BAT_RUNNING && early.running_bat[a].active==1);
  /* Equalize the world root; the delayed input spent one extra tick running. */
  late.players[a].x=early.players[a].x;
  target(&early,a,f,1,1);target(&late,a,f,1,1);
  for(i=0;i<50;i++){
   draws=0;assert(mf_combat_prototype_draw(&early,a,100,202,230)==(early.players[a].attack!=0));
   n=draws;for(k=0;k<n;k++){ids[k]=drawn_ids[k];flips[k]=draw_flips[k];}
   draws=0;assert(mf_combat_prototype_draw(&late,a,100,202,230)==(late.players[a].attack!=0));
   assert(draws==n && count==boot);
   for(k=0;k<n;k++)assert(ids[k]==drawn_ids[k] && flips[k]==draw_flips[k]);
   assert(early.players[a].attack==late.players[a].attack && early.players[a].x==late.players[a].x);
   assert(early.events==late.events && early.score==late.score && early.broken==late.broken);
   assert(!memcmp(early.enemies,late.enemies,sizeof(early.enemies)));
   step(&early,a,d,0);step(&late,a,d,0);
  }
  assert(early.broken==3 && early.score==830 && !early.players[a].attack);
  /* Simultaneous jump retains priority; no grounded bat from an air gesture. */
  init(&early,f);step(&early,a,0,0);step(&early,a,d,d);step(&early,a,0,0);
  step(&early,a,d|MF_A|MF_B,d|MF_A|MF_B);
  assert(!early.players[a].bat && early.players[a].attack_air);
 }
 puts("PASS unified bat: immediate/delayed actual visual IDs/mirrors, stale-pose protection, identical collisions/damage/events/momentum/recovery, both players/facings, no uploads, jump priority");
 return 0;
}
