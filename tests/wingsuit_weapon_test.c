#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "wingsuit.h"
#define S 256
static const unsigned zero[2]={0,0};
static void setup(mf_wingsuit *g,int coop){mf_ws_init(g,coop);g->spawn=10000;}
static void step(mf_wingsuit *g,unsigned a,unsigned b){unsigned h[2]={a,b};mf_ws_step(g,h,zero,3);}
static int shots(const mf_wingsuit *g){int i,n=0;for(i=0;i<MF_WS_SHOTS;i++)n+=!!g->shots[i].active;return n;}
static void focus(mf_wingsuit *g){int i;for(i=0;i<MF_WS_FOCUS_TICKS;i++)step(g,MF_A,0);}
int main(void)
{
    mf_wingsuit g,snapshot;unsigned h[2]={MF_A,0},p[2]={0,0};int i,x,y,n;
    setup(&g,0);x=g.players[0].x;step(&g,MF_A|MF_RIGHT,0);
    assert(g.players[0].x-x==640 && g.players[0].shot_hold==1 && shots(&g)==3);
    assert(g.shots[0].vx==-S && g.shots[1].vx==0 && g.shots[2].vx==S);
    assert(g.shots[0].x==g.players[0].x-5*S && g.shots[2].x==g.players[0].x+5*S);
    assert(g.shots[0].y==g.players[0].y-21*S && g.players[0].cooldown==7);
    /* Holding briefly is mobile: the threshold, not a single A edge, causes drag. */
    for(i=1;i<MF_WS_FOCUS_TICKS-1;i++){
        x=g.players[0].x;step(&g,MF_A|MF_RIGHT,0);assert(g.players[0].x-x==640);
    }
    x=g.players[0].x;n=shots(&g);step(&g,MF_A|MF_RIGHT,0);
    assert(g.players[0].shot_hold==MF_WS_FOCUS_TICKS && g.players[0].x-x==416 && shots(&g)==n);
    assert(mf_ws_beam_active(&g,0));
    for(i=0;i<10;i++)step(&g,MF_A,0);
    assert(shots(&g)==n); /* No focused projectile remnants exist. */
    x=g.players[0].x;step(&g,MF_RIGHT,0);
    assert(g.players[0].shot_hold==0 && g.players[0].x-x==640);
    for(i=0;i<7;i++)step(&g,0,0);
    n=shots(&g);step(&g,MF_A,0);assert(shots(&g)==n+3);
    /* Diagonals retain normalization at both movement speeds. */
    setup(&g,0);x=g.players[0].x;y=g.players[0].y;step(&g,MF_UP|MF_RIGHT|MF_A,0);
    assert(g.players[0].x-x==452 && y-g.players[0].y==452);
    focus(&g);x=g.players[0].x;y=g.players[0].y;step(&g,MF_UP|MF_RIGHT|MF_A,0);
    assert(g.players[0].x-x==293 && y-g.players[0].y==293);
    assert(2*293*293<=416*416 && 2*293*293>=414*414);
    /* Repeated taps use full-speed movement and do not accumulate focus. */
    setup(&g,0);
    for(i=0;i<24;i++){
        x=g.players[0].x;step(&g,MF_LEFT|((i%8==0)?MF_A:0),0);
        assert(g.players[0].x-x==-640 && g.players[0].shot_hold<=1);
    }
    /* Independently held/tapped actors share pools, not movement/hold clocks. */
    setup(&g,1);focus(&g);x=g.players[0].x;y=g.players[1].x;
    step(&g,MF_A|MF_RIGHT,MF_A|MF_RIGHT);
    assert(g.players[0].x-x==416 && g.players[1].x-y==640 && g.players[1].shot_hold==1);
    assert(g.players[0].shot_hold==MF_WS_FOCUS_TICKS);
    for(i=0;i<MF_WS_SHOTS;i++)if(g.shots[i].active && g.shots[i].owner==1)break;
    assert(i<MF_WS_SHOTS && g.shots[i].vx==-S);
    /* A short edge latched between VBlanks still emits a mobile fan. */
    setup(&g,0);p[0]=MF_A;mf_ws_step(&g,zero,p,1);
    assert(shots(&g)==3 && !g.players[0].shot_hold);
    setup(&g,0);mf_ws_step(&g,h,p,0);assert(!shots(&g) && !g.players[0].shot_hold);
    /* A complete burst must fit: exhaustion never produces a partial stream. */
    setup(&g,0);g.players[0].shot_hold=MF_WS_FOCUS_TICKS-1;
    for(i=0;i<31;i++)g.shots[i]=(mf_ws_shot){1,160*S,100*S,1,90,0};
    step(&g,MF_A,0);assert(shots(&g)==31 && mf_ws_beam_active(&g,0));
    setup(&g,0);for(i=0;i<30;i++)g.shots[i]=(mf_ws_shot){1,160*S,100*S,1,90,0};
    step(&g,MF_A,0);assert(shots(&g)==30 && !g.players[0].cooldown);
    /* Spread cannot drift into either HUD, and TTL cleanup still applies. */
    setup(&g,0);g.shots[0]=(mf_ws_shot){1,52*S,100*S,0,60,-S};
    g.shots[1]=(mf_ws_shot){1,267*S,100*S,0,60,S};
    g.shots[2]=(mf_ws_shot){1,160*S,100*S,0,1,S};step(&g,0,0);assert(!shots(&g));
    step(&g,MF_A,0);assert(g.shots[0].vx==-S && g.shots[1].vx==0 && g.shots[2].vx==S);
    /* Disconnect cancels focus; pause freezes cadence and restart clears modes. */
    setup(&g,0);focus(&g);mf_ws_step(&g,h,zero,0);assert(!g.players[0].shot_hold);
    p[0]=MF_START;mf_ws_step(&g,h,p,1);assert(g.paused);snapshot=g;
    mf_ws_step(&g,h,zero,1);assert(!memcmp(&g,&snapshot,sizeof(g)));
    setup(&g,1);focus(&g);g.game_over=1;mf_ws_step(&g,zero,p,3);
    assert(!g.game_over && !g.players[0].shot_hold && !g.players[1].shot_hold && !shots(&g));
    printf("PASS combat pass 1: exact mobile/focus speeds, 20-tick threshold, 65%% drag, normalized diagonals, unchanged 3-way taps/attached flame, coop, atomic bursts, HUD/TTL cleanup and pause/restart; state %lu bytes\n",(unsigned long)sizeof(g));
    return 0;
}
