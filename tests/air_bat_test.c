#include <assert.h>
#include <stdio.h>
#include "game.h"
static void tick(mf_game *g,unsigned h0,unsigned h1,unsigned p0,unsigned p1)
{
    unsigned h[2]={h0,h1},p[2]={p0,p1};mf_game_step_coop(g,h,p);
}
static void wait(mf_game *g,int n){while(n--)tick(g,0,0,0,0);}
static void input(mf_game *g,int player,unsigned held,unsigned pressed)
{
    tick(g,player?0:held,player?held:0,player?0:pressed,player?pressed:0);
}
static void init(mf_game *g,int facing)
{
    int i;mf_game_init(g);tick(g,0,0,MF_START,MF_START);
    for(i=0;i<2;i++){
        g->players[i].x=200*256;g->players[i].y=200*256;g->players[i].facing=facing;g->players[i].invulnerable=0;
        g->enemies[i].state=MF_ENEMY_ABSENT;g->enemies[i].hp=0;g->enemies[i].timer=100000;
    }
    for(i=0;i<3;i++){g->drums[i].hp=0;g->drums[i].respawn=-100000;}
}
static unsigned dir(const mf_game *g,int p){return g->players[p].facing>0?MF_RIGHT:MF_LEFT;}
static void taps(mf_game *g,int p,int distance,int attack)
{
    unsigned d=dir(g,p);int i;input(g,p,d,d);
    for(i=1;i<distance;i++)tick(g,0,0,0,0);
    input(g,p,d|(attack?MF_A:0),d|(attack?MF_A:0));
}
static void enemy(mf_game *g,int i,int x,int y)
{
    mf_enemy *e=&g->enemies[i];*e=(mf_enemy){0};e->x=x*256;e->y=y*256;e->hp=MF_ENEMY_MAX_HP;
    e->state=MF_ENEMY_RECOVER;e->timer=10000;e->grace=10000;e->target=-1;
}
int main(void)
{
    mf_game g,ref;int p,f,i,x,y,hp,mask,first,attempt;
    for(p=0;p<2;p++)for(f=-1;f<=1;f+=2){
        init(&g,f);input(&g,p,MF_B,MF_B);taps(&g,p,2,1);
        assert(g.players[p].bat && g.players[p].attack_air && g.players[p].air_bat_used && g.players[p].height>0);
        assert(!g.players[1-p].bat && !g.players[1-p].height);
        ref=g;ref.players[p].bat=ref.players[p].attack=ref.players[p].attack_air=0;
        x=g.players[p].x;y=g.players[p].y;mask=0;
        while(g.players[p].height){
            unsigned h=dir(&g,p)|MF_UP;
            if(g.players[p].bat)mask|=1<<mf_bat_frame(&g.players[p]);
            input(&g,p,h,0);input(&ref,p,h,0);
            assert(g.players[p].height==ref.players[p].height && g.players[p].vz==ref.players[p].vz);
            assert(g.players[p].x==ref.players[p].x && g.players[p].y==ref.players[p].y);
        }
        assert(mask==127 && (g.players[p].x-x)*f>0 && g.players[p].y<y);
        wait(&g,50);assert(!g.players[p].attack && !g.players[p].bat && !g.players[p].height);
    }
    puts("PASS both players/facings: fresh aerial bat priority, all seven poses, unchanged gravity and both-axis air steering");

    for(attempt=0;attempt<2;attempt++){
        init(&g,1);input(&g,0,MF_RIGHT,MF_RIGHT);wait(&g,1);
        if(attempt){input(&g,0,MF_RIGHT,MF_RIGHT);assert(g.players[0].bat_window);}
        input(&g,0,MF_B,MF_B);assert(!g.players[0].tap_window && !g.players[0].bat_window);
        input(&g,0,MF_RIGHT|MF_A,MF_RIGHT|MF_A);
        assert(g.players[0].attack_air && !g.players[0].bat);
    }
    init(&g,1);input(&g,0,MF_B|MF_RIGHT,MF_B|MF_RIGHT);wait(&g,1);
    input(&g,0,MF_RIGHT|MF_A,MF_RIGHT|MF_A);assert(!g.players[0].bat);
    puts("PASS takeoff discards one/two grounded taps and simultaneous jump+direction; missing fresh combo gives kick");

    init(&g,1);input(&g,0,MF_B,MF_B);taps(&g,0,MF_BAT_TAP_TICKS,1);assert(g.players[0].bat && g.players[0].attack_air);
    init(&g,1);input(&g,0,MF_B,MF_B);taps(&g,0,MF_BAT_TAP_TICKS+1,1);assert(!g.players[0].bat && g.players[0].attack_air);
    init(&g,1);input(&g,0,MF_B,MF_B);taps(&g,0,2,0);wait(&g,MF_BAT_ATTACK_TICKS-1);
    input(&g,0,MF_A,MF_A);assert(g.players[0].bat && g.players[0].attack_air);
    init(&g,1);input(&g,0,MF_B,MF_B);taps(&g,0,2,0);wait(&g,MF_BAT_ATTACK_TICKS);
    input(&g,0,MF_A,MF_A);assert(!g.players[0].bat && g.players[0].attack_air);
    init(&g,1);input(&g,0,MF_B,MF_B);input(&g,0,MF_RIGHT,MF_RIGHT);
    for(i=0;i<6;i++)input(&g,0,MF_RIGHT,MF_RIGHT);
    input(&g,0,MF_RIGHT|MF_A,MF_A);assert(!g.players[0].bat);
    puts("PASS airborne gesture timing boundaries and held-direction rejection match grounded rules");

    init(&g,1);input(&g,0,MF_B,MF_B);taps(&g,0,2,1);
    /* Prolong the test flight to exercise a second complete gesture after recovery. */
    g.players[0].height=200*256;g.players[0].vz=900;
    while(g.players[0].attack)tick(&g,0,0,0,0);
    assert(g.players[0].height>0 && g.players[0].air_bat_used);
    taps(&g,0,2,1);assert(!g.players[0].bat && g.players[0].attack_air);
    wait(&g,120);input(&g,0,MF_B,MF_B);assert(!g.players[0].air_bat_used);
    taps(&g,0,2,1);assert(g.players[0].bat && g.players[0].air_bat_used);
    puts("PASS one aerial bat per jump, ordinary kick fallback after use, new jump re-arms bat");

    for(p=0;p<2;p++)for(f=-1;f<=1;f+=2){
        init(&g,f);input(&g,p,MF_B,MF_B);taps(&g,p,2,1);
        x=g.players[p].x/256;y=g.players[p].y/256;
        enemy(&g,0,x+f*80,y);enemy(&g,1,x+f*82,y);
        while(g.players[p].attack<MF_BAT_ACTIVE_FIRST){tick(&g,0,0,0,0);assert(g.enemies[0].hp==6);}
        tick(&g,0,0,0,0);assert(g.enemies[0].hp==4 && g.enemies[1].hp==4);
        assert(g.spark_z>=60 && g.spark_z<=84 && g.players[1-p].health==100);
        hp=g.enemies[0].hp;wait(&g,90);assert(g.enemies[0].hp==hp);
    }
    init(&g,1);g.players[0].height=200*256;g.players[0].bat=1;g.players[0].attack_air=1;
    g.players[0].attack=MF_BAT_ACTIVE_FIRST;enemy(&g,0,240,200);
    tick(&g,0,0,0,0);assert(g.enemies[0].hp==6 && !g.spark);
    init(&g,1);g.players[0].height=40*256;g.players[0].bat=1;g.players[0].attack_air=1;
    g.players[0].attack=MF_BAT_ACTIVE_FIRST;enemy(&g,0,240,225);enemy(&g,1,160,200);
    tick(&g,0,0,0,0);assert(g.enemies[0].hp==6 && g.enemies[1].hp==6);
    puts("PASS active-only standing-enemy overlaps, sensible vertical/depth/facing rejection, multiple targets once, head-height sparks");

    init(&g,1);enemy(&g,0,240,200);enemy(&g,1,245,200);
    g.players[0].height=1000;g.players[0].vz=-1200;g.players[0].bat=1;g.players[0].attack_air=1;
    g.players[0].air_bat_used=1;g.players[0].attack=MF_BAT_ACTIVE_FIRST;g.players[0].hit_mask=8;
    tick(&g,0,0,0,0);
    assert(!g.players[0].height && !g.players[0].vz && !g.players[0].attack_air);
    assert(g.players[0].attack==MF_BAT_LAND_RECOVERY_START+1 && g.players[0].hit_mask==8);
    assert(g.enemies[0].hp==6 && g.enemies[1].hp==6 && !(g.events&MF_SWOOSH));
    wait(&g,15);assert(!g.players[0].attack && !g.players[0].bat && g.enemies[1].hp==6);
    puts("PASS landing during active attack enters non-damaging brief recovery without resetting hit mask or replaying sound");

    init(&g,1);tick(&g,MF_B,MF_B,MF_B,MF_B);tick(&g,MF_RIGHT,MF_RIGHT,MF_RIGHT,MF_RIGHT);
    wait(&g,1);tick(&g,MF_RIGHT|MF_A,MF_RIGHT|MF_A,MF_RIGHT|MF_A,MF_RIGHT|MF_A);
    x=g.players[0].x/256;enemy(&g,0,x+70,200);enemy(&g,1,x+74,200);
    g.enemies[0].hp=3;g.enemies[1].hp=3;first=0;
    for(i=0;i<80;i++){tick(&g,0,0,0,0);if(g.events&MF_SWOOSH)++first;}
    assert(g.score==2*MF_ENEMY_DEFEAT_SCORE && !g.enemies[0].hp && !g.enemies[1].hp);
    assert((g.players[0].hit_mask&24)==24 && (g.players[1].hit_mask&24)==24);
    assert(g.players[0].health==100 && g.players[1].health==100 && first==1);
    puts("PASS simultaneous two-player aerial bats: independent masks, coalesced swing SFX, no friendly fire or duplicate score");
    return 0;
}
