#include <assert.h>
#include <stdio.h>
#include "game.h"
static void step(mf_game *g,int n) {while(n--)mf_game_step(g,0,0);}
static void start(mf_game *g) {
    int i;mf_game_init(g);mf_game_step(g,0,MF_START); g->enemies[1].state=MF_ENEMY_ABSENT;g->enemies[1].hp=0;g->enemies[1].timer=100000;
    for(i=0;i<3;i++){g->drums[i].hp=0;g->drums[i].respawn=-100000;}
}
static void close_enemy(mf_game *g) {
    g->players[0].x=200*256;g->players[0].y=200*256;g->players[0].facing=1;
    g->enemies[0].x=244*256;g->enemies[0].y=200*256;g->enemies[0].facing=-1;
    g->enemies[0].state=MF_ENEMY_IDLE;g->enemies[0].timer=0;g->enemies[0].grace=1000;g->enemies[0].vx=0;
}
int main(void)
{
    mf_game g;int i,x,y,hp,score;
    start(&g);x=g.enemies[0].x;y=g.enemies[0].y;step(&g,80);
    assert(g.enemies[0].x<x && g.enemies[0].y>y && g.players[0].health==100);
    puts("PASS single enemy approaches both axes with initial grace");
    start(&g);close_enemy(&g);g.enemies[0].grace=0;
    mf_game_step(&g,0,0);assert(g.enemies[0].state==MF_ENEMY_WINDUP);
    step(&g,MF_PUNK_WINDUP_TICKS-1);assert(g.players[0].health==100);
    mf_game_step(&g,0,0);assert(g.players[0].health==100-MF_ENEMY_DAMAGE && g.hitstop==MF_HIT_STOP_TICKS);
    hp=g.players[0].health;step(&g,20);assert(g.players[0].health==hp && g.players[0].invulnerable>0);
    puts("PASS telegraph, punch, single-hit latch, invulnerability and recovery");
    start(&g);close_enemy(&g);g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=6;
    g.players[0].y=225*256;step(&g,5);assert(g.players[0].health==100);
    close_enemy(&g);g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=6;g.players[0].x=g.enemies[0].x+44*256;
    step(&g,5);assert(g.players[0].health==100);
    close_enemy(&g);g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=6;g.players[0].height=63*256;
    mf_game_step(&g,0,0);assert(g.players[0].health==100);
    puts("PASS enemy misses wrong depth, behind-facing targets and elevated hurtbox");
    start(&g);close_enemy(&g);mf_game_step(&g,0,MF_A);step(&g,35);
    assert(g.enemies[0].hp==MF_ENEMY_MAX_HP-1 && g.enemies[0].x>244*256);
    hp=g.enemies[0].hp;step(&g,30);assert(g.enemies[0].hp==hp);
    start(&g);close_enemy(&g);g.players[0].y=225*256;mf_game_step(&g,0,MF_A);step(&g,35);
    assert(g.enemies[0].hp==MF_ENEMY_MAX_HP);
    start(&g);close_enemy(&g);g.players[0].facing=-1;mf_game_step(&g,0,MF_A);step(&g,35);
    assert(g.enemies[0].hp==MF_ENEMY_MAX_HP);
    start(&g);close_enemy(&g);g.enemies[0].x=266*256;g.enemies[0].state=MF_ENEMY_RECOVER;g.enemies[0].timer=1000;mf_game_step(&g,0,MF_A);step(&g,35);
    assert(g.enemies[0].hp==MF_ENEMY_MAX_HP);
    puts("PASS Buck attack/hurtbox overlap, one hit per swing, recoil and lane/facing/range rejection");
    start(&g);close_enemy(&g);mf_game_step(&g,0,MF_B);mf_game_step(&g,0,MF_A);step(&g,10);
    assert(g.enemies[0].hp==MF_ENEMY_MAX_HP-2 && g.players[0].y==200*256 && g.players[0].height>0);
    puts("PASS jump-kick damages enemy without changing ground depth");
    start(&g);close_enemy(&g);g.players[0].attack=6;g.players[0].attack_air=0;
    mf_game_step(&g,0,0);assert(g.hitstop==MF_HIT_STOP_TICKS && !g.paused);
    x=g.ticks;y=g.players[0].x;step(&g,MF_HIT_STOP_TICKS);assert(g.ticks==x && g.players[0].x==y && !g.paused);
    puts("PASS restrained hit-stop freezes gameplay without requesting music pause");
    start(&g);
    for(i=0;i<MF_ENEMY_MAX_HP;i++) {
        close_enemy(&g);g.players[0].attack=0;mf_game_step(&g,0,MF_A);step(&g,30);
    }
    assert(g.enemies[0].hp==0 && g.score==MF_ENEMY_DEFEAT_SCORE);
    score=g.score;
    while(g.enemies[0].state!=MF_ENEMY_ABSENT)mf_game_step(&g,0,0);
    assert(g.enemies[0].timer==MF_ENEMY_RESPAWN_TICKS);
    step(&g,MF_ENEMY_RESPAWN_TICKS-1);assert(g.enemies[0].state==MF_ENEMY_ABSENT && g.score==score);
    mf_game_step(&g,0,0);assert(g.enemies[0].hp==MF_ENEMY_MAX_HP && g.enemies[0].grace==MF_ENEMY_SPAWN_GRACE);
    assert(g.enemies[0].x>g.players[0].x+200*256 && g.enemies[0].x/256>g.camera+320);
    puts("PASS one defeat score, removal, configurable eight-second respawn offscreen with grace");
    start(&g);close_enemy(&g);g.players[0].health=MF_ENEMY_DAMAGE;g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=6;
    mf_game_step(&g,0,0);assert(!g.players[0].health && g.players[0].defeated==MF_BUCK_RECOVERY_TICKS);
    step(&g,MF_HIT_STOP_TICKS+MF_BUCK_RECOVERY_TICKS);
    assert(g.players[0].health==100 && g.players[0].x==100*256 && g.players[0].invulnerable>0);
    puts("PASS Buck defeat auto-recovers without an immediate enemy attack");
    return 0;
}
