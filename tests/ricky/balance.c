#include <assert.h>
#include <stdio.h>
#include "game.c"
static void setup(mf_game *g,int cls,int player) {
 mf_game_init(g);g->started=1;g->spawn_wait=100000;
 for(int i=0;i<MF_DRUMS;i++)g->drums[i].hp=0;
 for(int i=0;i<MF_PLAYERS;i++)g->players[i].active=0;
 for(int i=0;i<MF_ENEMIES;i++)g->enemies[i].state=MF_ENEMY_ABSENT;
 g->players[player]=(mf_player){.active=1,.health=100,.x=240*256,.y=200*256,.facing=-1};
 g->enemies[0]=(mf_enemy){.hp=6,.x=205*256,.y=200*256,.facing=1,.state=MF_ENEMY_IDLE,.target=player};
 g->enemy_class[0]=cls;
}
int main(void) {
 mf_game g;int cls,p,mode,state,i,hp;
 for(cls=MF_ENEMY_CORPORATE_PUNK;cls<=MF_ENEMY_RICKY;cls++)for(p=0;p<2;p++) {
  /* Jabs and aerial kicks retain their damage. */
  for(mode=0;mode<2;mode++) {
   setup(&g,cls,p);g.players[p].attack=8;
   if(mode){g.players[p].attack_air=1;g.players[p].height=12*256;}
   player_hits(&g,&g.players[p]);assert(g.enemies[0].hp==6-(mode?2:1));
  }
  /* Existing per-swing mask rejects adjacent collisions, resets next swing. */
  for(mode=0;mode<3;mode++) {
   setup(&g,cls,p);mf_player *a=&g.players[p];
   a->bat=mode?1:MF_BAT_RUNNING;a->attack=mode?MF_BAT_ACTIVE_FIRST:MF_FAST_BAT_ACTIVE_FIRST;
   g.running_bat[p].active=mode==0;
   if(mode==2){a->attack_air=1;a->height=12*256;}
   player_hits(&g,a);assert(g.enemies[0].hp==3 && g.enemies[0].state==MF_ENEMY_HURT);
   for(i=0;i<10;i++)player_hits(&g,a);
   assert(g.enemies[0].hp==3 && !g.stage_kills);
   a->hit_mask=0;player_hits(&g,a);
   assert(!g.enemies[0].hp && g.enemies[0].state==MF_ENEMY_DYING && g.stage_kills==(cls!=MF_ENEMY_SPECIAL));
   player_hits(&g,a);assert(g.stage_kills==(cls!=MF_ENEMY_SPECIAL));
  }
  for(state=MF_ENEMY_IDLE;state<=MF_ENEMY_RECOVER;state++) {
   setup(&g,cls,p);mf_player *a=&g.players[p];mf_enemy *e=&g.enemies[0];
   e->state=state;e->timer=1;g.ricky_punch[0]=1;
   /* Charge and a flame missing the lane must not stun. */
   a->charge=MF_TORCH_CHARGE_TICKS-1;enemy_step(&g,0);assert(e->state!=MF_ENEMY_IDLE || state==MF_ENEMY_RECOVER);
   setup(&g,cls,p);a=&g.players[p];e=&g.enemies[0];e->state=state;e->timer=1;g.ricky_punch[0]=1;
   a->torch=MF_TORCH_FIRE;a->torch_tick=5;
   hp=e->hp;torch_hits(&g,a);assert(e->hp==hp);enemy_step(&g,0);
   assert(e->state==MF_ENEMY_IDLE && !e->timer && a->health==100 && !g.ricky_punch[0]);
   for(i=0;i<20;i++){enemy_step(&g,0);assert(e->state==MF_ENEMY_IDLE && a->health==100);}
   /* Release immediately restores attack eligibility, even with residual burn. */
   e->burn=20;e->burn_clock=20;a->torch=MF_TORCH_AWAY;
   enemy_step(&g,0);assert(e->state==MF_ENEMY_WINDUP && e->timer>1);
  }
  setup(&g,cls,p);g.players[p].torch=MF_TORCH_FIRE;g.players[p].y=229*256;
  g.enemies[0].state=MF_ENEMY_WINDUP;g.enemies[0].timer=5;
  enemy_step(&g,0);assert(g.enemies[0].timer==4);
  /* Full update ordering: contact wins over an already-active enemy,
     release permits a fresh windup immediately, and recontact cancels it. */
  setup(&g,cls,p);g.players[p].torch=MF_TORCH_FIRE;
  g.players[p].torch_tick=8;g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=1;
  {
   unsigned held[2]={0},pressed[2]={0};held[p]=MF_A;
   mf_game_step_inputs(&g,held,pressed,3);
   assert(g.players[p].health==100 && g.enemies[0].hp==6 && g.enemies[0].state==MF_ENEMY_IDLE);
   held[p]=0;mf_game_step_inputs(&g,held,pressed,3);
   assert(g.enemies[0].state==MF_ENEMY_WINDUP && g.enemies[0].timer>1);
   g.players[p].torch=MF_TORCH_FIRE;held[p]=MF_A;
   mf_game_step_inputs(&g,held,pressed,3);assert(g.enemies[0].state==MF_ENEMY_IDLE);
   for(i=0;i<300 && g.enemies[0].hp;i++){
    mf_game_step_inputs(&g,held,pressed,3);assert(g.players[p].health==100);
   }
   assert(!g.enemies[0].hp && g.enemies[0].state==MF_ENEMY_DYING && g.stage_kills==(cls!=MF_ENEMY_SPECIAL));
  }
  /* Co-op contact is shared: releasing one flame cannot release the stun
     while the other player still contacts either enemy slot. */
  setup(&g,cls,p);g.players[1-p]=g.players[p];
  g.players[0].torch=g.players[1].torch=MF_TORCH_FIRE;
  g.enemies[1]=g.enemies[0];g.enemy_class[1]=cls;
  for(i=0;i<2;i++){g.enemies[i].state=MF_ENEMY_ACTIVE;g.enemies[i].timer=1;enemy_step(&g,i);assert(g.enemies[i].state==MF_ENEMY_IDLE);}
  g.players[p].torch=MF_TORCH_AWAY;
  for(i=0;i<2;i++){enemy_step(&g,i);assert(g.enemies[i].state==MF_ENEMY_IDLE);}
  g.players[1-p].torch=MF_TORCH_AWAY;
  for(i=0;i<2;i++){enemy_step(&g,i);assert(g.enemies[i].state==MF_ENEMY_WINDUP);}
  /* An exact charge threshold starts fire; no new windup or stun at charge. */
  setup(&g,cls,p);g.players[p].a_blocked=0;g.players[p].charge=MF_TORCH_CHARGE_TICKS-2;
  torch_input(&g.players[p],MF_A,0,1);assert(!g.players[p].torch);
  torch_input(&g.players[p],MF_A,0,1);assert(g.players[p].torch==MF_TORCH_FIRE);
  /* Actual damage cadence is unchanged; continuous contact can still kill. */
  setup(&g,cls,p);g.players[p].torch=MF_TORCH_FIRE;
  torch_hits(&g,&g.players[p]);hp=g.enemies[0].hp;assert(hp==6-MF_TORCH_DAMAGE);
  for(i=1;i<MF_TORCH_DAMAGE_TICKS;i++){torch_hits(&g,&g.players[p]);assert(g.enemies[0].hp==hp);}
  torch_hits(&g,&g.players[p]);assert(g.enemies[0].hp==hp-MF_TORCH_DAMAGE);
  g.enemies[0].hp=1;g.players[p].torch_tick=0;torch_hits(&g,&g.players[p]);
  assert(g.enemies[0].state==MF_ENEMY_DYING && g.stage_kills==(cls!=MF_ENEMY_SPECIAL) && !g.enemies[0].burn);
  for(i=0;i<30;i++)enemy_step(&g,0);
  assert(g.enemies[0].state==MF_ENEMY_ABSENT && g.stage_kills==(cls!=MF_ENEMY_SPECIAL));
 }
 puts("PASS bat 3HP/single hit/two-hit KO; flame contact interrupt/release/cadence/death; all classes, both slots and players");
}
