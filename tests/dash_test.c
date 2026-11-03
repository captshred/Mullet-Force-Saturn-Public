#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include "game.h"
#define NORMAL 390
#define FAST (NORMAL*MF_DASH_SPEED_NUM/MF_DASH_SPEED_DEN)
static void tick(mf_game *g,unsigned h0,unsigned h1,unsigned e0,unsigned e1)
{unsigned h[2]={h0,h1},e[2]={e0,e1};mf_game_step_inputs(g,h,e,3);}
static void input(mf_game *g,int p,unsigned h,unsigned e){tick(g,p?0:h,p?h:0,p?0:e,p?e:0);}
static void wait(mf_game *g,int n){while(n--)tick(g,0,0,0,0);}
static void init(mf_game *g)
{
 int i;mf_game_init(g);tick(g,0,0,MF_START,MF_START);wait(g,1);
 for(i=0;i<2;i++){g->players[i].x=(200+i*40)*256;g->players[i].y=200*256;g->players[i].invulnerable=0;g->enemies[i].state=MF_ENEMY_ABSENT;g->enemies[i].hp=0;g->enemies[i].timer=100000;}
 for(i=0;i<3;i++){g->drums[i].hp=0;g->drums[i].respawn=-100000;}
}
static void pair(mf_game *g,int p,unsigned dir,int gap,unsigned extra)
{int t;input(g,p,dir,dir);for(t=1;t<gap;t++)input(g,p,0,0);input(g,p,dir|extra,dir|extra);}
int main(void)
{
 mf_game g,other;int p,face,t,x,y,hp;unsigned dir;int speed=FAST;
 assert(sizeof(mf_dash_state)==28 && sizeof(g.dash)==56);
 for(p=0;p<2;p++)for(face=-1;face<=1;face+=2){
  init(&g);dir=face>0?MF_RIGHT:MF_LEFT;g.players[p].facing=face;x=g.players[p].x;
  input(&g,p,dir,dir);assert(g.players[p].x==x+face*NORMAL && !g.dash[p].dir);
  input(&g,p,0,0);x=g.players[p].x;input(&g,p,dir,dir);
  assert(g.dash[p].dir==face && g.players[p].x==x+face*speed && !g.dash[1-p].dir && !g.players[p].attack);
  for(t=0;t<15;t++){input(&g,p,dir,dir);assert(g.dash[p].dir==face);}
  input(&g,p,0,0);assert(!g.dash[p].dir);input(&g,p,dir,dir);assert(!g.dash[p].dir);
 }
 puts("PASS dash both players/facings, exact speed, distinct release, held-edge filtering, no repeated activation");
 for(t=2;t<=MF_DASH_TAP_TICKS+2;t++){
  init(&g);pair(&g,0,MF_RIGHT,t,0);assert((g.dash[0].dir!=0)==(t<=MF_DASH_TAP_TICKS));
 }
 init(&g);input(&g,0,MF_RIGHT,MF_RIGHT);for(t=0;t<40;t++){input(&g,0,MF_RIGHT,MF_RIGHT);assert(!g.dash[0].dir);}
 input(&g,0,0,0);input(&g,0,MF_RIGHT,MF_RIGHT);assert(!g.dash[0].dir);
 init(&g);input(&g,0,MF_RIGHT,MF_RIGHT);input(&g,0,MF_LEFT,MF_LEFT);assert(!g.dash[0].dir);input(&g,0,0,0);input(&g,0,MF_LEFT,MF_LEFT);assert(g.dash[0].dir==-1);
 init(&g);pair(&g,0,MF_RIGHT,2,0);input(&g,0,MF_LEFT,MF_LEFT);assert(!g.dash[0].dir && g.players[0].facing==-1);
 init(&g);input(&g,0,MF_LEFT|MF_RIGHT,MF_LEFT|MF_RIGHT);input(&g,0,MF_RIGHT,MF_RIGHT);assert(!g.dash[0].dir);wait(&g,1);pair(&g,0,MF_RIGHT,2,0);assert(g.dash[0].dir);
 puts("PASS inclusive12-tick boundary, slow taps, opposite/ambiguous directions and reversal");
 init(&g);input(&g,0,MF_RIGHT|MF_UP,MF_RIGHT);input(&g,0,MF_UP,0);x=g.players[0].x;y=g.players[0].y;input(&g,0,MF_RIGHT|MF_UP,MF_RIGHT);
 assert(g.dash[0].dir && g.players[0].x-x==speed*181/256 && y-g.players[0].y==(speed*181/256)*3/4);
 x=g.players[0].x;y=g.players[0].y;input(&g,0,MF_UP,0);assert(!g.dash[0].dir && g.players[0].x==x && y-g.players[0].y==NORMAL*3/4);
 init(&g);tick(&g,MF_RIGHT,MF_LEFT,MF_RIGHT,MF_LEFT);tick(&g,0,0,0,0);tick(&g,MF_RIGHT,MF_LEFT,MF_RIGHT,MF_LEFT);assert(g.dash[0].dir==1 && g.dash[1].dir==-1);
 input(&g,0,MF_RIGHT,0);assert(g.dash[0].dir && !g.dash[1].dir);
 other=g;input(&g,0,0,0);assert(!g.dash[0].dir && other.dash[0].dir);
 puts("PASS diagonal normalization, independent P1/P2 and independent game copies");
 for(p=0;p<2;p++)for(face=-1;face<=1;face+=2){
  init(&g);g.players[p].facing=face;dir=face>0?MF_RIGHT:MF_LEFT;input(&g,p,dir,dir);input(&g,p,0,0);x=g.players[p].x;input(&g,p,dir|MF_A,dir|MF_A);
  assert(g.players[p].bat && g.players[p].attack && !g.dash[p].dir && g.players[p].x==x);
 }
 init(&g);pair(&g,0,MF_RIGHT,2,0);x=g.players[0].x;input(&g,0,MF_RIGHT|MF_A,MF_A);assert(g.players[0].bat && !g.dash[0].dir && g.players[0].x==x);
 init(&g);pair(&g,0,MF_RIGHT,MF_DASH_TAP_TICKS+1,MF_A);assert(g.players[0].bat && !g.dash[0].dir);
 init(&g);pair(&g,0,MF_RIGHT,2,0);for(t=0;t<MF_BAT_ATTACK_TICKS+2;t++)input(&g,0,MF_RIGHT,0);x=g.players[0].x;input(&g,0,MF_RIGHT|MF_A,MF_A);assert(g.players[0].attack && !g.players[0].bat && !g.dash[0].dir && g.players[0].x-x==NORMAL);
 init(&g);pair(&g,0,MF_RIGHT,2,0);x=g.players[0].x;input(&g,0,MF_RIGHT|MF_B,MF_B);assert(!g.dash[0].dir && g.players[0].height==1510 && g.players[0].x-x==NORMAL);
 input(&g,0,MF_RIGHT|MF_A,MF_A);assert(g.players[0].attack_air && !g.dash[0].dir);
 while(g.players[0].height)input(&g,0,MF_RIGHT,MF_RIGHT);
 for(t=0;t<8;t++){input(&g,0,MF_RIGHT,MF_RIGHT);assert(!g.dash[0].dir);}
 wait(&g,1);pair(&g,0,MF_RIGHT,2,0);assert(g.dash[0].dir);
 puts("PASS same-tick/delayed FF+A bat priority, original slow bat window, punch/jump/kick and held landing guards");
 init(&g);pair(&g,0,MF_RIGHT,2,0);for(t=0;t<MF_BAT_ATTACK_TICKS+2;t++)input(&g,0,MF_RIGHT,0);input(&g,0,MF_RIGHT|MF_A,MF_A);
 for(t=0;t<MF_TORCH_CHARGE_TICKS+5;t++){input(&g,0,MF_RIGHT|MF_A,0);assert(!g.dash[0].dir);}
 assert(g.players[0].torch==MF_TORCH_FIRE);input(&g,0,MF_RIGHT,0);assert(!g.dash[0].dir);
 init(&g);pair(&g,0,MF_RIGHT,2,0);g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=5;g.enemies[0].hp=6;g.enemies[0].facing=1;g.enemies[0].x=g.players[0].x-20*256;g.enemies[0].y=g.players[0].y;hp=g.players[0].health;
 input(&g,0,MF_RIGHT,0);assert(g.players[0].health==hp-MF_ENEMY_DAMAGE && g.players[0].hurt && !g.dash[0].dir);
 init(&g);pair(&g,0,MF_RIGHT,2,0);g.hitstop=3;x=g.players[0].x;y=g.dash[0].anim;for(t=0;t<3;t++){input(&g,0,MF_RIGHT,0);assert(g.dash[0].dir && g.players[0].x==x && g.dash[0].anim==y);}input(&g,0,MF_RIGHT,0);assert(g.players[0].x-x==speed);
 g.hitstop=2;input(&g,0,0,0);input(&g,0,MF_RIGHT,MF_RIGHT);input(&g,0,MF_RIGHT,0);assert(!g.dash[0].dir);
 puts("PASS torch charge/fire, damage cancellation and held-dash hit-stop freeze without buffered activation");
 init(&g);pair(&g,0,MF_RIGHT,2,0);input(&g,0,MF_RIGHT,MF_START);assert(g.paused && !g.dash[0].dir);input(&g,0,MF_RIGHT,MF_START);assert(!g.paused && !g.dash[0].dir);for(t=0;t<20;t++){input(&g,0,MF_RIGHT,MF_RIGHT);assert(!g.dash[0].dir);}
 mf_game_init(&g);input(&g,0,MF_RIGHT,MF_RIGHT);input(&g,0,0,0);input(&g,0,MF_RIGHT,MF_START|MF_RIGHT);assert(!g.dash[0].dir);input(&g,0,0,0);input(&g,0,MF_RIGHT,MF_RIGHT);assert(!g.dash[0].dir);
 init(&g);pair(&g,0,MF_RIGHT,2,0);{unsigned h[2]={MF_RIGHT,0},e[2]={0,0};mf_game_step_inputs(&g,h,e,2);assert(!g.dash[0].dir);mf_game_step_inputs(&g,h,e,3);assert(!g.dash[0].dir);}
 init(&g);g.players[0].health=0;g.players[0].defeated=1;input(&g,0,MF_RIGHT,MF_RIGHT);assert(g.players[0].health==100 && !g.dash[0].dir);input(&g,0,MF_RIGHT,MF_RIGHT);assert(!g.dash[0].dir);
 init(&g);g.players[1].active=0;pair(&g,0,MF_RIGHT,2,0);tick(&g,MF_RIGHT,MF_RIGHT,0,MF_START|MF_RIGHT);assert(g.dash[0].dir && g.players[1].active && !g.dash[1].dir);
 init(&g);pair(&g,0,MF_RIGHT,2,0);for(t=0;t<MF_BAT_ATTACK_TICKS+2;t++)input(&g,0,MF_RIGHT,0);input(&g,0,MF_RIGHT|MF_A,MF_A);for(t=0;t<45;t++){input(&g,0,MF_RIGHT,MF_RIGHT);assert(!g.dash[0].dir);}wait(&g,1);pair(&g,0,MF_RIGHT,2,0);assert(g.dash[0].dir);
 puts("PASS menu/pause/resume/disconnect/respawn/join/attack-recovery guards");
 init(&g);g.players[1].active=0;pair(&g,0,MF_RIGHT,2,0);g.players[0].x=614*256-1;input(&g,0,MF_RIGHT|MF_DOWN,0);assert(g.players[0].x==614*256 && g.camera==320);g.players[0].y=229*256;input(&g,0,MF_RIGHT|MF_DOWN,0);assert(g.players[0].y==229*256);
 input(&g,0,0,0);pair(&g,0,MF_LEFT,2,0);g.players[0].x=26*256+1;g.players[0].y=168*256;input(&g,0,MF_LEFT|MF_UP,0);assert(g.players[0].x==26*256 && g.players[0].y==168*256 && g.camera==0);
 init(&g);pair(&g,0,MF_LEFT,2,0);for(t=0;t<300;t++){input(&g,0,MF_LEFT,0);assert(g.players[1].x-g.players[0].x<=260*256 && g.camera>=0 && g.camera<=320);}
 puts("PASS original world/depth bounds and shared camera tether");
 printf("PASS preset%d/10, dash speed%d/256 pixels/tick,56 bytes per-game state, no heap or texture resources\n",MF_DASH_PRESET,speed);return 0;
}
