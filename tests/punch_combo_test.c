#include <assert.h>
#include <stdio.h>
#include "game.h"
static void tick(mf_game *g,unsigned h0,unsigned h1,unsigned p0,unsigned p1)
{unsigned h[2]={h0,h1},p[2]={p0,p1};mf_game_step_inputs(g,h,p,3);}
static void wait(mf_game *g,int n){while(n--)tick(g,0,0,0,0);}
static void init(mf_game *g,int facing)
{
 int i;mf_game_init(g);tick(g,0,0,MF_START,MF_START);
 for(i=0;i<2;i++){g->players[i].x=200*256;g->players[i].y=200*256;g->players[i].facing=facing;g->players[i].invulnerable=10000;g->enemies[i].hp=0;g->enemies[i].state=MF_ENEMY_ABSENT;g->enemies[i].timer=10000;}
 for(i=0;i<3;i++){g->drums[i].hp=0;g->drums[i].respawn=-10000;}
}
static void press(mf_game *g,int p)
{tick(g,p?0:MF_A,p?MF_A:0,p?0:MF_A,p?MF_A:0);}
static void until(mf_game *g,int p,int counter)
{while(g->players[p].attack<counter)tick(g,0,0,0,0);}
int main(void)
{
 mf_game g;int p,f,i,start,n,events,hits,score;
 for(p=0;p<2;p++)for(f=-1;f<=1;f+=2){
  init(&g,f);press(&g,p);assert(g.combo[p].phase==0 && g.combo[p].next==1);
  start=g.ticks;until(&g,p,10);press(&g,p);assert(g.jab[p].buffer>0);while(g.combo[p].phase==0)tick(&g,0,0,0,0);
  assert(g.ticks-start==12 && g.combo[p].phase==1 && g.combo[p].next==2);
  start=g.ticks;until(&g,p,10);press(&g,p);while(g.combo[p].phase==1)tick(&g,0,0,0,0);
  assert(g.ticks-start==12 && g.combo[p].phase==2 && g.combo[p].next==0);
  start=g.ticks;until(&g,p,14);press(&g,p);while(g.combo[p].phase==2)tick(&g,0,0,0,0);
  assert(g.ticks-start==16 && g.combo[p].phase==0 && g.combo[p].next==1);
  assert(g.combo[1-p].next==0 && !g.players[1-p].attack);
 }
 /* An unchained cross lasts28 ticks; same active6..10 and exactly one damage. */
 for(p=0;p<2;p++)for(f=-1;f<=1;f+=2){
  init(&g,f);g.combo[p].next=2;press(&g,p);assert(g.combo[p].phase==2);
  g.enemies[0]=(mf_enemy){0};g.enemies[0].hp=6;g.enemies[0].x=(200+f*40)*256;g.enemies[0].y=200*256;g.enemies[0].state=MF_ENEMY_RECOVER;g.enemies[0].timer=10000;g.enemies[0].grace=10000;
  n=1;hits=0;events=1;score=0;
  while(g.players[p].attack){int t=g.players[p].attack;tick(&g,0,0,0,0);if(g.events&MF_COMBAT_JAB(p))events++;if(g.events&(MF_COMBAT_CONNECT(p)|MF_COMBAT_NONKILL(p))){assert(t==6);hits++;score=g.score;}}
  assert(g.combo[p].phase==2 && g.enemies[0].hp==5 && hits==1 && events==1 && g.score==score);(void)n;
 }
 init(&g,1);g.combo[0].next=2;press(&g,0);n=1;while(g.players[0].attack){wait(&g,1);n++;}assert(n==28);
 /* Timeout at45 simulation ticks from initiation, pauses/hit-stop do not age. */
 init(&g,1);press(&g,0);wait(&g,44);assert(g.combo[0].next==1);wait(&g,1);assert(!g.combo[0].next && !g.combo[0].timeout);press(&g,0);assert(g.combo[0].phase==0);
 init(&g,1);press(&g,0);n=g.combo[0].timeout;tick(&g,0,0,MF_START,0);wait(&g,8);assert(g.combo[0].timeout==n);tick(&g,0,0,MF_START,0);
 /* Held input cannot advance combo; interruption resets per-player state. */
 init(&g,1);press(&g,0);for(i=0;i<35;i++)tick(&g,MF_A,0,0,0);assert(g.combo[0].next==1 && !g.players[0].attack);
 for(i=0;i<5;i++){
  init(&g,1);press(&g,0);
  if(i==0)g.players[0].hurt=3;
  if(i==1)g.players[0].health=0;
  if(i==2)g.players[0].height=20*256;
  if(i==3)g.players[0].bat=1;
  if(i==4)g.players[0].torch=MF_TORCH_FIRE;
  wait(&g,1);assert(!g.combo[0].next && !g.combo[0].timeout && !g.combo[0].phase);
 }
 init(&g,1);press(&g,0);wait(&g,25);tick(&g,MF_B,0,MF_B,0);assert(!g.combo[0].next && g.players[0].height);
 init(&g,1);press(&g,0);wait(&g,25);tick(&g,MF_RIGHT,0,MF_RIGHT,0);wait(&g,1);tick(&g,MF_RIGHT|MF_A,0,MF_RIGHT|MF_A,0);assert(g.players[0].bat && !g.combo[0].next);
 init(&g,1);tick(&g,MF_A,MF_A,MF_A,MF_A);assert(g.combo[0].next==1 && g.combo[1].next==1);
 wait(&g,8);tick(&g,MF_A,0,MF_A,0);while(g.combo[0].phase==0)wait(&g,1);assert(g.combo[0].phase==1 && g.combo[1].phase==0);
 puts("PASS combo: both players/facings, buffered jab/jab/cross/next-jab intervals12/12/16,28-tick cross,unchanged6..10 active/one damage/SFX,45-tick timeout,held rejection,independent players,damage/death/jump/bat/torch resets,pause freeze");return 0;
}
