#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "wingsuit.h"
#define S 256
static const unsigned zero[2]={0,0};
static void setup(mf_wingsuit *g){mf_ws_init(g,1);g->spawn=10000;}
static void step(mf_wingsuit *g,unsigned a,unsigned b){unsigned held[2]={a,b};mf_ws_step(g,held,zero,3);}
static void drone(mf_wingsuit *g,int x,int y){g->enemies[0]=(mf_ws_enemy){1,x,y,0,0};}
int main(void)
{
    mf_wingsuit g;int i,x,total;
    setup(&g);g.players[0].shot_hold=MF_WS_FOCUS_TICKS-1;
    drone(&g,g.players[0].x,100*S);step(&g,MF_A,0);
    assert(mf_ws_beam_active(&g,0) && !g.enemies[0].active && g.deaths==1 && g.players[0].score==100);
    drone(&g,g.players[0].x,100*S);
    for(i=1;i<6;i++){step(&g,MF_A,0);assert(g.enemies[0].active && !g.deaths);}
    step(&g,MF_A,0);assert(!g.enemies[0].active && g.deaths==1 && g.players[0].score==200);
    step(&g,0,0);assert(!mf_ws_beam_active(&g,0) && !g.beam_wait[0]);
    drone(&g,g.players[0].x,100*S);
    for(i=0;i<10;i++){step(&g,0,0);assert(g.enemies[0].active && !g.deaths);}
    /* Move across an enemy: collision follows the current player center. */
    setup(&g);g.players[0].shot_hold=MF_WS_FOCUS_TICKS-1;x=g.players[0].x;
    drone(&g,x+22*S,100*S);step(&g,MF_A|MF_RIGHT,0);
    assert(g.players[0].x==x+416 && !g.enemies[0].active && g.deaths==1);
    /* Outside the stream and above its tip remain unaffected. */
    setup(&g);g.players[0].shot_hold=MF_WS_FOCUS_TICKS-1;drone(&g,g.players[0].x+22*S,100*S);
    step(&g,MF_A,0);assert(g.enemies[0].active && !g.deaths);
    /* Full-height damage reaches the top, at every representative emitter. */
    {
        static const int ys[]={16,32,64,128,200,223};int n;
        for(n=0;n<6;n++){
            setup(&g);g.players[0].y=ys[n]*S;g.players[0].shot_hold=19;
            drone(&g,g.players[0].x,-320);step(&g,MF_A,0);
            assert(!g.enemies[0].active && g.deaths==1); /* center at y=0 */
            setup(&g);g.players[0].y=ys[n]*S;g.players[0].shot_hold=19;
            drone(&g,g.players[0].x,-10*S-321);step(&g,MF_A,0);
            assert(g.enemies[0].active && !g.deaths); /* below top by -1 subpixel */
            setup(&g);g.players[0].y=ys[n]*S;g.players[0].shot_hold=19;
            drone(&g,g.players[0].x,(ys[n]-MF_WS_BEAM_EMITTER+10)*S+1-320);
            step(&g,MF_A,0);assert(g.enemies[0].active && !g.deaths);
        }
    }
    /* Same drone in both beams emits only one death, then only an explosion. */
    setup(&g);g.players[1].x=g.players[0].x;g.players[0].shot_hold=g.players[1].shot_hold=MF_WS_FOCUS_TICKS-1;
    drone(&g,g.players[0].x,100*S);step(&g,MF_A,MF_A);assert(g.deaths==1);
    total=g.deaths;for(i=0;i<20;i++){step(&g,MF_A,MF_A);total+=g.deaths;}assert(total==1);
    /* Single-shot deaths use the very same one-shot event count. */
    setup(&g);drone(&g,100*S,100*S);g.shots[0]=(mf_ws_shot){1,100*S,107*S,0,60,0};
    step(&g,0,0);assert(g.deaths==1);step(&g,0,0);assert(!g.deaths);
    for(i=0;i<2;i++){
        int k;setup(&g);g.players[i].invulnerable=0;
        g.hostile[0]=(mf_ws_hostile_shot){1,g.players[i].x,g.players[i].y-3*S,0,60,0,768};
        step(&g,0,0);assert(g.deaths==1 && g.players[i].lives==2);
        for(k=0;k<60;k++){step(&g,0,0);assert(!g.deaths);}
        g.players[i].lives=1;g.players[i].invulnerable=0;
        g.hostile[0]=(mf_ws_hostile_shot){1,g.players[i].x,g.players[i].y-3*S,0,60,0,768};
        step(&g,0,0);assert(g.deaths==1 && !g.players[i].lives && !mf_ws_beam_active(&g,i));
        for(k=0;k<10;k++){step(&g,0,0);assert(!g.deaths);}
    }
    /* Exact activation boundary, release and nineteen-tick repeated taps. */
    for(i=0;i<2;i++){
        int k,cycle;unsigned held[2]={0,0};held[i]=MF_A;setup(&g);
        for(k=1;k<=19;k++){
            mf_ws_step(&g,held,zero,3);assert(g.players[i].shot_hold==k && !mf_ws_beam_active(&g,i));
        }
        mf_ws_step(&g,held,zero,3);assert(g.players[i].shot_hold==20 && mf_ws_beam_active(&g,i));
        mf_ws_step(&g,zero,zero,3);assert(!g.players[i].shot_hold && !mf_ws_beam_active(&g,i) && !g.beam_wait[i]);
        for(cycle=0;cycle<12;cycle++){
            for(k=0;k<19;k++){mf_ws_step(&g,held,zero,3);assert(!mf_ws_beam_active(&g,i));}
            mf_ws_step(&g,zero,zero,3);assert(!g.players[i].shot_hold);
        }
    }
    puts("PASS flame tuning: P1/P2 nineteen ticks inactive, twentieth active; repeated sub-threshold taps; top/emitter collision bounds across six player heights");
    puts("PASS flame: activation/release, attached movement, six-tick pulses, area/top bounds, coop single kill, single-shot death, Buck/Chuck life-loss and final-death events exactly once");
}
