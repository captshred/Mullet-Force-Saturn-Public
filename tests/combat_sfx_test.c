#include <assert.h>
#include <stdio.h>
#include "game.h"
static unsigned previous[2];
static void step(mf_game *g,unsigned a,unsigned b){unsigned h[2]={a,b},e[2]={a&~previous[0],b&~previous[1]};previous[0]=a;previous[1]=b;mf_game_step_inputs(g,h,e,3);}
static void init(mf_game *g){int i;mf_game_init(g);g->started=1;previous[0]=previous[1]=0;
for(i=0;i<2;i++){g->players[i].active=1;g->players[i].health=100;g->players[i].x=(200+100*i)*256;g->players[i].y=200*256;g->players[i].facing=i?-1:1;g->players[i].invulnerable=0;g->players[i].a_blocked=0;g->enemies[i].hp=0;g->enemies[i].state=MF_ENEMY_ABSENT;g->enemies[i].timer=100000;}
for(i=0;i<3;i++){g->drums[i].hp=0;g->drums[i].respawn=-100000;}step(g,0,0);}
static void target(mf_game *g,int n,int actor){mf_enemy *e=&g->enemies[n];e->hp=6;e->state=MF_ENEMY_IDLE;e->x=g->players[actor].x+g->players[actor].facing*30*256;e->y=g->players[actor].y;e->grace=99999;}
int main(void){mf_game g;int i,j,hits,starts;
for(i=0;i<2;i++){
 init(&g);step(&g,i?0:MF_A,i?MF_A:0);assert(g.events&MF_COMBAT_JAB(i));assert(!(g.events&MF_COMBAT_NONKILL(i)));
 for(j=0;j<8;j++){step(&g,i?0:MF_A,i?MF_A:0);assert(!(g.events&MF_COMBAT_JAB(i)));}
 init(&g);target(&g,0,i);target(&g,1,i);hits=0;
 for(j=0;j<35;j++){step(&g,j==0 && !i?MF_A:0,j==0 && i?MF_A:0);if(g.events&MF_COMBAT_NONKILL(i))hits++;assert(!(g.events&MF_COMBAT_NONKILL(1-i)));}
 assert(hits==1 && g.enemies[0].hp==5 && g.enemies[1].hp==5);
 /* Real forward-forward -> run -> A begins one bat whoosh, not on carrying. */
 init(&g);{unsigned d=i?MF_LEFT:MF_RIGHT;step(&g,i?0:d,i?d:0);step(&g,0,0);step(&g,i?0:d,i?d:0);assert(g.dash[i].dir);
 for(j=0;j<4;j++){step(&g,i?0:d,i?d:0);assert(!(g.events&MF_COMBAT_BAT(i)));}
 step(&g,i?0:d|MF_A,i?d|MF_A:0);assert(g.events&MF_COMBAT_BAT(i));starts=1;
 for(j=0;j<30;j++){step(&g,i?0:d|MF_A,i?d|MF_A:0);if(g.events&MF_COMBAT_BAT(i))starts++;}assert(starts==1);}
 /* Standing and aerial gestures both emit bat initiation exactly once. */
 for(j=0;j<2;j++){
  unsigned d=i?MF_LEFT:MF_RIGHT;int k;
  init(&g);if(j)step(&g,i?0:MF_B,i?MF_B:0);
  step(&g,i?0:d,i?d:0);step(&g,0,0);
  step(&g,i?0:d|MF_A,i?d|MF_A:0);
  assert(g.players[i].bat && !!g.players[i].attack_air==j);
  assert(g.events&MF_COMBAT_BAT(i));
  for(k=0;k<12;k++){step(&g,0,0);assert(!(g.events&MF_COMBAT_BAT(i)));}
 }
 /* Aerial kick has no jab whoosh; its confirmed hit still gets CONNECT. */
 init(&g);g.players[i].height=20*256;g.players[i].vz=1;target(&g,0,i);hits=0;
 for(j=0;j<20;j++){step(&g,j==0 && !i?MF_A:0,j==0 && i?MF_A:0);assert(!(g.events&MF_COMBAT_JAB(i)));if(g.events&MF_COMBAT_NONKILL(i))hits++;}assert(hits==1);
}
init(&g);target(&g,0,1);g.players[1].torch=MF_TORCH_FIRE;
step(&g,0,MF_A);assert(g.events&MF_COMBAT_NONKILL(1));assert(g.enemies[0].hp==5);
step(&g,0,MF_A);assert(!(g.events&MF_COMBAT_NONKILL(1)));
init(&g);step(&g,MF_A,MF_A);assert((g.events&(MF_COMBAT_JAB(0)|MF_COMBAT_JAB(1)))==(MF_COMBAT_JAB(0)|MF_COMBAT_JAB(1)));
puts("PASS custom events: both-player immediate jabs, held/missed attacks, same-tick multi-target impacts once, real running-bat initiation only, aerial CONNECT without whoosh");return 0;}
