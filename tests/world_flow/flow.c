#include <assert.h>
#include <stdio.h>
#include "game.c"
static void setup(mf_game *g,int camera,int coop) {
 mf_game_init(g);g->started=1;g->camera=camera;g->camera_floor=mf_world_checkpoint(camera);g->spawn_wait=1000000;
 g->players[0].x=(camera+142)*256;g->players[0].invulnerable=0;
 if(coop){g->players[1]=g->players[0];g->players[1].x+=40*256;}
 for(int i=0;i<3;i++)g->drums[i].hp=0;
}
static void tick(mf_game *g,unsigned h0,unsigned h1) {unsigned held[2]={h0,h1},pressed[2]={0};mf_game_step_inputs(g,held,pressed,3);}
int main(void) {
 mf_game g;int i,p,old,score,count[3]={0};
 setup(&g,0,0);
 for(i=0;i<75;i++){
  g.enemies[0]=(mf_enemy){.hp=1,.state=MF_ENEMY_IDLE};g.enemy_class[0]=i%2?MF_ENEMY_RICKY:MF_ENEMY_CORPORATE_PUNK;
  fire_damage(&g,&g.enemies[0],1,0);assert(g.stage==MF_STAGE_LEVEL1 && g.stage_kills==i+1);
 }
 assert(g.score==75*MF_ENEMY_DEFEAT_SCORE);
 /* No enemies: traverse all bounds, floor advancement and backwards clamp. */
 setup(&g,0,0);old=0;
 for(i=0;i<1600;i++) {tick(&g,MF_RIGHT,0);assert(g.camera>=old && g.camera-old<=2);old=g.camera;assert(g.players[0].x/256>=g.camera+26 && g.players[0].x/256<=g.camera+294);}
 assert(g.camera==960 && g.camera_floor==640 && g.players[0].x==1254*256 && g.stage==MF_STAGE_LEVEL1);
 for(i=0;i<900;i++){old=g.camera;tick(&g,MF_LEFT,0);assert(abs_i(g.camera-old)<=2 && g.camera>=640);}
 assert(g.camera==640 && g.players[0].x==666*256);
 /* One stationary partner blocks the leader without shifting the partner. */
 for(p=0;p<2;p++){
  setup(&g,320,1);int still=g.players[1-p].x;
  for(i=0;i<400;i++){tick(&g,p?0:MF_RIGHT,p?MF_RIGHT:0);assert(g.players[1-p].x==still);assert(abs_i(g.players[0].x-g.players[1].x)<=240*256);}
  int floor=g.camera_floor;
  for(i=0;i<700;i++){old=g.camera;tick(&g,MF_RIGHT,MF_RIGHT);assert(abs_i(g.camera-old)<=2);for(int j=0;j<2;j++)assert(g.players[j].x/256>=g.camera+26 && g.players[j].x/256<=g.camera+294);}
  assert(g.camera>floor && g.players[1-p].x>still);
 }
 /* Entry at multiple checkpoints and endpoint always starts offscreen. */
 for(int camera=0;camera<=960;camera+=160) {
  setup(&g,camera,0);g.players[0].x=(camera+160)*256;
  for(i=0;i<16;i++){
   g.enemies[0].state=MF_ENEMY_ABSENT;enemy_spawn(&g,0,0);mf_enemy *e=&g.enemies[0];assert(e->state!=MF_ENEMY_ABSENT);
   assert(e->x/256<=camera-96 || e->x/256>=camera+384);
   if(e->x/256<camera)assert(e->x/256>=g.camera_floor+26);
   count[g.enemy_class[0]]++;
  }
 }
 assert(count[0]==70 && count[2]==42);
 setup(&g,960,0);g.enemies[0].state=MF_ENEMY_ABSENT;enemy_spawn(&g,0,0);assert(g.enemies[0].x>1280*256);
 old=g.enemies[0].x;enemy_step(&g,0);assert(abs_i(g.enemies[0].x-old)<1024);
 for(i=0;i<220;i++){enemy_step(&g,0);if(g.enemies[0].state==MF_ENEMY_WINDUP || g.enemies[0].state==MF_ENEMY_ACTIVE)assert(g.enemies[0].x<=(960+301)*256);} /* No clamp warp into view. */
 setup(&g,800,0);score=g.score;g.enemies[0]=(mf_enemy){.state=MF_ENEMY_IDLE,.hp=6,.x=500*256};enemy_step(&g,0);
 assert(g.enemies[0].state==MF_ENEMY_ABSENT && g.stage_kills==0 && g.score==score);
 /* Co-op join/defeat recovery remains visible at the far end. */
 setup(&g,960,0);recover_player(&g,1,1);assert(g.players[1].x/256>=992 && g.players[1].x/256<=1248);
 /* Preserve the future settle/clear handoff, now entered only explicitly. */
 g.stage=MF_STAGE_SETTLING;g.stage_timer=MF_STAGE_SETTLE_TICKS;for(i=0;i<200;i++)stage_transition_step(&g);assert(g.stage==MF_STAGE_LEVEL2_ENTRY);
 puts("PASS world 1280/endpoint, 75 KOs, smooth checkpoint floors, no partner warp/catch-up, offscreen spawns/mix, retirement/no score, recovery and explicit stage handoff");
}
