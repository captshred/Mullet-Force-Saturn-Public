/* Input-only deterministic patrol/combat bot, normal HP/deaths/spawn mix.
   No attack forcing, NPC state writes, instant heals or cooldown bypass. */
#include <stdio.h>
#include "game.c"
int main(void) {
 unsigned total[3]={0},states[8]={0};int seeds=4,ticks=60000;
 for(int seed=1;seed<=seeds;seed++) {
  mf_game g;unsigned rng=seed,previous[2]={0};mf_game_init(&g);
  for(int t=0;t<ticks;t++) {
   unsigned held[2]={0},pressed[2]={0};int before[2];
   for(int p=0;p<2;p++) {
    int phase=(t+p*70)%900;
    held[p]|=phase<300?MF_RIGHT:phase<600?MF_LEFT:0;
    if((t+p*37)%360<32)held[p]|=MF_UP;
    if((t+p*37)%360>=180 && (t+p*37)%360<212)held[p]|=MF_DOWN;
    rng=rng*1664525u+1013904223u;
    if((t+p*13)%400<110 || (rng>>28)<5)held[p]|=MF_A;
    if((t+p*31)%95<2)held[p]|=MF_B;
    pressed[p]=held[p]&~previous[p];previous[p]=held[p];
   }
   if(t==0)pressed[0]|=MF_START;
   if(t==60)pressed[1]|=MF_START;
   for(int e=0;e<2;e++)before[e]=g.enemies[e].state;
   mf_game_step_inputs(&g,held,pressed,3);
   for(int e=0;e<2;e++)if(g.enemy_class[e]==MF_ENEMY_RICKY) {
    states[g.enemies[e].state]++;
    if(before[e]!=MF_ENEMY_WINDUP && g.enemies[e].state==MF_ENEMY_WINDUP)
#ifdef MF_RICKY_JUMP_MIN
     total[g.ricky_jump[e].active?2:g.ricky_punch[e]?0:1]++;
#else
     total[g.ricky_punch[e]?0:1]++;
#endif
   }
  }
 }
 printf("{\"seeds\":%d,\"ticks_per_seed\":%d,\"simulated_minutes\":%.2f,\"punch\":%u,\"standing_chain\":%u,\"jump_chain\":%u,\"ricky_slot_ticks_by_state\":[",seeds,ticks,seeds*ticks/3600.,total[0],total[1],total[2]);
 for(int i=0;i<8;i++)printf("%s%u",i?",":"",states[i]);puts("],\"method\":\"normal two-player patrol/attack inputs, real health/recovery and original enemy mix; no NPC forcing\"}");
 return !(total[0] && total[1]);
}
