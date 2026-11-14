#include <assert.h>
#include <stdio.h>
#include "game.c"
static void tick(mf_game *g,unsigned a,unsigned b,unsigned connected) {
 unsigned h[2]={a,b},p[2]={0,0};mf_game_step_inputs(g,h,p,connected);
}
int main(void) {
 assert(MF_WORLD_WIDTH==1920 && MF_WORLD_RIGHT==1894 && MF_WORLD_CAMERA_MAX==1600);
 int marks[]={0,320,640,960,1280};
 for(unsigned i=0;i<sizeof marks/sizeof marks[0];i++)assert(mf_world_checkpoint(marks[i])==marks[i]);
 assert(mf_world_checkpoint(1599)==1280 && mf_world_checkpoint(1600)==1280);
 for(int coop=0;coop<2;coop++) {
  mf_game g;mf_game_init(&g);g.started=1;
  if(coop)recover_player(&g,1,1);
  int max_count=0,seen_classes=0,retired=0;
  for(int t=0;t<2400;t++) {
   int camera=g.camera,floor=g.camera_floor;
   for(int p=0;p<2;p++)g.players[p].invulnerable=100;
   int states[MF_ENEMIES];for(int j=0;j<MF_ENEMIES;j++)states[j]=g.enemies[j].state;
   tick(&g,MF_RIGHT,coop?MF_RIGHT:0,coop?3:1);
   assert(g.stage==MF_STAGE_LEVEL1 && g.camera>=camera && g.camera-camera<=2 && g.camera_floor>=floor);
   int count=mf_enemy_count(&g);assert(count<=mf_enemy_limit(&g));if(count>max_count)max_count=count;
   for(int p=0;p<coop+1;p++)assert(g.players[p].x>=(g.camera+26)*256 && g.players[p].x<=(g.camera+294)*256);
   for(int j=0;j<MF_ENEMIES;j++) {
    mf_enemy *e=&g.enemies[j];
    if(states[j]!=MF_ENEMY_ABSENT && e->state==MF_ENEMY_ABSENT)++retired;
    if(e->state!=MF_ENEMY_ABSENT) {
     seen_classes|=1<<g.enemy_class[j];
     assert(e->x>=MF_ENEMY_WORLD_LEFT*256 && e->x<=MF_ENEMY_WORLD_RIGHT*256);
     if(states[j]==MF_ENEMY_ABSENT)assert(e->x/256<g.camera || e->x/256>g.camera+320);
    }
   }
   assert(g.score==0 && g.stage_kills==0); /* Retirement is never a KO. */
  }
  assert(g.camera==1600 && g.camera_floor==1280 && g.players[0].x==1894*256);
  assert(max_count==(coop?3:2) && g.ricky_spawns>(unsigned)max_count && (seen_classes&1));
  for(int t=0;t<1000;t++) {
   int camera=g.camera;for(int p=0;p<2;p++)g.players[p].invulnerable=100;
   tick(&g,MF_LEFT,coop?MF_LEFT:0,coop?3:1);
   assert(g.camera>=1280 && camera-g.camera<=2 && g.stage==MF_STAGE_LEVEL1);
  }
  assert(g.camera==1280 && g.players[0].x==1306*256);
  if(coop) {
   tick(&g,0,0,1);assert(!g.players[1].active && mf_enemy_limit(&g)==2);
   unsigned h[2]={0,MF_START},p[2]={0,MF_START};mf_game_step_inputs(&g,h,p,3);
   assert(g.players[1].active && g.players[1].x>=g.camera*256 && g.players[1].x<=(g.camera+320)*256);
  }
  printf("PASS %s 1920px traversal, endpoint1600/checkpoint1280 backstop, smooth camera/tether, offscreen spawns, max%d, class schedule intact, retirement/no KO, join/leave\n",coop?"coop":"solo",max_count);
 }
}
