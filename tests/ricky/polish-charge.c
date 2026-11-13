#include <assert.h>
#include <stdio.h>
#include "game.c"
static void setup(mf_game *g,int p,int cls) {
 mf_game_init(g);g->started=1;g->spawn_wait=100000;
 for(int i=0;i<MF_DRUMS;i++)g->drums[i].hp=0;
 for(int i=0;i<MF_ENEMIES;i++)g->enemies[i].state=MF_ENEMY_ABSENT;
 for(int i=0;i<MF_PLAYERS;i++)g->players[i].active=0;
 g->players[p]=(mf_player){.active=1,.health=100,.x=240*256,.y=200*256,.facing=-1};
 g->enemies[0]=(mf_enemy){.hp=6,.x=215*256,.y=200*256,.facing=1,.state=MF_ENEMY_ACTIVE,.timer=4,.target=p};
 g->enemy_class[0]=cls;
}
static void hit(mf_game *g,int p) {
 mf_player *a=&g->players[p];mf_enemy *e=&g->enemies[0];
 e->x=a->x+(a->torch==MF_TORCH_FIRE?25:-25)*256;e->facing=a->torch==MF_TORCH_FIRE?-1:1;e->y=a->y;e->state=MF_ENEMY_ACTIVE;e->timer=4;e->hit_done=0;
 a->invulnerable=0;g->hitstop=0;enemy_step(g,0);
}
int main(void) {
 mf_game g;const int when[]={20,45,59};int p,c,k,i,ignitions;
 for(p=0;p<2;p++)for(c=0;c<2;c++)for(k=0;k<3;k++) {
  int cls=c?MF_ENEMY_RICKY:MF_ENEMY_CORPORATE_PUNK;
  setup(&g,p,cls);mf_player *a=&g.players[p];a->charge=when[k];
  hit(&g,p);assert(a->charge==when[k] && a->health==100-MF_ENEMY_DAMAGE && a->hurt==12);
  assert(a->knockback==650 && a->invulnerable==MF_BUCK_INVULNERABLE_TICKS);
  ignitions=0;
  for(i=when[k];i<65;i++) {
   torch_input(a,MF_A,0,1);ignitions+=a->torch_sound!=0;
   if(i+1<60)assert(a->charge==i+1 && !a->torch);
   else assert(mf_torch_active(a) && !a->charge && a->hurt==12);
  }
  assert(ignitions==1 && !a->attack && !a->bat && !a->buffered);
  /* Fire newly ignited during hurt has a real collision volume and damage. */
  g.enemies[0].x=a->x-35*256;g.enemies[0].hp=6;
  assert(mf_torch_hits(a,mf_enemy_hurtbox(&g.enemies[0])));
  torch_hits(&g,a);assert(g.enemies[0].hp==6-MF_TORCH_DAMAGE);
  /* A later hit still interrupts deployed fire, including in a prior hurt. */
  hit(&g,p);assert(!a->torch && !a->charge && a->a_blocked);
  for(i=0;i<70;i++)torch_input(a,MF_A,0,1);
  assert(!a->torch && !a->charge && !a->torch_sound);
  setup(&g,p,cls);a=&g.players[p];a->charge=when[k];hit(&g,p);
  torch_input(a,0,0,1);assert(!a->torch && !a->charge && !a->torch_sound);
  for(i=0;i<70;i++)torch_input(a,0,0,1);
  assert(!a->torch && !a->charge && !a->attack);
 }
 for(p=0;p<2;p++) {
  setup(&g,p,MF_ENEMY_RICKY);mf_player *a=&g.players[p];a->charge=20;
  for(i=0;i<3;i++){hit(&g,p);assert(a->charge==20+i*10);for(k=0;k<10;k++)torch_input(a,MF_A,0,1);}
  assert(a->charge==50 && a->health==100-3*MF_ENEMY_DAMAGE);
  /* Full tick ordering: hit at 20, keep physical A down, no new punch/ignition. */
  setup(&g,p,MF_ENEMY_CORPORATE_PUNK);a=&g.players[p];a->charge=20;hit(&g,p);
  g.enemies[0].state=MF_ENEMY_ABSENT;g.hitstop=0;
  {unsigned held[2]={0},pressed[2]={0};held[p]=MF_A;ignitions=0;
   for(i=0;i<45;i++){mf_game_step_inputs(&g,held,pressed,3);ignitions+=(g.events&MF_TORCH_IGNITE)!=0;assert(!a->attack && !a->bat);}
   assert(ignitions==1 && a->torch==MF_TORCH_FIRE && !a->hurt);
  }
  setup(&g,p,MF_ENEMY_RICKY);a=&g.players[p];a->charge=59;a->health=MF_ENEMY_DAMAGE;
  hit(&g,p);assert(!a->health && !a->charge && !a->torch && a->defeated==MF_BUCK_RECOVERY_TICKS);
  for(k=0;k<5;k++) {
   setup(&g,p,MF_ENEMY_RICKY);a=&g.players[p];a->charge=59;hit(&g,p);
   unsigned held[2]={0},pressed[2]={0};held[p]=MF_A;
   if(k==0){a->health=0;torch_input(a,MF_A,0,1);}
   if(k==1)torch_input(a,MF_A,0,0);
   if(k==2){g.paused=1;mf_game_step_inputs(&g,held,pressed,3);}
   if(k==3){g.stage=MF_STAGE_SETTLING;g.stage_timer=1;g.hitstop=0;mf_game_step_inputs(&g,held,pressed,3);}
   if(k==4){a->height=256;torch_input(a,MF_A,0,1);}
   assert(!a->charge && !a->torch && !a->torch_sound);
  }
 }
 /* The same four-tick damage flash clock drives both enemy types. */
 for(c=0;c<2;c++) {
  setup(&g,0,c?MF_ENEMY_RICKY:MF_ENEMY_CORPORATE_PUNK);
  g.enemies[0].state=MF_ENEMY_IDLE;fire_damage(&g,&g.enemies[0],1,0);
  assert(g.enemies[0].fire_flash==4);
  for(i=3;i>=0;i--){enemy_step(&g,0);assert(g.enemies[0].fire_flash==i);}
 }
 /* Both ports progress independently; releasing P1 does not reset P2. */
 setup(&g,0,MF_ENEMY_RICKY);g.enemies[0].state=MF_ENEMY_ABSENT;
 g.players[1]=g.players[0];g.players[0].charge=20;g.players[1].charge=45;
 hit(&g,0);g.enemies[0].state=MF_ENEMY_ABSENT;g.hitstop=0;
 {unsigned held[2]={MF_A,MF_A},pressed[2]={0};for(i=0;i<15;i++)mf_game_step_inputs(&g,held,pressed,3);
  assert(g.players[0].charge==35 && g.players[1].torch==MF_TORCH_FIRE);
  held[0]=0;mf_game_step_inputs(&g,held,pressed,3);assert(!g.players[0].charge && g.players[1].torch==MF_TORCH_FIRE);
 }
 puts("PASS charge through hits at 20/45/59, threshold while hurt, visible-volume damage, release, repeated hits, independent ports, death/disconnect/pause/stage/air cancellation, single ignition and active-fire interruption");
}
