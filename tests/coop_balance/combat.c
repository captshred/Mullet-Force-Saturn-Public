#include <assert.h>
#include <stdio.h>
#include "game.c"
static void step(mf_game *g,unsigned a,unsigned b,unsigned connected) {
 unsigned h[2]={a,b},p[2]={a,b};mf_game_step_inputs(g,h,p,connected);
}
static void setup(mf_game *g) {
 mf_game_init(g);g->started=1;g->spawn_wait=100000;
 for(int i=0;i<MF_DRUMS;i++)g->drums[i].hp=0;
 for(int i=0;i<MF_ENEMIES;i++)g->enemies[i].state=MF_ENEMY_ABSENT;
 for(int i=0;i<MF_PLAYERS;i++)g->players[i]=(mf_player){.active=1,.health=100,.x=(100+i*60)*256,.y=200*256,.facing=1};
}
int main(void) {
 mf_game g;
 /* Every jab/cross tick, both actors, standing/moving, hit/miss, queued A. */
 for(int who=0;who<2;who++)for(int phase=0;phase<3;phase++)for(int tick=1;tick<=(phase==2?MF_CROSS_TOTAL_TICKS:24);tick++)for(int hit=0;hit<2;hit++) {
  setup(&g);mf_player *p=&g.players[who];p->attack=tick;p->hit_mask=hit?(1<<MF_DRUMS):0;
  g.combo[who].phase=phase;g.jab[who].buffer=8;p->buffered=MF_A;
  int hp=hit?5:6;g.enemies[0]=(mf_enemy){.state=MF_ENEMY_IDLE,.hp=hp,.x=p->x+28*256,.y=p->y,.target=-1,.grace=100};
  unsigned h[2]={0,0},e[2]={0,0};h[who]=MF_B|MF_RIGHT;e[who]=MF_B;
  mf_game_step_inputs(&g,h,e,3);
  assert(p->height==1510 && p->vz==1436 && !p->attack && !p->hit_mask && !p->attack_air);
  assert(!g.jab[who].buffer && !p->buffered && !g.combo[who].timeout);
  assert(g.enemies[0].hp==hp && p->x>(100+who*60)*256);
  int peak=0,landed=0;for(int n=0;n<60;n++) {
   h[who]=MF_B;e[who]=0;g.enemies[0].grace=100;mf_game_step_inputs(&g,h,e,3);
   if(p->height>peak)peak=p->height;if(n>40 && !p->height)landed=1;
   assert(!p->attack && g.enemies[0].hp==hp);
  }
  assert(landed && peak>15000 && !p->height); /* Held B never retriggers. */
 }
 /* Actual hit then fresh jump in hit-stop: retain existing global freeze,
    consume B on its first simulation tick, never deal another punch hit. */
 setup(&g);g.players[0].attack=6;g.enemies[0]=(mf_enemy){.state=MF_ENEMY_IDLE,.hp=6,.x=128*256,.y=200*256,.target=-1,.grace=100};
 step(&g,0,0,3);assert(g.enemies[0].hp==5 && g.hitstop);
 step(&g,MF_B,0,3);assert(g.players[0].buffered&MF_B);
 while(g.hitstop)step(&g,0,0,3);step(&g,0,0,3);
 assert(g.players[0].height && !g.players[0].attack && g.enemies[0].hp==5);
 for(int state=0;state<4;state++) {
  setup(&g);mf_player *p=&g.players[0];p->attack=5;
  if(state==0)p->hurt=8;if(state==1)p->health=0;
  if(state==2)p->bat=1;if(state==3)p->torch=MF_TORCH_FIRE;
  step(&g,state==3?(MF_A|MF_B):MF_B,0,3);assert(!p->height && !p->vz);
 }
 /* All three punch latch bits are independent; cancel ends the shared window. */
 for(int who=0;who<2;who++) {
  setup(&g);mf_player *p=&g.players[who];p->attack=6;
  for(int j=0;j<MF_ENEMIES;j++)g.enemies[j]=(mf_enemy){.state=MF_ENEMY_IDLE,.hp=6,.x=p->x+28*256,.y=p->y,.target=-1};
  player_hits(&g,p);assert(p->hit_mask==(7<<MF_DRUMS));
  for(int j=0;j<MF_ENEMIES;j++)assert(g.enemies[j].hp==5);
  player_hits(&g,p);player_step(&g,who,MF_B,MF_B);player_hits(&g,p);
  for(int j=0;j<MF_ENEMIES;j++)assert(g.enemies[j].hp==5);
 }
 /* Each slot, either class, can land damage and latch it exactly once. */
 for(int j=0;j<MF_ENEMIES;j++)for(int kind=0;kind<2;kind++) {
  setup(&g);mf_enemy *e=&g.enemies[j];
  *e=(mf_enemy){.state=MF_ENEMY_ACTIVE,.hp=6,.x=130*256,.y=200*256,.facing=-1,.target=0,.timer=4};
  g.enemy_class[j]=kind?MF_ENEMY_RICKY:MF_ENEMY_CORPORATE_PUNK;
  enemy_step(&g,j);assert(g.players[0].health<100 && e->hit_done==1);
  int hp=g.players[0].health;g.players[0].invulnerable=0;enemy_step(&g,j);assert(g.players[0].health==hp);
 }
 /* Population, schedule, class mix, join and leave at all world boundaries. */
 for(int camera=0;camera<=960;camera+=320) {
  setup(&g);g.camera=camera;g.camera_floor=mf_world_checkpoint(camera);
  g.players[0].x=(camera+140)*256;g.players[1].x=(camera+190)*256;
  g.players[1].active=0;g.spawn_wait=0;int mix=0,maxsolo=0,maxcoop=0;
  for(int n=0;n<30;n++) {
   g.spawn_wait=0;stage_spawns(&g);assert(mf_enemy_count(&g)<=2);
   if(mf_enemy_count(&g)>maxsolo)maxsolo=mf_enemy_count(&g);
  }
  step(&g,0,MF_START,3);assert(g.players[1].active);
  for(int n=0;n<30;n++){g.spawn_wait=0;stage_spawns(&g);assert(mf_enemy_count(&g)<=3);if(mf_enemy_count(&g)>maxcoop)maxcoop=mf_enemy_count(&g);}
  assert(maxsolo==2 && maxcoop==3);
  int score=g.score,kills=g.stage_kills;
  step(&g,0,0,1);assert(!g.players[1].active && mf_enemy_limit(&g)==2 && mf_enemy_count(&g)==3);
  g.spawn_wait=0;stage_spawns(&g);assert(mf_enemy_count(&g)==3 && g.score==score && g.stage_kills==kills);
  /* One retiring actor leaves two: still no replacement. */
  g.enemies[2].state=MF_ENEMY_DYING;g.enemies[2].timer=1;enemy_step(&g,2);
  stage_spawns(&g);assert(mf_enemy_count(&g)==2);
  g.enemies[1].state=MF_ENEMY_ABSENT;g.spawn_wait=0;stage_spawns(&g);assert(mf_enemy_count(&g)==2);
  for(int round=0;round<16;round++) {
   for(int j=0;j<MF_ENEMIES;j++)g.enemies[j].state=MF_ENEMY_ABSENT;
   g.players[1].active=1;
   for(int n=0;n<300 && mf_enemy_count(&g)<3;n++) {
    g.spawn_wait=0;stage_spawns(&g);
    for(int j=0;j<MF_ENEMIES;j++){g.players[0].invulnerable=g.players[1].invulnerable=100;enemy_step(&g,j);}
   }
   assert(mf_enemy_count(&g)==3);
   for(int j=0;j<MF_ENEMIES;j++) {
    mf_enemy *e=&g.enemies[j];mix|=1<<g.enemy_class[j];
    e->x=g.players[0].x+100*256;e->y=g.players[0].y;e->grace=0;e->target=-1;
    for(int n=0;n<180;n++){g.players[0].invulnerable=100;enemy_step(&g,j);}
    assert(e->state!=MF_ENEMY_ABSENT);
    e->state=MF_ENEMY_IDLE;e->hp=1;fire_damage(&g,e,1,0);
    assert(e->state==MF_ENEMY_DYING);e->timer=1;enemy_step(&g,j);assert(e->state==MF_ENEMY_ABSENT);
   }
  }
  assert((mix&(1<<MF_ENEMY_RICKY)) && (mix&1));
  printf("PASS camera %d: solo max %d, coop max %d, join/leave, all slots CP/Ricky fight/KO/retire\n",camera,maxsolo,maxcoop);
 }
 printf("PASS jump cancel: all startup/active/recovery ticks, both actors, moving, hit/miss, held B, buffered A, hit-stop, special/hurt/death guards; mf_game %zu bytes\n",sizeof(g));
}
