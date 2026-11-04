/* Exercise authoritative damage resolvers directly at collision boundaries. */
#include <assert.h>
#include <stdio.h>
#include "../src/game.c"
static void setup(mf_game *g,int p){int i;mf_game_init(g);g->started=1;
 for(i=0;i<2;i++){g->players[i].active=1;g->players[i].health=100;g->players[i].invulnerable=0;g->players[i].x=(200+100*i)*256;g->players[i].y=200*256;g->enemies[i].hp=0;g->enemies[i].state=MF_ENEMY_ABSENT;}
 for(i=0;i<3;i++)g->drums[i].hp=0;
 g->players[p].facing=1;g->events=0;
}
int main(void){mf_game g;int p,lethal,bat;
 for(p=0;p<2;p++)for(lethal=0;lethal<2;lethal++)for(bat=0;bat<2;bat++){
  mf_player *a;mf_enemy *e;int hp;
  setup(&g,p);a=&g.players[p];e=&g.enemies[0];a->attack=bat?MF_BAT_ACTIVE_FIRST:6;a->bat=bat;
  e->hp=lethal?1:6;e->state=MF_ENEMY_IDLE;e->x=a->x+30*256;e->y=a->y;
  player_hits(&g,a);hp=e->hp;assert(hp==(lethal?0:6-(bat?MF_BAT_DAMAGE:1)));
  assert(g.events&(lethal?MF_COMBAT_CONNECT(p):MF_COMBAT_NONKILL(p)));
  assert(!(g.events&(lethal?MF_COMBAT_NONKILL(p):MF_COMBAT_CONNECT(p))));assert(!(g.events&MF_WORLD_IMPACT));
  g.events=0;player_hits(&g,a);assert(!g.events && e->hp==hp);
 }
 for(p=0;p<2;p++)for(lethal=0;lethal<2;lethal++){
  mf_player *a;mf_enemy *e;setup(&g,p);a=&g.players[p];e=&g.enemies[0];
  a->health=lethal?MF_ENEMY_DAMAGE:100;e->hp=6;e->state=MF_ENEMY_ACTIVE;e->timer=5;e->facing=1;e->x=a->x-30*256;e->y=a->y;e->target=p;e->target_lock=120;
  enemy_step(&g,0);assert(a->health==(lethal?0:100-MF_ENEMY_DAMAGE));assert(g.events&MF_COMBAT_HURT(p));
  assert(g.events&(lethal?MF_COMBAT_CONNECT(p):MF_COMBAT_NONKILL(p)));assert(!(g.events&MF_WORLD_IMPACT));
  g.events=0;enemy_step(&g,0);assert(!g.events);
 }
 for(p=0;p<2;p++){
  setup(&g,p);g.players[p].attack=6;player_hits(&g,&g.players[p]);assert(!g.events);
  g.drums[0].hp=1;g.drums[0].x=g.players[p].x+30*256;g.drums[0].y=g.players[p].y;
  player_hits(&g,&g.players[p]);assert(!g.drums[0].hp && (g.events&MF_COMBAT_DESTROY(p)) && !(g.events&MF_COMBAT_CONNECT(p)));
  g.events=0;player_hits(&g,&g.players[p]);assert(!g.events);
 }
 puts("PASS SFX2: Buck/Chuck lethal/nonlethal punches/bats, enemy lethal/nonlethal hits to both, destruction once, misses, collision deduplication");return 0;
}
