#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "game.h"
#include "bat_momentum_config.h"
static void tick(mf_game *g,int who,unsigned h,unsigned e)
{unsigned held[2]={0,0},edge[2]={0,0};held[who]=h;edge[who]=e;mf_game_step_inputs(g,held,edge,3);}
static void init(mf_game *g,int who,int face)
{int i;mf_game_init(g);g->started=1;for(i=0;i<2;i++){g->players[i].active=1;g->players[i].health=100;g->players[i].x=(250+i*30)*256;g->players[i].y=200*256;g->players[i].invulnerable=0;g->enemies[i].state=MF_ENEMY_ABSENT;g->enemies[i].hp=0;g->enemies[i].timer=100000;}for(i=0;i<3;i++){g->drums[i].hp=0;g->drums[i].respawn=-100000;}g->players[who].facing=face;tick(g,who,0,0);}
static void dash(mf_game *g,int who,int face,int delay)
{unsigned dir=face>0?MF_RIGHT:MF_LEFT;tick(g,who,dir,dir);tick(g,who,0,0);tick(g,who,dir,dir);assert(g->dash[who].dir==face);while(delay--)tick(g,who,dir,0);}
static void target(mf_game *g,int n,int who,int face,int lane,int distance)
{mf_enemy *e=&g->enemies[n];e->hp=6;e->state=MF_ENEMY_IDLE;e->x=g->players[who].x+face*distance*256;e->y=g->players[who].y+lane*256;e->grace=99999;}
int main(void)
{mf_game g;int who,face,delay,t,x,score;unsigned dir;
 for(who=0;who<2;who++)for(face=-1;face<=1;face+=2)for(delay=1;delay<=181;delay+=60){
  init(&g,who,face);dir=face>0?MF_RIGHT:MF_LEFT;dash(&g,who,face,delay);x=g.players[who].x;
  tick(&g,who,dir|MF_A,MF_A);assert(g.running_bat[who].active && g.players[who].bat && !g.dash[who].dir && g.running_bat[who].carry==MF_BAT_SLIDE_TICKS-1);
  if(x>30*256 && x<610*256 && (g.players[who].x-g.players[1-who].x)<250*256 && (g.players[1-who].x-g.players[who].x)<250*256)assert(g.players[who].x==x+face*MF_BAT_SLIDE_START);
  for(t=1;t<MF_BAT_SLIDE_TICKS;t++) {
   int before=g.players[who].x;int v=MF_BAT_SLIDE_START*(MF_BAT_SLIDE_TICKS-t)/MF_BAT_SLIDE_TICKS;
   tick(&g,who,dir|MF_A,MF_A);
   if(before>30*256 && before<610*256 && abs(g.players[who].x-g.players[1-who].x)<245*256)assert(g.players[who].x==before+face*v);
  }
  x=g.players[who].x;tick(&g,who,dir|MF_A,MF_A);assert(g.players[who].x==x);
  while(g.players[who].attack)tick(&g,who,dir|MF_A,MF_A);
  assert(!g.running_bat[who].active && !g.dash[who].dir);x=g.players[who].x;tick(&g,who,dir,0);
  if(x>30*256 && x<610*256 && (g.players[who].x-g.players[1-who].x)<250*256 && (g.players[1-who].x-g.players[who].x)<250*256)assert(g.players[who].x==x+face*390);
 }
 /* Activation-tick A is planted and stationary; normal damage stays2. */
 init(&g,0,1);tick(&g,0,MF_RIGHT,MF_RIGHT);tick(&g,0,0,0);x=g.players[0].x;tick(&g,0,MF_RIGHT|MF_A,MF_RIGHT|MF_A);
 assert(g.players[0].bat && !g.running_bat[0].active && g.players[0].x==x);
 target(&g,0,0,1,0,50);while(g.players[0].attack<13)tick(&g,0,0,0);assert(g.enemies[0].hp==4);
 /* Existing mask/multi-target defeat and score once. */
 for(face=-1;face<=1;face+=2){init(&g,0,face);dir=face>0?MF_RIGHT:MF_LEFT;dash(&g,0,face,30);tick(&g,0,dir|MF_A,MF_A);target(&g,0,0,face,0,55);target(&g,1,0,face,0,60);score=g.score;
  for(t=0;t<45;t++)tick(&g,0,0,0);
  assert(g.enemies[0].hp==0 && g.enemies[1].hp==0 && g.score-score==2*MF_ENEMY_DEFEAT_SCORE);
 }
 /* Specials take ordinary bat damage; wrong lane/out-of-reach not killed. */
 init(&g,0,1);dash(&g,0,1,30);tick(&g,0,MF_RIGHT|MF_A,MF_A);target(&g,0,0,1,0,55);g.enemy_class[0]=MF_ENEMY_SPECIAL;target(&g,1,0,1,45,55);
 for(t=0;t<20;t++){tick(&g,0,0,0);}assert(g.enemies[0].hp==4 && g.enemies[1].hp==6);
 /* Damage cancels carry, no new invulnerability. */
 init(&g,0,1);dash(&g,0,1,20);tick(&g,0,MF_RIGHT|MF_A,MF_A);g.enemies[0].hp=6;g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=6;g.enemies[0].x=g.players[0].x+25*256;g.enemies[0].y=g.players[0].y;g.enemies[0].facing=-1;
 tick(&g,0,0,0);assert(g.players[0].health==88 && !g.running_bat[0].active && !g.players[0].attack);
 /* Jump still wins; hitstop buffers classification once. */
 init(&g,0,1);dash(&g,0,1,20);tick(&g,0,MF_RIGHT|MF_B,MF_B);assert(g.players[0].height>0 && !g.running_bat[0].active);
 init(&g,0,1);dash(&g,0,1,20);g.hitstop=3;tick(&g,0,MF_RIGHT|MF_A,MF_A);assert(g.running_bat[0].pending);for(t=0;t<3;t++)tick(&g,0,MF_RIGHT,0);assert(g.running_bat[0].active);
 /* Both actors can begin and complete separate swings on the same tick. */
 init(&g,0,1);g.players[1].facing=-1;
 {unsigned h[2]={MF_RIGHT,MF_LEFT},e[2]={MF_RIGHT,MF_LEFT},z[2]={0,0};
 mf_game_step_inputs(&g,h,e,3);mf_game_step_inputs(&g,z,z,3);mf_game_step_inputs(&g,h,e,3);
 assert(g.dash[0].dir==1 && g.dash[1].dir==-1);x=g.players[0].x;score=g.players[1].x;e[0]=e[1]=MF_A;h[0]|=MF_A;h[1]|=MF_A;mf_game_step_inputs(&g,h,e,3);
 assert(g.running_bat[0].active && g.running_bat[1].active && g.running_bat[0].dir==1 && g.running_bat[1].dir==-1);
 assert(g.players[0].x==x+MF_BAT_SLIDE_START && g.players[1].x==score-MF_BAT_SLIDE_START);
 for(t=1;t<MF_BAT_SLIDE_TICKS;t++){int x0=g.players[0].x,x1=g.players[1].x,v=MF_BAT_SLIDE_START*(MF_BAT_SLIDE_TICKS-t)/MF_BAT_SLIDE_TICKS;e[0]=e[1]=0;mf_game_step_inputs(&g,h,e,3);assert(g.players[0].x==x0+v && g.players[1].x==x1-v && !g.dash[0].dir && !g.dash[1].dir);}
 }
 /* Stage edges and shared camera tether remain authoritative; hitstop freezes slide. */
 for(face=-1;face<=1;face+=2){
  init(&g,0,face);dash(&g,0,face,3);g.players[1].active=0;g.players[0].x=(face>0?614:26)*256;
  tick(&g,0,(face>0?MF_RIGHT:MF_LEFT)|MF_A,MF_A);assert(g.players[0].x==(face>0?614:26)*256);
 }
 init(&g,0,1);dash(&g,0,1,3);tick(&g,0,MF_RIGHT|MF_A,MF_A);x=g.players[0].x;t=g.running_bat[0].carry;g.hitstop=2;
 tick(&g,0,MF_RIGHT,0);assert(g.players[0].x==x && g.running_bat[0].carry==t);
 tick(&g,0,MF_RIGHT,0);assert(g.players[0].x==x && g.running_bat[0].carry==t);
 puts("PASS planted bat slide: both players/mirrors,monotonic fixed-point decay,stage clamps,hitstop,unchanged attack/KO/score/damage/recovery/input");return 0;}
