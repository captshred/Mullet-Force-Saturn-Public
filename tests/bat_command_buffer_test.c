#define main original_fast_bat_tests
#include "fast_bat_test.c"
#undef main
int main(void)
{
 mf_game g;int p,f,n,i,transition,old;
 for(p=0;p<2;p++)for(f=-1;f<=1;f+=2)for(n=1;n<=5;n++){
  unsigned d=direction(f);init(&g,f);
  for(i=0;i<n;i++){
   if(i){step(&g,p,0,0);while(g.players[p].attack<13)step(&g,p,0,0);}
   step(&g,p,MF_A,MF_A);
  }
  /* Arm neutral then complete FF+A during the current punch. */
  step(&g,p,0,0);step(&g,p,d,d);step(&g,p,0,0);
  old=g.players[p].attack;step(&g,p,d|MF_A,d|MF_A);
  transition=g.combo[p].phase==2?17:13;
  if(g.players[p].bat){assert(old>=transition);assert(g.events&MF_COMBAT_BAT(p));continue;}assert(g.running_bat[p].pending);
  assert(g.players[p].attack==old+1 && !(g.events&MF_COMBAT_JAB(p)));
  assert(!g.dash[p].dir); /* Recognition never gives punch a movement dash. */
  while(g.players[p].attack<transition){
   step(&g,p,d,0);assert(!g.players[p].bat && !(g.events&MF_COMBAT_JAB(p)));
  }
  step(&g,p,d,0);assert(g.players[p].bat==MF_BAT_RUNNING && !g.running_bat[p].pending);
  assert(g.events&MF_COMBAT_BAT(p));assert(!(g.events&MF_COMBAT_JAB(p)));
  for(i=0;i<50;i++){step(&g,p,d,0);assert(!(g.events&(MF_COMBAT_BAT(p)|MF_COMBAT_JAB(p))));}
  assert(!g.players[p].attack && !g.running_bat[p].pending);
 }
 /* No attack at all from FF during punch unless A completes the command. */
 init(&g,1);step(&g,0,MF_A,MF_A);step(&g,0,0,0);step(&g,0,MF_RIGHT,MF_RIGHT);step(&g,0,0,0);step(&g,0,MF_RIGHT,MF_RIGHT);
 for(i=0;i<40;i++){step(&g,0,MF_RIGHT,0);assert(!g.players[0].bat && !g.running_bat[0].pending);}
 /* Buffered command cancels on jump input; does not survive pause. */
 init(&g,1);step(&g,0,MF_A,MF_A);step(&g,0,0,0);step(&g,0,MF_RIGHT,MF_RIGHT);step(&g,0,0,0);step(&g,0,MF_RIGHT|MF_A,MF_RIGHT|MF_A);
 assert(g.running_bat[0].pending);step(&g,0,MF_B,MF_B);assert(!g.running_bat[0].pending);
 init(&g,1);step(&g,0,MF_A,MF_A);step(&g,0,0,0);step(&g,0,MF_RIGHT,MF_RIGHT);step(&g,0,0,0);step(&g,0,MF_RIGHT|MF_A,MF_RIGHT|MF_A);
 assert(g.running_bat[0].pending);step(&g,0,0,MF_START);assert(g.paused && !g.running_bat[0].pending);
 init(&g,1);step(&g,0,MF_A,MF_A);g.hitstop=6;old=g.players[0].attack;
 step(&g,0,0,0);step(&g,0,MF_RIGHT,MF_RIGHT);step(&g,0,0,0);step(&g,0,MF_RIGHT|MF_A,MF_RIGHT|MF_A);
 assert(g.running_bat[0].pending && g.players[0].attack==old && !g.dash[0].dir);
 for(i=0;i<40 && !g.players[0].bat;i++)step(&g,0,MF_RIGHT,0);
 assert(g.players[0].bat==MF_BAT_RUNNING);
 puts("PASS bat command buffer: both players/facings, 1..5 punches then FF+A, earliest13/17 transition, no punch cancel/dash boost/extra jab/double attack/spam; FF without A and cancellation guards");
 return original_fast_bat_tests();
}
