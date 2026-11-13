#include <assert.h>
#include <stdio.h>
#include "game.c"
static void setup(mf_game *g,int player) {
 int i;mf_game_init(g);g->started=1;g->spawn_wait=100000;
 for(i=0;i<3;i++)g->drums[i].hp=0;
 for(i=0;i<2;i++){g->enemies[i].state=MF_ENEMY_ABSENT;g->players[i].active=0;}
 g->players[player]=(mf_player){.active=1,.health=100,.x=240*256,.y=200*256,.facing=-1};
 g->enemies[0]=(mf_enemy){.x=180*256,.y=200*256,.hp=6,.facing=1,.state=MF_ENEMY_IDLE,.target=-1};
 g->enemy_class[0]=MF_ENEMY_RICKY;
}
int main(void) {
 mf_game g;int p,i,j,hp,x,y,count[3]={0};
 for(p=0;p<2;p++) {
  setup(&g,p);ricky_step(&g,0);assert(g.enemies[0].state==MF_ENEMY_WINDUP && !g.ricky_punch[0]);
  for(i=0;i<21;i++){ricky_step(&g,0);assert(g.players[p].health==100);}
  ricky_step(&g,0);assert(g.players[p].health==88);
  g.players[p].invulnerable=0;
  for(i=0;i<3;i++)ricky_step(&g,0);
  assert(g.players[p].health==88 && g.enemies[0].state==MF_ENEMY_RECOVER);
  for(i=0;i<23;i++){ricky_step(&g,0);assert(g.players[p].health==88);}
  /* Miss wrong lane / airborne / behind. */
  for(j=0;j<3;j++) {
   setup(&g,p);g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=4;
   if(j==0)g.players[p].y=229*256;
   if(j==1)g.players[p].height=100*256;
   if(j==2)g.players[p].x=130*256;
   ricky_step(&g,0);assert(g.players[p].health==100);
  }
  /* Punch, airborne kick, bat, and approved running bat all hit Ricky. */
  for(j=0;j<6;j++) {
   setup(&g,p);g.players[p].x=215*256;g.players[p].attack=8;
   g.players[p].attack_air=j==1;g.players[p].bat=j>=2?MF_BAT_RUNNING:0;
   if(j==1)g.players[p].height=12*256;
   if(j>=2)g.players[p].attack=MF_FAST_BAT_ACTIVE_FIRST;
   if(j>=4){g.players[p].bat=1;g.players[p].attack=MF_BAT_ACTIVE_FIRST;}
   if(j==5){g.players[p].attack_air=1;g.players[p].height=12*256;}
   if(j==3)g.running_bat[p].active=1;
   hp=g.enemies[0].hp;player_hits(&g,&g.players[p]);
   assert(g.enemies[0].hp<hp);
   if(j==3)assert(!g.enemies[0].hp && g.stage_kills==1);
  }
  setup(&g,p);g.enemies[0].state=MF_ENEMY_WINDUP;g.enemies[0].timer=22;
  g.players[p].x=215*256;g.players[p].attack=8;player_hits(&g,&g.players[p]);
  assert(g.enemies[0].state==MF_ENEMY_HURT);enemy_step(&g,0);assert(g.players[p].health==100);
  setup(&g,p);fire_damage(&g,&g.enemies[0],1,p);assert(g.enemies[0].burn && g.enemies[0].hp<6);
 }
 /* Both existing slots may attack; shared player invulnerability prevents stacking. */
 setup(&g,0);g.enemies[1]=g.enemies[0];g.enemy_class[1]=MF_ENEMY_RICKY;
 for(i=0;i<2;i++){g.enemies[i].state=MF_ENEMY_ACTIVE;g.enemies[i].timer=4;}
 enemy_step(&g,0);enemy_step(&g,1);assert(g.players[0].health==88);
 setup(&g,0);g.enemies[1]=g.enemies[0];g.enemy_class[1]=MF_ENEMY_CORPORATE_PUNK;
 g.enemies[1].x=215*256;
 for(i=0;i<2;i++){g.enemies[i].state=MF_ENEMY_ACTIVE;g.enemies[i].timer=4;}
 enemy_step(&g,0);enemy_step(&g,1);assert(g.players[0].health==88);
 setup(&g,0);g.players[0].x=400*256;g.players[0].y=229*256;
 x=g.enemies[0].x;y=g.enemies[0].y;ricky_step(&g,0);assert(g.enemies[0].x>x && g.enemies[0].y>y);
 setup(&g,0);g.players[0].x=g.enemies[0].x;ricky_step(&g,0);assert(g.enemies[0].x!=g.players[0].x);
 setup(&g,0);g.enemies[0].x=210*256;ricky_step(&g,0);assert(g.ricky_punch[0] && g.enemies[0].timer==12);
 setup(&g,0);for(i=0;i<40;i++) {
  g.enemies[0].hp=1;g.enemies[0].state=MF_ENEMY_IDLE;fire_damage(&g,&g.enemies[0],1,0);
  assert(g.stage_kills==i+1);fire_damage(&g,&g.enemies[0],1,0);assert(g.stage_kills==i+1);
 }
 assert(g.stage==MF_STAGE_SETTLING);for(i=0;i<200;i++)stage_transition_step(&g);assert(g.stage==MF_STAGE_LEVEL2_ENTRY);
 setup(&g,0);g.enemies[0].state=MF_ENEMY_ABSENT;
 for(i=0;i<16;i++) {enemy_spawn(&g,0,0);assert(g.enemies[0].state!=MF_ENEMY_ABSENT);count[g.enemy_class[0]]++;g.enemies[0].state=MF_ENEMY_ABSENT;}
 assert(count[MF_ENEMY_CORPORATE_PUNK]==10 && count[MF_ENEMY_RICKY]==6);
 puts("PASS Ricky chain/punch, P1/P2, lane/height/facing misses, single-hit, interrupt, all player attacks, flame, diagonal/axis pursuit, 40 KOs, class schedule");
 return 0;
}
