#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "wingsuit.h"
#define S 256
static const unsigned zero[2]={0,0};
static void tick(mf_wingsuit *g){mf_ws_step(g,zero,zero,3);}
static int count(const mf_ws_shot *s,int n){int i,c=0;for(i=0;i<n;i++)c+=!!s[i].active;return c;}
static int count_hostile(const mf_ws_hostile_shot *s,int n){int i,c=0;for(i=0;i<n;i++)c+=!!s[i].active;return c;}
int main(void)
{
    mf_wingsuit g;unsigned h[2]={0,0},p[2]={0,0};int i,x,y;
    mf_ws_init(&g,0);g.spawn=10000;assert(g.players[0].active && !g.players[1].active);
    x=g.players[0].x;y=g.players[0].y;h[0]=MF_UP|MF_RIGHT;
    mf_ws_step(&g,h,zero,1);assert(g.players[0].x-x==452 && y-g.players[0].y==452);
    assert(2*452*452<=640*640 && 2*452*452>638*638);
    h[0]=MF_UP|MF_LEFT;for(i=0;i<200;i++)mf_ws_step(&g,h,zero,1);
    assert(g.players[0].x==MF_WS_PLAYER_MIN && g.players[0].y==16*S);
    h[0]=MF_DOWN|MF_RIGHT;for(i=0;i<300;i++)mf_ws_step(&g,h,zero,1);
    assert(g.players[0].x==MF_WS_PLAYER_MAX && g.players[0].y==223*S);
    p[1]=MF_START;mf_ws_step(&g,zero,p,2);assert(g.players[1].active);p[1]=0;
    x=g.players[1].x;h[0]=MF_LEFT;h[1]=MF_RIGHT;mf_ws_step(&g,h,zero,3);
    assert(g.players[1].x==x+640);x=g.players[0].x;
    mf_ws_step(&g,h,zero,2);assert(g.players[0].x==x); /* disconnected port cannot steer */
    mf_ws_init(&g,1);h[0]=h[1]=MF_A;
    mf_ws_step(&g,h,zero,3);assert(count(g.shots,MF_WS_SHOTS)==2);
    assert(g.shots[0].owner==0 && g.shots[1].owner==1);
    for(i=0;i<MF_WS_SHOTS;i++)g.shots[i]=(mf_ws_shot){1,64*S,100*S,i&1,60,0};
    g.players[0].cooldown=g.players[1].cooldown=0;mf_ws_step(&g,h,zero,3);
    assert(count(g.shots,MF_WS_SHOTS)==MF_WS_SHOTS); /* exhausted pool drops fire safely */
    for(i=0;i<MF_WS_SHOTS;i++)g.shots[i].ttl=1;
    tick(&g);assert(count(g.shots,MF_WS_SHOTS)==0);
    for(i=0;i<MF_WS_HOSTILE;i++)g.hostile[i]=(mf_ws_hostile_shot){1,64*S,100*S,0,90,0,768};
    g.enemies[0]=(mf_ws_enemy){1,200*S,50*S,79,0,0,0,0,0,0};tick(&g);
    assert(count_hostile(g.hostile,MF_WS_HOSTILE)==MF_WS_HOSTILE);
    for(i=0;i<MF_WS_HOSTILE;i++){assert(g.hostile[i].x==64*S);g.hostile[i].ttl=1;}
    tick(&g);assert(count_hostile(g.hostile,MF_WS_HOSTILE)==0);
    mf_ws_init(&g,0);g.spawn=1;tick(&g);assert(g.enemies[0].active);
    g.enemies[0].y=257*S;tick(&g);assert(!g.enemies[0].active);
    for(i=0;i<MF_WS_ENEMIES;i++)g.enemies[i]=(mf_ws_enemy){1,70*S,0,0,0,0,0,0,0,0};
    g.spawn=1;tick(&g);for(i=0;i<MF_WS_ENEMIES;i++)assert(g.enemies[i].age==1);
    mf_ws_init(&g,1);g.enemies[0]=(mf_ws_enemy){1,130*S,100*S,0,0,0,0,0,0,0};
    g.shots[0]=(mf_ws_shot){1,130*S,106*S,1,60,0};g.shots[1]=g.shots[0];tick(&g);
    assert(g.players[1].score==100 && g.players[0].score==0 && g.enemies[0].explosion==12);
    for(i=0;i<12;i++)tick(&g);
    assert(!g.enemies[0].explosion);
    mf_ws_init(&g,0);g.players[0].invulnerable=0;
    g.hostile[0]=(mf_ws_hostile_shot){1,g.players[0].x,g.players[0].y-3*S,0,30,0,768};tick(&g);
    assert(g.players[0].lives==2 && g.players[0].respawn==60 && g.players[0].invulnerable==120);
    for(i=0;i<60;i++)tick(&g);
    assert(!g.players[0].respawn && g.players[0].invulnerable==120);
    g.enemies[0]=(mf_ws_enemy){1,g.players[0].x,g.players[0].y-320,0,0,0,0,0,0,0};tick(&g);assert(g.players[0].lives==2);
    g.players[0].invulnerable=0;g.players[0].lives=1;
    g.hostile[0]=(mf_ws_hostile_shot){1,g.players[0].x,g.players[0].y-3*S,0,30,0,768};tick(&g);assert(g.game_over);
    p[0]=MF_START;mf_ws_step(&g,zero,p,1);assert(!g.game_over && g.players[0].lives==3 && !g.players[1].active);
    x=g.ticks;mf_ws_step(&g,zero,p,1);assert(g.paused && (int)g.ticks==x);
    tick(&g);assert((int)g.ticks==x);mf_ws_step(&g,zero,p,1);assert(!g.paused && (int)g.ticks==x+1);
    mf_ws_init(&g,1);g.players[0].invulnerable=g.players[1].invulnerable=0;
    g.hostile[0]=(mf_ws_hostile_shot){1,g.players[1].x,g.players[1].y-3*S,0,30,0,768};tick(&g);
    assert(g.players[1].lives==2 && g.players[0].lives==3);
    g.players[0].lives=g.players[1].lives=0;tick(&g);assert(g.game_over);
    mf_ws_step(&g,zero,p,3);assert(!g.game_over && g.players[1].active && g.players[1].lives==3);
    /* Long deterministic stress: pooled objects remain bounded and expire. */
    mf_ws_init(&g,1);h[0]=MF_A;h[1]=MF_A;
    for(i=0;i<100000;i++){
        if(g.game_over)mf_ws_init(&g,1);
        h[0]=MF_A|((i&64)?MF_LEFT:MF_RIGHT);h[1]=MF_A|((i&64)?MF_UP:MF_DOWN);
        mf_ws_step(&g,h,zero,3);
        assert(g.players[0].x>=MF_WS_PLAYER_MIN && g.players[0].x<=MF_WS_PLAYER_MAX);
        assert(g.players[1].y>=16*S && g.players[1].y<=223*S);
    }
    printf("PASS wingsuit: movement/bounds, coop/disconnect, pools, scoring, spawns, damage, respawn, pause, restart, 100000-tick stress; state %lu bytes\n",(unsigned long)sizeof(g));
    return 0;
}
