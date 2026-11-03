#include <assert.h>
#include <stdio.h>
#include "game.h"
static void tick(mf_game *g,unsigned h0,unsigned h1,unsigned p0,unsigned p1)
{
    unsigned h[2]={h0,h1},p[2]={p0,p1};mf_game_step_coop(g,h,p);
}
static void wait(mf_game *g,int n){while(n--)tick(g,0,0,0,0);}
static void isolate(mf_game *g)
{
    int i;mf_game_init(g);tick(g,0,0,MF_START,MF_START);
    for(i=0;i<MF_ENEMIES;i++){g->enemies[i].state=MF_ENEMY_ABSENT;g->enemies[i].hp=0;g->enemies[i].timer=100000;}
    for(i=0;i<MF_DRUMS;i++){g->drums[i].hp=0;g->drums[i].respawn=-100000;}
    g->players[0].invulnerable=g->players[1].invulnerable=0;
}
static void place_players(mf_game *g)
{
    g->players[0].x=g->players[1].x=200*256;
    g->players[0].y=g->players[1].y=200*256;
    g->players[0].facing=g->players[1].facing=1;
}
static void enemy(mf_game *g,int index,int x,int y)
{
    mf_enemy *e=&g->enemies[index];*e=(mf_enemy){0};e->x=x*256;e->y=y*256;
    e->hp=MF_ENEMY_MAX_HP;e->state=MF_ENEMY_IDLE;e->grace=1000;e->target=-1;e->facing=-1;
}
int main(void)
{
    mf_game g;int i,j,x,hp,score;
    mf_game_init(&g);tick(&g,0,MF_RIGHT,0,MF_START);
    assert(g.started && g.players[1].active && !g.paused);
    mf_game_init(&g);
    tick(&g,0,0,MF_START,0);assert(g.started && !g.players[1].active);
    x=g.players[0].x;wait(&g,10);assert(g.players[0].x==x);
    tick(&g,0,0,0,MF_START);assert(g.players[1].active && !g.paused);
    tick(&g,0,0,0,MF_START);assert(!g.paused);
    tick(&g,0,0,MF_START,0);assert(g.paused);
    x=g.players[1].x;tick(&g,0,MF_RIGHT,0,MF_START);assert(g.paused && g.players[1].x==x);
    tick(&g,0,0,MF_START,0);assert(!g.paused);
    puts("PASS P2 joins from title or gameplay, never toggles pause; P1 owns pause; absent pad is optional");

    for(i=0;i<2;i++) {
        mf_game_init(&g);g.started=1;g.paused=1;g.score=555;
        g.players[0].x=(i?614:26)*256;g.players[0].y=(i?229:168)*256;g.camera=i?320:0;
        x=g.players[0].x;g.drums[0].hp=1;g.enemies[0].hp=3;
        tick(&g,0,0,0,MF_START);
        assert(g.players[1].active && g.paused && g.score==555 && g.players[0].x==x);
        assert(g.players[1].x/256>=g.camera+32 && g.players[1].x/256<=g.camera+288);
        assert(g.players[1].y>=168*256 && g.players[1].y<=229*256 && g.players[1].invulnerable==120);
        assert(g.drums[0].hp==1 && g.enemies[0].hp==3);
    }
    puts("PASS protected visible joining at both stage edges, including paused game, without scene reset");

    isolate(&g);place_players(&g);tick(&g,MF_LEFT,MF_RIGHT,MF_A,MF_B);
    assert(g.players[0].attack && !g.players[0].height && !g.players[1].attack && g.players[1].height);
    assert(g.players[0].x<200*256 && g.players[1].x>200*256);
    assert(g.players[0].y==200*256 && g.players[1].y==200*256);
    tick(&g,0,0,0,MF_A);assert(g.players[1].attack_air && !g.players[0].attack_air);
    assert((g.events&MF_SWOOSH)!=0);
    for(i=0;i<80;i++)tick(&g,MF_RIGHT,MF_LEFT,0,0);
    assert(g.players[0].x>g.players[1].x && g.players[0].health==100 && g.players[1].health==100);
    for(i=0;i<600;i++)tick(&g,MF_LEFT,MF_RIGHT,0,0);
    assert(g.players[1].x-g.players[0].x<=260*256);
    assert(g.players[0].x/256>=g.camera+20 && g.players[1].x/256<=g.camera+300);
    puts("PASS independent moves/attacks/jumps, no friendly fire, players pass each other, camera tether");

    isolate(&g);place_players(&g);enemy(&g,0,244,200);enemy(&g,1,244,200);
    tick(&g,0,0,MF_A,MF_A);wait(&g,9);
    assert(g.enemies[0].hp==MF_ENEMY_MAX_HP-2 && g.enemies[1].hp==MF_ENEMY_MAX_HP-2);
    assert((g.players[0].hit_mask&24)==24 && (g.players[1].hit_mask&24)==24);
    hp=g.enemies[0].hp;wait(&g,30);assert(g.enemies[0].hp==hp);
    isolate(&g);place_players(&g);enemy(&g,0,244,200);g.enemies[0].hp=1;
    tick(&g,0,0,MF_A,MF_A);wait(&g,30);
    assert(g.score==MF_ENEMY_DEFEAT_SCORE);
    puts("PASS both players hit both enemies once per swing; shared killing blow awards score once");

    isolate(&g);place_players(&g);enemy(&g,0,244,200);enemy(&g,1,244,200);
    g.enemies[0].state=g.enemies[1].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=g.enemies[1].timer=6;
    tick(&g,0,0,0,0);
    assert(g.players[0].health==100-MF_ENEMY_DAMAGE && g.players[1].health==100-MF_ENEMY_DAMAGE);
    assert(g.enemies[0].hit_done==3 && g.enemies[1].hit_done==0);
    wait(&g,20);assert(g.players[0].health==100-MF_ENEMY_DAMAGE);
    assert(g.events==0 || g.events==MF_SWOOSH);
    puts("PASS enemy per-player hit mask, shared invulnerability prevents synchronized double damage");

    isolate(&g);g.players[0].x=180*256;g.players[1].x=340*256;
    g.players[0].y=g.players[1].y=200*256;
    enemy(&g,0,200,200);enemy(&g,1,320,200);
    tick(&g,0,0,0,0);assert(g.enemies[0].target==0 && g.enemies[1].target==1);
    g.players[0].x=330*256;g.players[1].x=210*256;
    wait(&g,30);assert(g.enemies[0].target==0 && g.enemies[1].target==1);
    g.players[0].health=0;g.players[0].defeated=120;
    tick(&g,0,0,0,0);assert(g.enemies[0].target==1);
    puts("PASS sensible nearby targets, stable locks, retarget on player defeat");

    isolate(&g);place_players(&g);g.players[1].active=0;
    enemy(&g,0,244,200);enemy(&g,1,244,200);g.enemies[0].grace=g.enemies[1].grace=0;
    tick(&g,0,0,0,0);
    assert(g.enemies[0].state==MF_ENEMY_WINDUP && g.enemies[1].state==MF_ENEMY_RECOVER);
    assert(g.enemies[0].target==0 && g.enemies[1].target==0);
    puts("PASS two enemies target Buck in single-player, shared-target telegraphs stagger");

    isolate(&g);place_players(&g);g.players[1].health=0;g.players[1].defeated=1;
    g.players[0].health=61;g.players[0].attack=12;g.players[0].height=8*256;g.players[0].vz=100;
    x=g.players[0].x;enemy(&g,0,510,200);g.enemies[0].hp=3;
    tick(&g,0,0,0,0);
    assert(g.players[1].health==100 && g.players[1].invulnerable==120);
    assert(g.players[0].health==61 && g.players[0].attack==13 && g.players[0].x==x);
    assert(g.enemies[0].hp==3 && g.enemies[0].grace!=MF_ENEMY_SPAWN_GRACE);
    g.players[0].health=0;g.players[0].defeated=1;g.players[1].attack=12;g.players[1].health=73;
    tick(&g,0,0,0,0);assert(g.players[0].health==100 && g.players[1].health==73 && g.players[1].attack==13);
    puts("PASS each player recovers without resetting survivor or enemies");

    isolate(&g);place_players(&g);enemy(&g,0,244,200);enemy(&g,1,244,200);
    g.enemies[0].hp=1;g.enemies[1].hp=2;
    tick(&g,0,0,MF_A,MF_A);wait(&g,40);
    assert(g.score==2*MF_ENEMY_DEFEAT_SCORE);
    assert(g.enemies[0].state==MF_ENEMY_ABSENT && g.enemies[1].state==MF_ENEMY_ABSENT);
    g.enemies[0].timer=1;g.enemies[1].timer=200;score=g.score;
    tick(&g,0,0,0,0);
    assert(g.enemies[0].hp==MF_ENEMY_MAX_HP && g.enemies[0].grace>=120 && g.enemies[0].x/256>g.camera+320);
    assert(g.enemies[1].state==MF_ENEMY_ABSENT && g.enemies[1].timer==199 && g.score==score);
    puts("PASS independent enemy removals, respawn timers, far/offscreen spawn and exactly-once score");

    mf_game_init(&g);tick(&g,0,0,MF_START,MF_START);
    for(i=0;i<20000;i++){
        unsigned a=(i/90)%2?MF_LEFT:MF_RIGHT,b=(i/120)%2?MF_LEFT:MF_RIGHT;
        if(i%64<32)a|=MF_UP;else a|=MF_DOWN;
        if(i%80<40)b|=MF_UP;else b|=MF_DOWN;
        tick(&g,a,b,(i%28==0?MF_A:0)|(i%137==0?MF_B:0),(i%29==0?MF_A:0)|(i%139==0?MF_B:0));
        assert(g.events>=0 && (g.events&~4095)==0 && g.camera>=0 && g.camera<=320);
        for(j=0;j<2;j++){
            assert(g.players[j].health>=0 && g.players[j].health<=100);
            assert(g.players[j].x>=26*256 && g.players[j].x<=614*256 && g.players[j].height>=0);
            assert(g.players[j].y>=168*256 && g.players[j].y<=229*256);
            assert(g.enemies[j].hp>=0 && g.enemies[j].hp<=MF_ENEMY_MAX_HP);
        }
    }
    puts("PASS 20000 simultaneous co-op combat ticks: actor bounds, health, event coalescing and camera invariants");
    return 0;
}
