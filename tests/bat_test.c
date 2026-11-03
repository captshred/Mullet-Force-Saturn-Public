#include <assert.h>
#include <stdio.h>
#include "game.h"
static void tick(mf_game *g,unsigned h0,unsigned h1,unsigned p0,unsigned p1)
{
    unsigned h[2]={h0,h1},p[2]={p0,p1};mf_game_step_coop(g,h,p);
}
static void wait(mf_game *g,int n){while(n--)tick(g,0,0,0,0);}
static void init(mf_game *g,int facing)
{
    int i;mf_game_init(g);tick(g,0,0,MF_START,MF_START);
    for(i=0;i<2;i++){
        g->players[i].x=200*256;g->players[i].y=200*256;g->players[i].facing=facing;g->players[i].invulnerable=0;
        g->enemies[i].state=MF_ENEMY_ABSENT;g->enemies[i].hp=0;g->enemies[i].timer=100000;
    }
    for(i=0;i<3;i++){g->drums[i].hp=0;g->drums[i].respawn=-100000;}
}
static void input(mf_game *g,int player,unsigned held,unsigned pressed)
{
    tick(g,player?0:held,player?held:0,player?0:pressed,player?pressed:0);
}
static unsigned forward(mf_game *g,int p){return g->players[p].facing>0?MF_RIGHT:MF_LEFT;}
static void taps(mf_game *g,int p,int distance,int attack)
{
    unsigned d=forward(g,p);int i;input(g,p,d,d);
    for(i=1;i<distance;i++)tick(g,0,0,0,0);
    input(g,p,d|(attack?MF_A:0),d|(attack?MF_A:0));
}
static void enemy(mf_game *g,int index,int x,int y)
{
    mf_enemy *e=&g->enemies[index];*e=(mf_enemy){0};e->x=x*256;e->y=y*256;e->hp=MF_ENEMY_MAX_HP;
    e->state=MF_ENEMY_RECOVER;e->timer=10000;e->grace=10000;e->target=-1;
}
int main(void)
{
    mf_game g;int p,f,i,x,y,hp,mask,score;
    for(p=0;p<2;p++)for(f=-1;f<=1;f+=2){
        init(&g,f);taps(&g,p,5,1);
        assert(g.players[p].bat && g.players[p].attack && !g.players[p].attack_air);
        assert(!g.players[1-p].attack && !g.players[p].bat_window && !g.players[p].tap_window);
        x=g.players[p].x;y=g.players[p].y;mask=0;
        while(g.players[p].attack){
            mask|=1<<mf_bat_frame(&g.players[p]);input(&g,p,MF_A|MF_RIGHT|MF_DOWN,0);
            assert(g.players[p].x==x && g.players[p].y==y && g.players[p].facing==f);
        }
        assert(mask==127 && !g.players[p].bat);wait(&g,40);assert(!g.players[p].attack);
    }
    puts("PASS both players/facings: bat priority, consumed gesture, seven poses, planted stance and finite recovery");

    init(&g,1);taps(&g,0,MF_BAT_TAP_TICKS,1);assert(g.players[0].bat);
    init(&g,1);taps(&g,0,MF_BAT_TAP_TICKS+1,1);assert(!g.players[0].bat && g.players[0].attack);
    init(&g,1);taps(&g,0,4,0);wait(&g,MF_BAT_ATTACK_TICKS-2);input(&g,0,MF_A,MF_A);assert(g.players[0].bat);
    init(&g,1);taps(&g,0,4,0);wait(&g,MF_BAT_ATTACK_TICKS-1);input(&g,0,MF_A,MF_A);assert(g.players[0].bat);
    init(&g,1);taps(&g,0,4,0);wait(&g,MF_BAT_ATTACK_TICKS);input(&g,0,MF_A,MF_A);assert(!g.players[0].bat);
    puts("PASS inclusive 250ms tap / ~183ms A windows and expiration, including simultaneous second tap+A");

    init(&g,1);input(&g,0,MF_RIGHT,MF_RIGHT);
    for(i=0;i<40;i++)input(&g,0,MF_RIGHT,MF_RIGHT); /* reject repeated edges while held */
    input(&g,0,MF_RIGHT|MF_A,MF_A);assert(!g.players[0].bat);
    init(&g,1);input(&g,0,MF_RIGHT,MF_RIGHT);wait(&g,1);input(&g,0,MF_LEFT,MF_LEFT);wait(&g,1);
    input(&g,0,MF_LEFT|MF_A,MF_LEFT|MF_A);assert(!g.players[0].bat);
    init(&g,1);input(&g,0,MF_RIGHT|MF_LEFT,MF_RIGHT|MF_LEFT);wait(&g,1);
    input(&g,0,MF_RIGHT|MF_A,MF_RIGHT|MF_A);assert(!g.players[0].bat);
    init(&g,1);taps(&g,0,4,0);input(&g,0,MF_B,MF_B);input(&g,0,MF_A,MF_A);
    assert(g.players[0].attack_air && !g.players[0].bat && g.players[0].height>0);
    puts("PASS held forward, opposite/ambiguous taps rejected; airborne A remains jump kick");

    init(&g,1);tick(&g,MF_RIGHT,MF_RIGHT,MF_RIGHT,MF_RIGHT);wait(&g,1);
    tick(&g,MF_RIGHT|MF_A,MF_A,MF_RIGHT|MF_A,MF_A);
    assert(g.players[0].bat && g.players[1].attack && !g.players[1].bat);
    init(&g,1);input(&g,0,MF_RIGHT,MF_RIGHT);wait(&g,1);g.hitstop=3;
    input(&g,0,MF_RIGHT|MF_A,MF_RIGHT|MF_A);assert(!g.players[0].attack && g.players[0].bat_window);
    wait(&g,3);assert(g.players[0].bat && !g.paused);
    puts("PASS independent gesture histories and second tap+A buffering during restrained hit-stop");

    for(p=0;p<2;p++)for(f=-1;f<=1;f+=2){
        init(&g,f);taps(&g,p,4,1);x=g.players[p].x/256;y=g.players[p].y/256;
        enemy(&g,0,x+f*82,y);enemy(&g,1,x+f*84,y);
        for(i=0;i<3;i++){
            g.drums[i].hp=3;g.drums[i].x=(x+f*(66+i*4))*256;g.drums[i].y=y*256;g.drums[i].respawn=0;
        }
        while(g.players[p].attack<MF_BAT_ACTIVE_FIRST){
            tick(&g,0,0,0,0);assert(g.enemies[0].hp==MF_ENEMY_MAX_HP && g.drums[0].hp==3);
        }
        tick(&g,0,0,0,0);
        assert(g.enemies[0].hp==MF_ENEMY_MAX_HP-2 && g.enemies[1].hp==MF_ENEMY_MAX_HP-2);
        assert(g.drums[0].hp==1 && g.drums[1].hp==1 && g.drums[2].hp==1);
        assert(g.enemies[0].vx*f>850 && g.drums[0].vx*f==MF_BAT_KNOCKBACK);
        assert(g.players[p].hit_mask==31 && g.players[1-p].health==100);
        hp=g.enemies[0].hp;score=g.score;wait(&g,70);
        assert(g.enemies[0].hp==hp && g.score==score && !g.players[p].attack);
    }
    puts("PASS active-only 2x damage, longer mirrored reach, stronger knockback; five targets once per swing, no friendly fire");

    init(&g,1);taps(&g,0,3,1);x=g.players[0].x/256;
    enemy(&g,0,x+40,225);enemy(&g,1,x-40,200);wait(&g,50);
    assert(g.enemies[0].hp==MF_ENEMY_MAX_HP && g.enemies[1].hp==MF_ENEMY_MAX_HP);
    init(&g,1);enemy(&g,0,240,200);g.enemies[0].hp=6;g.players[0].bat=1;g.players[0].attack=MF_BAT_ACTIVE_LAST+1;
    wait(&g,5);assert(g.enemies[0].hp==6);
    init(&g,1);input(&g,0,MF_A,MF_A);assert(!g.players[0].bat && !g.players[0].attack_air);
    puts("PASS bat misses wrong depth/behind and recovery-only contact; ordinary A remains punch");

    init(&g,1);tick(&g,MF_RIGHT,MF_RIGHT,MF_RIGHT,MF_RIGHT);wait(&g,1);
    tick(&g,MF_RIGHT|MF_A,MF_RIGHT|MF_A,MF_RIGHT|MF_A,MF_RIGHT|MF_A);
    x=g.players[0].x/256;enemy(&g,0,x+70,200);g.enemies[0].hp=3;
    wait(&g,30);assert(!g.enemies[0].hp && g.score==MF_ENEMY_DEFEAT_SCORE);
    assert((g.players[0].hit_mask&8) && (g.players[1].hit_mask&8));
    puts("PASS simultaneous player bat attacks share an enemy safely and award one defeat score");
    return 0;
}
