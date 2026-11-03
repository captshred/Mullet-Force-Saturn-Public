#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "game.h"
#include "jab_config.h"
static unsigned previous[2];
static void init(mf_game *g)
{
 int i;mf_game_init(g);g->started=1;memset(previous,0,sizeof(previous));
 for(i=0;i<2;i++){g->players[i].active=1;g->players[i].health=100;g->players[i].x=(220+i*60)*256;g->players[i].y=200*256;g->players[i].invulnerable=0;g->players[i].a_blocked=0;g->enemies[i].state=MF_ENEMY_ABSENT;g->enemies[i].hp=0;g->enemies[i].timer=100000;}
 for(i=0;i<3;i++){g->drums[i].hp=0;g->drums[i].respawn=-100000;}
}
static void tick(mf_game *g,unsigned a,unsigned b,unsigned connected)
{unsigned h[2]={a,b},e[2]={a&~previous[0],b&~previous[1]};previous[0]=a;previous[1]=b;mf_game_step_inputs(g,h,e,connected);}
static void until(mf_game *g,int actor,int counter)
{int n=0;while(g->players[actor].attack<counter){tick(g,0,0,3);assert(++n<100);}}
int main(void)
{
 mf_game g;int i,j,n,starts,before,starttick,firsttick,old,damage,face;
 /* A single edge and a held A both produce only one jab; no repeat at idle. */
 for(i=0;i<2;i++){
  init(&g);tick(&g,i?0:MF_A,i?MF_A:0,3);assert(g.players[i].attack==2);starts=1;
  for(n=0;n<50;n++){before=g.players[i].attack;tick(&g,0,0,3);if(g.players[i].attack && (!before || g.players[i].attack<before))starts++;}
  assert(starts==1 && !g.players[i].attack);
  init(&g);starts=0;
  for(n=0;n<50;n++){before=g.players[i].attack;tick(&g,i?0:MF_A,i?MF_A:0,3);if(g.players[i].attack && (!before || g.players[i].attack<before))starts++;}
  assert(starts==1 && !g.players[i].attack && !g.players[i].torch);
 }
 /* Long hold retains the existing torch charge instead of auto-jabbing. */
 init(&g);starts=0;for(n=0;n<120;n++){before=g.players[0].attack;tick(&g,MF_A,0,3);if(g.players[0].attack && (!before || g.players[0].attack<before))starts++;}assert(starts==1 && g.players[0].torch==MF_TORCH_FIRE && !g.jab[0].buffer);
 /* Exactly three deliberate presses; late inputs cancel after12 elapsed ticks. */
 for(i=0;i<2;i++)for(face=-1;face<=1;face+=2){
  init(&g);g.players[i].facing=face;tick(&g,i?0:MF_A,i?MF_A:0,3);firsttick=g.ticks;
  for(j=0;j<2;j++){
   until(&g,i,8);tick(&g,i?0:MF_A,i?MF_A:0,3);assert(g.jab[i].buffer>0);starttick=g.ticks;
   old=g.players[i].attack;n=0;while(g.players[i].attack>=old){old=g.players[i].attack;tick(&g,0,0,3);assert(++n<10);}
   assert(g.players[i].attack==2 && g.ticks-firsttick==MF_JAB_REPEAT_COUNTER-1 && g.ticks>starttick);firsttick=g.ticks;assert(!g.jab[i].buffer && !g.players[i].bat);
  }
  for(n=0;n<30;n++){before=g.players[i].attack;tick(&g,0,0,3);assert(!g.players[i].attack || g.players[i].attack>=before);}
 }
 /* Too-early second edge expires; an edge at eligibility dispatches immediately. */
 init(&g);tick(&g,MF_A,0,3);tick(&g,0,0,3);tick(&g,MF_A,0,3);for(n=0;n<30;n++){before=g.players[0].attack;tick(&g,0,0,3);assert(!g.players[0].attack || g.players[0].attack>=before);}assert(!g.jab[0].buffer);
 init(&g);tick(&g,MF_A,0,3);until(&g,0,MF_JAB_REPEAT_COUNTER);tick(&g,MF_A,0,3);assert(g.players[0].attack==2 && !g.jab[0].buffer);
 /* Per-target mask resets only on a genuinely new jab. */
 init(&g);g.enemies[0].state=MF_ENEMY_IDLE;g.enemies[0].hp=6;g.enemies[0].grace=99999;g.enemies[0].x=g.players[0].x+35*256;g.enemies[0].y=g.players[0].y;tick(&g,MF_A,0,3);starts=1;damage=0;
 for(n=0;n<55;n++){
  unsigned a=0;before=g.players[0].attack;old=g.enemies[0].hp;
  if(starts==1 && g.players[0].attack==11)a=MF_A;
  g.enemies[0].x=g.players[0].x+35*256;g.enemies[0].vx=0;
  tick(&g,a,0,3);if(g.players[0].attack && g.players[0].attack<before)starts++;
  damage+=old-g.enemies[0].hp;
 }
 assert(starts==2 && damage==2 && g.enemies[0].hp==4);
 /* Hit-stop freezes both eligibility and queue age. */
 init(&g);tick(&g,MF_A,0,3);until(&g,0,13);g.hitstop=3;tick(&g,MF_A,0,3);assert(g.jab[0].buffer==MF_JAB_BUFFER_TICKS && g.players[0].attack==13);
 tick(&g,0,0,3);assert(g.jab[0].buffer==MF_JAB_BUFFER_TICKS && g.players[0].attack==13);tick(&g,0,0,3);assert(g.players[0].attack==13);tick(&g,0,0,3);assert(g.players[0].attack==2 && !g.jab[0].buffer);
 /* All interruption/priority paths discard, rather than defer, the queued jab. */
 for(i=0;i<9;i++){
  init(&g);tick(&g,MF_A,0,3);until(&g,0,8);tick(&g,MF_A,0,3);assert(g.jab[0].buffer);
  if(i==0)g.players[0].hurt=4;
  if(i==1)g.players[0].health=0;
  if(i==2)g.players[0].bat=1;
  if(i==3)g.players[0].torch=MF_TORCH_FIRE;
  if(i==4)g.players[0].height=256;
  if(i==5)g.running_bat[0].pending=1;
  tick(&g,i==6?MF_B:i==7?MF_START:0,0,i==8?2:3);assert(!g.jab[0].buffer);
 }
 /* A buffered B during hitstop also beats a later buffered jab. */
 init(&g);tick(&g,MF_A,0,3);until(&g,0,13);g.hitstop=3;tick(&g,MF_B,0,3);tick(&g,0,0,3);tick(&g,MF_A,0,3);tick(&g,0,0,3);assert(g.players[0].attack!=2 && !g.jab[0].buffer);
 /* Independent queues can restart on different ticks. */
 init(&g);tick(&g,MF_A,0,3);tick(&g,0,MF_A,3);until(&g,0,8);tick(&g,MF_A,0,3);tick(&g,0,MF_A,3);n=0;
 for(i=0;i<8;i++){before=g.players[0].attack;old=g.players[1].attack;tick(&g,0,0,3);if(g.players[0].attack<before)n|=1;if(g.players[1].attack<old)n|=2;}assert(n==3);
 puts("PASS jab repeat: fresh-edge single/hold,3 taps,12-tick restart,6-tick expiry,one hit/target/jab,hitstop,interruptions,priority,independent players/mirrors");return 0;
}
