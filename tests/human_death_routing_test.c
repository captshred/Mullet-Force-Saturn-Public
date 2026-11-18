/* Exercise the actual collision dispatcher, including its per-target hit mask. */
#include <assert.h>
#include <stdio.h>
#include "../src/game.c"
static void setup(mf_game *g,int actor,int kind,int lethal){int i;mf_player *p;mf_enemy *e;mf_game_init(g);g->started=1;
 for(i=0;i<MF_ENEMIES;i++){g->enemies[i].hp=0;g->enemies[i].state=MF_ENEMY_ABSENT;}
 for(i=0;i<MF_DRUMS;i++)g->drums[i].hp=0;
 p=&g->players[actor];p->active=1;p->health=100;p->hurt=0;p->x=200*256;p->y=200*256;p->height=kind==1?20*256:0;p->attack_air=kind==1;p->attack=6;p->bat=0;p->hit_mask=0;p->facing=1;g->combo[actor].phase=kind==2?2:0;
 e=&g->enemies[0];e->hp=lethal?1:6;e->state=MF_ENEMY_IDLE;e->x=230*256;e->y=p->y;g->events=0;}
int main(void){mf_game g;int actor,kind,lethal;
 for(actor=0;actor<2;actor++)for(kind=0;kind<3;kind++)for(lethal=0;lethal<2;lethal++){
  setup(&g,actor,kind,lethal);player_hits(&g,&g.players[actor]);
  assert(!!(g.events&MF_COMBAT_HUMAN_DEATH(actor))==lethal);
  assert(!!(g.events&MF_COMBAT_HEAVY_HIT(actor))==(!lethal && kind!=0));
  assert(!!(g.events&MF_COMBAT_CONNECT(actor))==lethal);
  assert(!!(g.events&MF_COMBAT_NONKILL(actor))==!lethal);
  assert(g.enemies[0].hp==(lethal?0:(kind==1?4:5)));
  g.events=0;player_hits(&g,&g.players[actor]);assert(!g.events);
  setup(&g,actor,kind,lethal);g.enemies[0].x=600*256;player_hits(&g,&g.players[actor]);assert(!g.events);
 }
 setup(&g,0,2,0);g.enemies[0].hp=0;g.drums[0].hp=1;g.drums[0].x=230*256;g.drums[0].y=200*256;player_hits(&g,&g.players[0]);assert(g.events&MF_WORLD_IMPACT);assert(!(g.events&(MF_COMBAT_HEAVY_HIT(0)|MF_COMBAT_HUMAN_DEATH(0))));
 for(actor=0;actor<2;actor++)for(kind=0;kind<3;kind++){
  setup(&g,actor,kind,0);g.enemies[0].hp=0;g.drums[0].hp=3;g.drums[0].x=230*256;g.drums[0].y=200*256;player_hits(&g,&g.players[actor]);assert(g.drums[0].hp==2);assert(!!(g.events&MF_COMBAT_HEAVY_HIT(actor))==(kind!=0));assert(!(g.events&MF_COMBAT_HUMAN_DEATH(actor)));g.events=0;player_hits(&g,&g.players[actor]);assert(!g.events);
 }
 setup(&g,0,0,1);fire_damage(&g,&g.enemies[0],1,0);assert(g.events&MF_COMBAT_HUMAN_DEATH(0));
 g.events=0;hit_sound(&g,0,0,0);assert(g.events&MF_COMBAT_CONNECT(0));assert(!(g.events&MF_COMBAT_HUMAN_DEATH(0)));
 puts("PASS actual dispatcher: both players, jab/cross/kick, lethal precedence, misses, duplicate masks, inorganic destruction, fire death and separate player death");return 0;}
