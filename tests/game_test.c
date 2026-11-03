#include <assert.h>
#include <stdio.h>
#include "game.h"
static void step(mf_game *g,int n,unsigned held) { while(n--) mf_game_step(g,held,0); }
static void start(mf_game *g) { mf_game_init(g); mf_game_step(g,0,MF_START); g->enemies[1].state=MF_ENEMY_ABSENT;g->enemies[1].hp=0;g->enemies[1].timer=100000; g->enemies[0].state=MF_ENEMY_ABSENT; g->enemies[0].hp=0; g->enemies[0].timer=100000; }
static void place(mf_game *g) {
    g->players[0].x=220*256; g->players[0].y=199*256; g->players[0].facing=1;
    g->drums[0].x=260*256; g->drums[0].y=199*256; g->drums[0].vx=0;
}
int main(void)
{
    mf_game g; int x,y,hp,i;
    mf_game_init(&g); step(&g,50,MF_RIGHT); assert(g.players[0].x==100*256);
    start(&g); x=g.players[0].x; step(&g,60,MF_RIGHT); assert(g.players[0].x>x+80*256);
    step(&g,1500,MF_RIGHT|MF_DOWN); assert(g.players[0].x==614*256 && g.players[0].y==229*256 && g.camera==320);
    step(&g,1500,MF_LEFT|MF_UP); assert(g.players[0].x==26*256 && g.players[0].y==168*256 && g.camera==0);
    puts("PASS start gate, movement, world bounds, camera limits");
    start(&g); y=g.players[0].y; mf_game_step(&g,0,MF_B); assert(g.players[0].height>0);
    x=g.players[0].x; step(&g,10,MF_RIGHT); assert(g.players[0].x>x && g.players[0].y==y && g.players[0].height>0);
    step(&g,60,0); assert(!g.players[0].height && !g.players[0].vz && g.players[0].y==y);
    mf_game_step(&g,0,MF_B); step(&g,7,MF_UP); assert(g.players[0].y<y && g.players[0].height>0);
    puts("PASS separate ground/jump coordinates, air steering and landing");
    start(&g); place(&g); mf_game_step(&g,0,MF_A); step(&g,3,MF_A);
    assert(g.drums[0].hp==3); step(&g,8,MF_A); assert(g.drums[0].hp==2);
    assert(g.drums[0].vx>0 && g.drums[0].flash>0);
    step(&g,100,MF_A); assert(!g.players[0].attack && g.drums[0].hp==2);
    puts("PASS anticipation/contact/recovery, single hit per swing, held A releases");
    start(&g); place(&g); g.players[0].y-=20*256; mf_game_step(&g,0,MF_A); step(&g,30,0); assert(g.drums[0].hp==3);
    place(&g); g.players[0].facing=-1; mf_game_step(&g,0,MF_A); step(&g,30,0); assert(g.drums[0].hp==3);
    place(&g); g.players[0].x=100*256; mf_game_step(&g,0,MF_A); step(&g,30,0); assert(g.drums[0].hp==3);
    puts("PASS rejects wrong depth, wrong facing and out-of-range hits");
    start(&g); place(&g); mf_game_step(&g,0,MF_B); mf_game_step(&g,0,MF_A);
    assert(g.players[0].attack_air); step(&g,5,0); assert(g.drums[0].hp==2);
    step(&g,80,0); assert(!g.players[0].attack && !g.players[0].height);
    puts("PASS airborne kick collision and finite recovery");
    start(&g); place(&g); g.players[0].facing=-1; g.players[0].x=300*256;
    mf_game_step(&g,0,MF_A); step(&g,10,0); assert(g.drums[0].hp==2 && g.drums[0].vx<0);
    puts("PASS mirrored punch and leftward knockback");
    start(&g);
    for(i=0;i<3;i++) { place(&g); mf_game_step(&g,0,MF_A); step(&g,30,0); }
    assert(!g.drums[0].hp && g.broken==1 && g.score==130);
    step(&g,250,0); assert(g.drums[0].hp==3 && g.drums[0].x==260*256);
    puts("PASS drum destruction, score and timed respawn");
    start(&g); mf_game_step(&g,0,MF_B); mf_game_step(&g,0,MF_START);
    x=g.players[0].x; y=g.players[0].height; hp=g.drums[0].hp; step(&g,90,MF_RIGHT|MF_A|MF_B);
    assert(g.paused && g.players[0].x==x && g.players[0].height==y && g.drums[0].hp==hp);
    mf_game_step(&g,0,MF_START); assert(!g.paused && g.players[0].height!=y);
    assert(!g.debug); mf_game_step(&g,0,MF_C); assert(g.debug);
    puts("PASS pause freezes simulation, resume, debug off by default");
    start(&g);
    assert(mf_buck_frame(&g)==0);
    mf_game_step(&g,0,MF_B); assert(mf_buck_frame(&g)==11);
    step(&g,8,0); assert(mf_buck_frame(&g)==12);
    while(g.players[0].height) mf_game_step(&g,0,0);
    assert(g.players[0].landing==6 && mf_buck_frame(&g)==13);
    step(&g,6,0); assert(mf_buck_frame(&g)<2);
    for(i=0;i<30;i++) { g.players[0].walk=i; g.players[0].moving=1; assert(mf_buck_frame(&g)==2+i/5); }
    g.players[0].moving=0;
    g.players[0].attack=1; assert(mf_buck_frame(&g)==8);
    g.players[0].attack=6; assert(mf_buck_frame(&g)==9);
    g.players[0].attack=11; assert(mf_buck_frame(&g)==10);
    g.players[0].height=10*256; assert(mf_buck_frame(&g)==14);
    start(&g); place(&g); g.drums[0].x=g.players[0].x+64*256;
    mf_game_step(&g,0,MF_A); step(&g,9,0); assert(g.drums[0].hp==2);
    start(&g); place(&g); g.drums[0].x=g.players[0].x+65*256;
    mf_game_step(&g,0,MF_A); step(&g,9,0); assert(g.drums[0].hp==3);
    puts("PASS upgraded animation selection, landing duration and revised punch reach");
    return 0;
}
