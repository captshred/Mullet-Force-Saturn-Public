#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "game.h"
#include "bat_momentum_config.h"
static void tick(mf_game *g,unsigned h0,unsigned h1,unsigned p0,unsigned p1)
{unsigned h[2]={h0,h1},p[2]={p0,p1};mf_game_step_inputs(g,h,p,3);}
static void step(mf_game *g,int p,unsigned h,unsigned e)
{tick(g,p?0:h,p?h:0,p?0:e,p?e:0);}
static void init(mf_game *g,int facing)
{
 int i;mf_game_init(g);tick(g,0,0,MF_START,MF_START);
 for(i=0;i<2;i++){g->players[i].x=(300+i*20)*256;g->players[i].y=200*256;g->players[i].facing=facing;g->players[i].invulnerable=10000;g->enemies[i].state=MF_ENEMY_ABSENT;g->enemies[i].hp=0;g->enemies[i].timer=10000;}
 for(i=0;i<3;i++){g->drums[i].hp=0;g->drums[i].respawn=-10000;}
}
static unsigned direction(int f){return f>0?MF_RIGHT:MF_LEFT;}
static void dash(mf_game *g,int p,int f,int phase)
{
 int k;unsigned d=direction(f);step(g,p,0,0);step(g,p,d,d);step(g,p,0,0);step(g,p,d,d);
 for(k=0;k<phase*MF_RUN_FRAME_HOLD;k++)step(g,p,d,0);
 assert(g->dash[p].dir==f);
}
static void target(mf_game *g,int p,int f,int drum,int enemy)
{
 int i,x=g->players[p].x+f*45*256;
 for(i=0;i<3;i++)if(drum){g->drums[i]=(mf_drum){0};g->drums[i].x=x+i*f*4*256;g->drums[i].y=200*256;g->drums[i].hp=3;}
 for(i=0;i<2;i++)if(enemy){g->enemies[i]=(mf_enemy){0};g->enemies[i].x=x+i*f*4*256;g->enemies[i].y=200*256;g->enemies[i].hp=6;g->enemies[i].state=MF_ENEMY_RECOVER;g->enemies[i].timer=10000;g->enemies[i].grace=10000;}
}
int main(void)
{
 mf_game g,ref;int p,f,phase,i,n,hits,whoosh,score,first,x;
 for(p=0;p<2;p++)for(f=-1;f<=1;f+=2)for(phase=0;phase<4;phase++){
  init(&g,f);dash(&g,p,f,phase);target(&g,p,f,1,1);x=g.players[p].x;
  step(&g,p,direction(f)|MF_A,MF_A);assert(g.players[p].bat==MF_BAT_RUNNING && g.running_bat[p].active);
  whoosh=(g.events&MF_COMBAT_BAT(p))!=0;hits=0;first=0;
  while(g.players[p].attack){
   int t=g.players[p].attack;step(&g,p,direction(f),0);
   if(g.events&MF_COMBAT_BAT(p))whoosh++;
   if(g.events&MF_COMBAT_CONNECT(p)){hits++;first=t;}
   assert(!(g.events&MF_COMBAT_JAB(p)));
  }
  assert(first==MF_FAST_BAT_ACTIVE_FIRST && hits==1 && whoosh==1);
  assert(g.broken==3 && g.score==3*110+2*MF_ENEMY_DEFEAT_SCORE);
  for(i=0;i<3;i++)assert(!g.drums[i].hp);
  for(i=0;i<2;i++)assert(!g.enemies[i].hp);
  assert(!g.running_bat[p].active && !g.running_bat[p].carry);
  assert((g.players[p].x-x)*f>0);score=g.score;
  for(i=0;i<20;i++)tick(&g,0,0,0,0);
  assert(g.score==score && hits==1);
 }
 /* Miss duration, active shape and unchanged deceleration, no hit-stop. */
 init(&g,1);dash(&g,0,1,0);step(&g,0,MF_RIGHT|MF_A,MF_A);n=1;
 while(g.players[0].attack){tick(&g,MF_RIGHT,0,0,0);n++;}
 assert(n==MF_FAST_BAT_TOTAL_TICKS && !g.running_bat[0].active);
 /* Every collision boundary is tested, not just a first-contact success. */
 for(i=1;i<=MF_FAST_BAT_TOTAL_TICKS;i++){
  init(&g,1);target(&g,0,1,1,1);g.players[0].bat=MF_BAT_RUNNING;g.players[0].attack=i;g.running_bat[0].active=1;
  tick(&g,0,0,0,0);assert(g.broken==(i>=4 && i<=7?3:0));
  assert(g.score==(i>=4 && i<=7?830:0));
 }
 init(&g,1);dash(&g,0,1,0);step(&g,0,MF_RIGHT|MF_A,MF_A);
 for(i=0;i<40;i++)step(&g,0,MF_RIGHT|MF_A,i==2?MF_A:0);
 assert(!g.players[0].attack && !g.players[0].bat && !g.players[0].torch);
 /* Pause freezes the fast attack and buffered hit-stop cannot duplicate A. */
 init(&g,1);dash(&g,0,1,0);step(&g,0,MF_RIGHT|MF_A,MF_A);n=g.players[0].attack;
 tick(&g,0,0,MF_START,0);for(i=0;i<8;i++)tick(&g,0,0,0,0);assert(g.players[0].attack==n);
 tick(&g,0,0,MF_START,0);assert(g.players[0].attack==n+1);
 /* Both players can independently consume the same dash/A edge. */
 init(&g,1);tick(&g,0,0,0,0);tick(&g,MF_RIGHT,MF_RIGHT,MF_RIGHT,MF_RIGHT);tick(&g,0,0,0,0);tick(&g,MF_RIGHT,MF_RIGHT,MF_RIGHT,MF_RIGHT);
 tick(&g,MF_RIGHT|MF_A,MF_RIGHT|MF_A,MF_A,MF_A);assert(g.players[0].bat==2 && g.players[1].bat==2);
 target(&g,0,1,1,1);for(i=0;i<30;i++)tick(&g,0,0,0,0);
 assert(g.broken==3 && g.score==830);
 /* The second direction edge and A resolve to the approved running attack. */
 for(p=0;p<2;p++)for(f=-1;f<=1;f+=2){
  unsigned d=direction(f);
  init(&g,f);step(&g,p,0,0);step(&g,p,d,d);step(&g,p,0,0);ref=g;
  step(&g,p,d|MF_A,d|MF_A);
  step(&ref,p,d,d);step(&ref,p,d|MF_A,MF_A);
  assert(g.players[p].bat==MF_BAT_RUNNING && g.running_bat[p].active);
  /* Compare every attack tick relative to its initiation, including hitboxes,
     movement, recovery and sound. World x differs by the extra dash tick. */
  x=ref.players[p].x-g.players[p].x;
  for(i=0;i<MF_FAST_BAT_TOTAL_TICKS+8;i++){
   mf_player a=g.players[p],b=ref.players[p];mf_hitbox ha,hb;
   assert(a.attack==b.attack && a.bat==b.bat && a.attack_air==b.attack_air);
   assert(a.x+x==b.x && a.y==b.y && a.height==b.height);
   assert(!memcmp(&g.running_bat[p],&ref.running_bat[p],sizeof(mf_running_bat)));
   assert(g.events==ref.events && !(g.events&MF_COMBAT_JAB(p)));
   ha=mf_player_attackbox(&a);b.x-=x;hb=mf_player_attackbox(&b);
   assert(!memcmp(&ha,&hb,sizeof(ha)));
   step(&g,p,d,0);step(&ref,p,d,0);
  }
  /* A first forward press remains a jab, never a bat. */
  init(&g,f);step(&g,p,0,0);step(&g,p,d|MF_A,d|MF_A);
  assert(!g.players[p].bat && g.players[p].attack && !g.running_bat[p].active);
 }
 /* Air gestures always kick; physics matches a kick-only control. */
 for(p=0;p<2;p++)for(f=-1;f<=1;f+=2){
  init(&g,f);step(&g,p,MF_B,MF_B);ref=g;
  for(i=0;i<70;i++){
   unsigned d=direction(f),e=i==1||i==3?d:0,h=i==1||i>=3?d:0;
   if(i==3){e|=MF_A;h|=MF_A;}
   step(&g,p,h,e);step(&ref,p,h,e&~(MF_LEFT|MF_RIGHT));
   assert(!g.players[p].bat && !g.running_bat[p].active && !g.players[p].bat_window);
   assert(g.players[p].height==ref.players[p].height && g.players[p].vz==ref.players[p].vz);
   if(i==3)assert(g.players[p].attack_air && g.players[p].attack);
   if(!g.players[p].height && !g.players[p].vz)break;
  }
  assert(!g.players[p].attack && !g.players[p].bat && !g.players[p].bat_window);
 }
 init(&g,1);step(&g,0,MF_B|MF_A,MF_B|MF_A);assert(!g.players[0].bat && g.players[0].attack_air);
 puts("PASS fast bat: 12-tick miss, 4..7 contact, two players/facings/all run phases, three barrels and two punks once, immediate and established dash equivalence, single-forward jab, aerial kick/physics and clean landing");return 0;
}
