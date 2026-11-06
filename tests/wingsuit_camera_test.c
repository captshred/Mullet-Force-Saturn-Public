#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "wingsuit.h"
#define S MF_WS_SCALE
static const unsigned zero[2]={0,0};
static void setup(mf_wingsuit *g,int coop){mf_ws_init(g,coop);g->spawn=100000;}
static void step(mf_wingsuit *g,unsigned a,unsigned b){unsigned h[2]={a,b};mf_ws_step(g,h,zero,3);}
static void visible(const mf_wingsuit *g)
{
    int i;assert(g->camera_x>=0 && g->camera_x<=MF_WS_CAMERA_MAX);
    for(i=0;i<2;i++)if(g->players[i].active && g->players[i].lives && !g->players[i].respawn){
        int x=g->players[i].x-g->camera_x;
        assert(x>=16*S && x<=208*S);
    }
}
static void pair(int a,int b)
{
    mf_wingsuit g;int i;setup(&g,1);
    for(i=0;i<500;i++){
        int old=g.camera_x;step(&g,a,b);visible(&g);
        assert(g.camera_x-old<=MF_WS_CAMERA_SPEED && old-g.camera_x<=MF_WS_CAMERA_SPEED);
    }
}
int main(void)
{
    mf_wingsuit g,a,b;int i,old;
    /* Mirrored player input must produce exactly mirrored fixed-point camera
       paths, equal threshold timing, and the full 48px travel each way. */
    setup(&a,0);setup(&b,0);
    assert(a.camera_x==48*S && a.players[0].x==160*S);
    assert(MF_WS_CAMERA_MAX-a.camera_x==48*S);
    for(i=0;i<160;i++){
        int ca=a.camera_x,cb=b.camera_x;
        step(&a,MF_LEFT,0);step(&b,MF_RIGHT,0);visible(&a);visible(&b);
        assert(a.camera_x+b.camera_x==96*S);
        assert(a.players[0].x+b.players[0].x==320*S);
        assert(ca-a.camera_x>=0 && ca-a.camera_x<=3*S);
        assert(b.camera_x-cb>=0 && b.camera_x-cb<=3*S);
    }
    assert(!a.camera_x && b.camera_x==96*S);
    assert(a.players[0].x==16*S && b.players[0].x==304*S);
    setup(&g,1);assert(g.camera_x==48*S && g.players[0].x==130*S && g.players[1].x==190*S);
    setup(&g,0);g.players[0].respawn=1;step(&g,0,0);
    assert(g.players[0].x==160*S && g.camera_x==48*S);
    setup(&g,0);g.players[0].x=16*S;g.camera_x=-100;mf_ws_camera_step(&g);assert(!g.camera_x);
    g.players[0].x=MF_WS_PLAYER_MAX;g.camera_x=MF_WS_CAMERA_MAX+100;mf_ws_camera_step(&g);assert(g.camera_x==MF_WS_CAMERA_MAX);
    g.camera_x=48*S;
    for(i=50;i<=174;i++){g.players[0].x=(48+i)*S;mf_ws_camera_step(&g);assert(g.camera_x==48*S);}
    g.players[0].x=97*S;mf_ws_camera_step(&g);assert(g.camera_x==47*S);
    g.camera_x=48*S;g.players[0].x=223*S;mf_ws_camera_step(&g);assert(g.camera_x==49*S);
    g.camera_x=0;g.players[0].x=270*S;
    for(i=0;i<100;i++){
        old=g.camera_x;mf_ws_camera_step(&g);assert(g.camera_x>=old && g.camera_x-old<=3*S && g.camera_x<=96*S);
    }assert(g.camera_x==96*S);
    /* Player, drone/explosion, both projectile types and Flame emitter/hitbox
       share exactly the same transform. World rectangles keep their width. */
    setup(&g,1);g.camera_x=73*S+128;
    g.enemies[0].x=300*S;g.shots[0].x=180*S;g.hostile[0].x=200*S;
    {int x[]={g.players[0].x,g.players[1].x,g.enemies[0].x,g.shots[0].x,g.hostile[0].x,g.players[0].x-11*S,g.players[0].x+11*S};
     for(i=0;i<7;i++)assert(mf_ws_screen_x(&g,x[i])-48*S==x[i]-g.camera_x);
     assert(mf_ws_screen_x(&g,x[6])-mf_ws_screen_x(&g,x[5])==22*S);}
    pair(MF_LEFT,0);pair(0,MF_RIGHT);pair(MF_LEFT,MF_LEFT);pair(MF_RIGHT,MF_RIGHT);pair(MF_LEFT,MF_RIGHT);pair(MF_RIGHT,MF_LEFT);
    setup(&g,1);
    for(i=0;i<400;i++)step(&g,MF_LEFT,MF_RIGHT);
    assert(g.players[1].x-g.players[0].x==192*S);visible(&g);
    g.players[1].lives=0;
    for(i=0;i<300;i++)step(&g,MF_RIGHT,0);
    assert(g.camera_x==MF_WS_CAMERA_MAX && g.players[0].x==MF_WS_PLAYER_MAX);
    g.players[1].active=0;step(&g,0,0);visible(&g);
    mf_ws_step(&g,zero,(unsigned[2]){0,MF_START},3);visible(&g);
    g.players[0].respawn=60;g.players[0].x=16*S;
    for(i=0;i<60;i++){step(&g,0,MF_RIGHT);visible(&g);}
    assert(!g.players[0].respawn);visible(&g);
    /* Compare every gameplay byte with distinct camera values. Fixtures cover
       Shot and Flame kills, hostile damage, contact, age-80 aimed emission,
       and existing projectiles. New rooftop parallax state is tested separately. */
    for(i=0;i<5;i++){
        setup(&a,0);a.players[0].x=180*S;a.players[0].invulnerable=0;
        a.enemies[0]=(mf_ws_enemy){1,180*S,100*S,0,0,0,0,0,0,0};
        if(i==0)a.shots[0]=(mf_ws_shot){1,180*S,106*S,0,60,0};
        if(i==1)a.players[0].shot_hold=19;
        if(i==2)a.hostile[0]=(mf_ws_hostile_shot){1,180*S,197*S,0,60,0,768};
        if(i==3)a.enemies[0].y=200*S-320;
        if(i==4){a.enemies[0].age=79;a.enemies[0].x=300*S;}
        b=a;a.camera_x=0;b.camera_x=96*S;
        step(&a,i==1?MF_A:0,0);step(&b,i==1?MF_A:0,0);
        assert(a.camera_x!=b.camera_x);a.camera_x=b.camera_x=0;
        memset(a.turrets,0,sizeof(a.turrets));memset(b.turrets,0,sizeof(b.turrets));
        assert(!memcmp(&a,&b,sizeof(a)));
        if(i<2)assert(a.deaths==1 && a.players[0].score==100);
        if(i==2 || i==3)assert(a.players[0].lives==2 && a.deaths==1);
        if(i==4)assert(a.hostile[0].active && a.hostile[0].vx<0);
    }
    setup(&g,1);g.camera_x=0;g.players[0].x=16*S;g.players[1].x=208*S;
    step(&g,0,MF_RIGHT);assert(g.players[0].x==16*S && g.players[1].x==208*S);visible(&g);
    /* Formation origins follow the view; world bounds cover both districts. */
    setup(&g,0);
    for(i=0;i<MF_WS_STAGE_WIDTH-48;i++){
        int k;g.spawn=1;for(k=0;k<MF_WS_ENEMIES;k++)g.enemies[k]=(mf_ws_enemy){0};
        g.camera_x=(i&1)?0:MF_WS_CAMERA_MAX;step(&g,0,0);
        assert(g.enemies[0].active);
        assert(g.enemies[0].x>=0 && g.enemies[0].x<=MF_WS_STAGE_WIDTH*S);
    }
    /* Long opposed/collective/reverse motion, death, respawn and connectivity. */
    setup(&g,1);
    for(i=0;i<10000;i++){
        old=g.camera_x;step(&g,(i&512)?MF_LEFT:MF_RIGHT,(i&1024)?MF_LEFT:MF_RIGHT);visible(&g);
        assert(g.camera_x-old<=3*S && old-g.camera_x<=3*S);
    }
    printf("PASS balanced 320px camera: centered solo/coop/respawn, exact mirrored 48px left/right paths; clamp, both dead-zone edges, subpixel approach/no overshoot, all world transforms, six coop patterns/max separation/death/inactivity/join/respawn, 10000-tick visibility/speed, camera-independent collisions/damage/Flame/aim/trajectories; state %lu bytes\n",(unsigned long)sizeof(g));
}
