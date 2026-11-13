#include <assert.h>
#include <stdio.h>
#include "game.c"
static void setup(mf_game *g,int player,int facing,int camera) {
 mf_game_init(g);g->started=1;g->camera=camera;g->camera_floor=mf_world_checkpoint(camera);g->spawn_wait=100000;
 for(int i=0;i<3;i++)g->drums[i].hp=0;
 for(int i=0;i<2;i++){g->enemies[i].state=MF_ENEMY_ABSENT;g->players[i].active=0;}
 int root=camera+(facing>0?100:220);
 g->players[player]=(mf_player){.active=1,.health=100,.x=(root+facing*100)*256,.y=200*256,.facing=-facing};
 g->enemies[0]=(mf_enemy){.x=root*256,.y=200*256,.hp=6,.facing=facing,.state=MF_ENEMY_IDLE,.target=-1};
 g->enemy_class[0]=MF_ENEMY_RICKY;
}
static void launch(mf_game *g) {
 enemy_step(g,0);assert(g->ricky_jump[0].active && g->enemies[0].state==MF_ENEMY_WINDUP);
 for(int i=0;i<MF_RICKY_JUMP_WINDUP-1;i++){enemy_step(g,0);assert(g->enemies[0].state==MF_ENEMY_WINDUP);}
 enemy_step(g,0);assert(g->enemies[0].state==MF_ENEMY_ACTIVE);
}
int main(void) {
 mf_game g;int p,f,c,i;
 for(p=0;p<2;p++)for(f=-1;f<=1;f+=2)for(c=0;c<=960;c+=320) {
  setup(&g,p,f,c);int x=g.enemies[0].x;launch(&g);
  int dx=g.ricky_jump[0].dx,dy=g.ricky_jump[0].dy;
  assert(dx*f>0 && g.enemies[0].x!=x);
  for(i=1;i<MF_RICKY_JUMP_AIR;i++) {
   int t=MF_RICKY_JUMP_AIR-g.enemies[0].timer;
   g.players[p].invulnerable=0;enemy_step(&g,0);
   if(t<MF_RICKY_JUMP_ACTIVE_FIRST)assert(g.players[p].health==100);
   assert(g.players[p].health>=99 && g.enemies[0].x>=26*256 && g.enemies[0].x<=1254*256);
   assert(g.ricky_jump[0].dx==dx && g.ricky_jump[0].dy==dy);
  }
  assert(g.players[p].health==99 && g.enemies[0].hit_done==(1<<p));
  assert(g.enemies[0].state==MF_ENEMY_RECOVER && g.enemies[0].timer==18 && !g.ricky_jump[0].height);
  for(i=0;i<17;i++){enemy_step(&g,0);assert(g.enemies[0].state==MF_ENEMY_RECOVER);}
  enemy_step(&g,0);assert(!g.ricky_jump[0].active && g.ricky_jump[0].cooldown>0);
 }
 /* No homing after launch: moving to a different lane/behind/above evades. */
 for(i=0;i<4;i++) {
  setup(&g,0,1,0);launch(&g);int end=g.ricky_jump[0].start_x+g.ricky_jump[0].dx;
  if(i==0)g.players[0].y+=30*256;
  if(i==1)g.players[0].x=30*256;
  if(i==2)g.players[0].height=100*256;
  if(i==3)g.players[0].invulnerable=100;
  while(g.enemies[0].state==MF_ENEMY_ACTIVE)enemy_step(&g,0);
  assert(g.players[0].health==100 && g.enemies[0].x==end);
 }
 /* Exact world-edge approaches and a checkpoint advancing during flight. */
 for(f=-1;f<=1;f+=2) {
  setup(&g,0,f,f>0?960:0);
  g.enemies[0].x=(f>0?1154:126)*256;g.players[0].x=(f>0?1254:26)*256;
  launch(&g);while(g.enemies[0].state==MF_ENEMY_ACTIVE){enemy_step(&g,0);assert(g.enemies[0].x>=26*256 && g.enemies[0].x<=1254*256);}
  assert(g.enemies[0].x==(f>0?1232:48)*256);
 }
 setup(&g,0,1,540);launch(&g);int flight=g.enemies[0].x;
 g.camera=640;g.camera_floor=640;enemy_step(&g,0);
 assert(g.enemies[0].x>=flight && g.enemies[0].x-flight<5*256 && g.enemies[0].state==MF_ENEMY_ACTIVE);
 while(g.enemies[0].state==MF_ENEMY_ACTIVE)enemy_step(&g,0);
 assert(g.enemies[0].x>=666*256);
 /* Both players independently latch, even if invulnerability is externally reset. */
 setup(&g,0,1,0);g.players[1]=g.players[0];launch(&g);
 while(g.enemies[0].state==MF_ENEMY_ACTIVE){g.players[0].invulnerable=g.players[1].invulnerable=0;enemy_step(&g,0);}
 assert(g.players[0].health==99 && g.players[1].health==99 && g.enemies[0].hit_done==3);
 /* Windup is vulnerable to punch, bat and jump kick; landing can be punished. */
 for(i=0;i<4;i++) {
  setup(&g,0,1,0);enemy_step(&g,0);
  if(i==3){for(int t=0;t<40;t++)enemy_step(&g,0);assert(g.enemies[0].state==MF_ENEMY_RECOVER);}
  mf_player *p=&g.players[0];p->hurt=0;p->x=g.enemies[0].x+30*256;p->attack=i==1?MF_FAST_BAT_ACTIVE_FIRST:8;
  p->bat=i==1?MF_BAT_RUNNING:0;p->attack_air=i==2;p->height=i==2?12*256:0;
  player_hits(&g,p);assert(g.enemies[0].state==MF_ENEMY_HURT);enemy_step(&g,0);assert(!g.ricky_jump[0].active);
 }
 /* Actual contact cancels every queued flight stage; release never resumes it. */
 for(i=0;i<3;i++) {
  setup(&g,0,1,0);if(i)launch(&g);else enemy_step(&g,0);
  if(i==2)while(g.enemies[0].state==MF_ENEMY_ACTIVE)enemy_step(&g,0);
  mf_player *p=&g.players[0];p->x=g.enemies[0].x+30*256;p->torch=MF_TORCH_FIRE;p->torch_tick=0;
  enemy_step(&g,0);assert(!g.ricky_jump[0].active && !g.ricky_jump[0].height && g.ricky_jump[0].cooldown>0 && g.enemies[0].state==MF_ENEMY_IDLE);
  p->torch=0;enemy_step(&g,0);assert(!g.ricky_jump[0].active);
 }
 /* A death mid-flight cannot complete the pending hit; slot reuse resets state. */
 setup(&g,0,1,0);launch(&g);g.enemies[0].hp=1;fire_damage(&g,&g.enemies[0],1,0);enemy_step(&g,0);
 assert(g.enemies[0].state==MF_ENEMY_DYING && !g.ricky_jump[0].active && g.stage_kills==1);
 g.enemies[0].state=MF_ENEMY_ABSENT;enemy_spawn(&g,0,0);assert(!g.ricky_jump[0].cooldown && !g.ricky_jump[0].active);
 /* In overlapping ranges choose an alternative; speed remains 240 fixed point. */
 setup(&g,0,1,0);g.players[0].x=g.enemies[0].x+32*256;enemy_step(&g,0);assert(g.ricky_punch[0]);
 g.enemies[0].state=MF_ENEMY_IDLE;enemy_step(&g,0);assert(!g.ricky_punch[0]);
 g.enemies[0].state=MF_ENEMY_IDLE;enemy_step(&g,0);assert(g.ricky_punch[0]);
 puts("PASS jump-chain P1/P2/both facings/checkpoints, 12/24/5/18 timing, visible reach, 1HP single-hit latches, lane/height/invulnerability/facing misses, captured trajectory, counterplay, flame/release/death/reset, cooldown and variety");
}
