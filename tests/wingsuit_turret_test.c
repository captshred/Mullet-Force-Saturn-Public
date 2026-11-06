#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/wingsuit.c"
static void tick(mf_wingsuit *g){mf_ws_step(g,(unsigned[2]){0,0},(unsigned[2]){0,0},3);}
static void quiet(mf_wingsuit *g){mf_ws_init(g,1);g->spawn=10000;g->players[0].invulnerable=g->players[1].invulnerable=10000;}
static int bullets(const mf_wingsuit *g){int i,n=0;for(i=0;i<MF_WS_TURRET_SHOTS;i++)n+=!!g->turret_shots[i].active;return n;}
int main(void)
{
    mf_wingsuit g,h;int i,p,t,cam,phase,x,y;
    for(cam=0;cam<=96*S;cam++){
        quiet(&g);g.camera_x=cam;
        for(i=0;i<2;i++){
            int scroll16=96*65536+(cam-48*S)*288;
            mf_ws_turret_position(&g,i,&x,&y);
            assert(mf_ws_screen_x(&g,x)/S==(mf_ws_roof_anchors[i].map_x*65536-scroll16)/65536);
        }
    }
    for(cam=0;cam<=96;cam+=48)for(phase=0;phase<512;phase++){
        quiet(&g);g.camera_x=cam*S;g.scroll=phase;
        for(i=0;i<2;i++){mf_ws_turret_position(&g,i,&x,&y);assert(y==((mf_ws_roof_anchors[i].map_y+phase)&511)*S);}
    }
    for(p=0;p<5;p++)for(cam=0;cam<=96;cam+=48){
        int lo=100000,hi=0;quiet(&g);g.camera_x=cam*S;g.pattern_bag=1u<<p;g.spawn=1;spawn_enemies(&g);
        for(t=1;t<=220;t++)for(i=0;i<3;i++){
            mf_ws_enemy *e=&g.enemies[i];int old=e->x;e->age=t;move_enemy(e);
            assert(abs(e->x-old)<=4*S && e->x>=12*S && e->x<=308*S);
            if(t==56){if(e->x<lo)lo=e->x;if(e->x>hi)hi=e->x;}
        }
        assert(hi-lo>=90*S); /* Parent spans: 32/48/72/32/32px at local tick56. */
    }
    quiet(&g);g.scroll=300;g.turrets[1].hp=0;step_turrets(&g);assert(g.turrets[0].visible);
    for(t=0;t<MF_WS_TURRET_WARMUP-1;t++)step_turrets(&g);
    assert(!bullets(&g));step_turrets(&g);assert(bullets(&g)==1);
    assert(g.turret_shots[0].owner==0);h=g;
    g.players[0].x=16*S;g.players[1].x=304*S;
    for(t=0;t<39;t++){step_turrets(&g);}
    assert(bullets(&g)==1);
    step_turrets(&g);assert(bullets(&g)==2);
    for(t=0;t<200;t++){step_turrets(&g);}
    assert(bullets(&g)==4);
    /* Bullet velocities never follow subsequent player motion. */
    for(i=0;i<4;i++){int vx=g.turret_shots[i].vx,vy=g.turret_shots[i].vy;
        g.players[0].x+=S;step_turret_shots(&g);assert(g.turret_shots[i].vx==vx && g.turret_shots[i].vy==vy);}
    /* Periodic tracking: nearest valid hero, Buck ties, respawn/dead exclusion. */
    quiet(&g);g.scroll=300;step_turrets(&g);
    {mf_ws_turret *a=&g.turrets[0];
     g.players[0].x=a->x-20*S;g.players[1].x=a->x+20*S;
     g.players[0].y=g.players[1].y=a->y+40*S;
     turret_aim(&g,a);assert(a->target==0 && a->aim==7);
     g.players[0].respawn=60;turret_aim(&g,a);assert(a->target==1 && a->aim==1);
     g.players[1].lives=0;turret_aim(&g,a);assert(a->target==-1);}
    /* Four ordinary hits, score/death event only once, no new shots after death. */
    quiet(&g);g.scroll=300;step_turrets(&g);
    for(i=0;i<4;i++){
        mf_ws_turret *a=&g.turrets[0];
        g.shots[0]=(mf_ws_shot){1,a->x,a->y+7*S,0,40,0};tick(&g);
        assert(a->hp==3-i && !g.shots[0].active);
    }
    assert(g.turrets[0].explosion==12 && g.players[0].score==100 && g.deaths==1);
    for(t=0;t<80;t++){g.turrets[1].hp=0;tick(&g);}
    assert(!g.turrets[0].hp && !bullets(&g));
    /* Camera cannot duplicate/reset it; only the next physical map instance can. */
    for(t=0;t<97;t++){g.camera_x=t*S;step_turrets(&g);assert(!g.turrets[0].hp);}
    g.scroll=267;tick(&g);assert(g.turrets[0].y==0 && g.turrets[0].hp==4);
    assert(g.turrets[0].warmup==45);
    quiet(&g);g.scroll=300;g.players[0].shot_hold=MF_WS_FOCUS_TICKS;
    mf_ws_turret_position(&g,0,&x,&y);g.players[0].x=x;g.players[0].y=220*S;
    for(t=0;t<19;t++)mf_ws_step(&g,(unsigned[2]){MF_A,0},(unsigned[2]){0,0},3);
    assert(!g.turrets[0].hp && g.players[0].score==100);
    quiet(&g);g.players[0].invulnerable=0;
    g.turret_shots[0]=(mf_ws_hostile_shot){1,g.players[0].x,g.players[0].y-3*S,0,50,0,3*S};tick(&g);
    assert(g.players[0].lives==2 && g.players[0].respawn==60);
    h=g;g.paused=h.paused=1;h.deaths=0;tick(&g);assert(!memcmp(&g,&h,sizeof(g)));
    g.game_over=1;mf_ws_step(&g,(unsigned[2]){0,0},(unsigned[2]){MF_START,0},3);
    assert(g.turrets[0].hp==4 && !bullets(&g));
    quiet(&g);h=g;
    for(t=0;t<50000;t++){
        g.players[0].invulnerable=g.players[1].invulnerable=10000;
        h.players[0].invulnerable=h.players[1].invulnerable=10000;
        tick(&g);tick(&h);assert(!memcmp(&g,&h,sizeof(g)));
        assert(bullets(&g)<=4);for(i=0;i<2;i++)assert(g.turrets[i].hp>=0 && g.turrets[i].hp<=4);
    }
    printf("PASS turret: all 24577 camera samples/512 rows; five expanded smooth drone families; target validity, warmup/40-tick cadence, fixed four-shot pool/nonhoming, four-hit/beam kills, camera/cycle latch, pause/reset, 50000 deterministic ticks; state %zu bytes\n",sizeof(g));
}
