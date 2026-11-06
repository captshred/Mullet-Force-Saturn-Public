#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/wingsuit.c"
int main(void)
{
    mf_wingsuit g,h;int camera,p,i,t,seen=0,prev=-1;
    for(camera=0;camera<=96;camera+=48)for(p=0;p<3;p++){
        mf_ws_init(&g,0);g.camera_x=camera*S;g.wave=3;g.formation=p;g.spawn=1;
        spawn_enemies(&g);assert(g.enemies[5].active);h=g;
        h.enemies[2].active=0;
        for(t=0;t<500;t++){
            for(i=0;i<MF_WS_ENEMIES;i++)if(g.enemies[i].active){
                mf_ws_enemy *e=&g.enemies[i];int x=e->x;
                ++e->age;move_enemy(e);
                assert(e->x>=0 && e->x<=320*S && abs(e->x-x)<10*S);
                if(i && t>18){mf_ws_enemy sample=*e;sample.age+=18;move_enemy(&sample);
                    assert(sample.x==g.enemies[i-1].x && sample.y==g.enemies[i-1].y);}
                if(i!=2){++h.enemies[i].age;move_enemy(&h.enemies[i]);
                    assert(e->x==h.enemies[i].x && e->y==h.enemies[i].y);}
            }
        }
        assert(g.enemies[5].y>256*S);
    }
    mf_ws_init(&g,0);
    for(t=0;t<100;t++){
        memset(g.enemies,0,sizeof(g.enemies));g.wave=0;g.spawn=1;spawn_enemies(&g);
        p=g.enemies[0].pattern;assert(p!=prev);prev=p;seen|=1<<p;
        for(i=0;i<3;i++){int x=g.enemies[i].x;g.enemies[i].age=80;move_enemy(&g.enemies[i]);
            assert(g.enemies[i].x!=x);}
    }
    assert(seen==31);
    /* Actual simulation: independent one-hit kills, contact and no eye fire. */
    mf_ws_init(&g,0);g.spawn=10000;
    g.enemies[0]=(mf_ws_enemy){.active=1,.kind=MF_WS_CHROME_EYE,.origin=160*S,.age=79};
    for(t=0;t<220;t++){g.players[0].invulnerable=1000;mf_ws_step(&g,(unsigned[2]){0,0},(unsigned[2]){0,0},1);}
    for(i=0;i<MF_WS_HOSTILE;i++)assert(!g.hostile[i].active);
    assert(!g.enemies[0].active);
    mf_ws_init(&g,0);g.spawn=10000;
    g.enemies[0]=(mf_ws_enemy){.active=1,.kind=MF_WS_CHROME_EYE,.origin=160*S,.age=80};
    h=g;move_enemy(&h.enemies[0]);
    g.shots[0]=(mf_ws_shot){1,h.enemies[0].x,h.enemies[0].y+6*S+352,0,30,0};
    mf_ws_step(&g,(unsigned[2]){0,0},(unsigned[2]){0,0},1);
    assert(!g.enemies[0].active && g.enemies[0].explosion==12);
    /* Eye contact uses existing invulnerability/respawn conventions. */
    mf_ws_init(&g,0);g.spawn=10000;g.players[0].invulnerable=0;
    g.enemies[0]=(mf_ws_enemy){.active=1,.kind=MF_WS_CHROME_EYE,.pattern=0,
        .origin=g.players[0].x,.age=156};
    mf_ws_step(&g,(unsigned[2]){0,0},(unsigned[2]){0,0},1);
    assert(g.players[0].lives==2 && g.players[0].respawn==60);
    h=g;g.paused=1;h.paused=1;h.deaths=0;
    mf_ws_step(&g,(unsigned[2]){0,0},(unsigned[2]){0,0},1);assert(!memcmp(&g,&h,sizeof(g)));
    g.game_over=1;mf_ws_step(&g,(unsigned[2]){0,0},(unsigned[2]){MF_START,0},1);
    assert(!g.enemies[0].active && !g.enemies[0].kind && g.enemy_rng==0x4d465332u);
    mf_ws_init(&g,0);h=g;
    for(t=0;t<30000;t++){
        g.players[0].invulnerable=h.players[0].invulnerable=1000;
        mf_ws_step(&g,(unsigned[2]){0,0},(unsigned[2]){0,0},1);
        mf_ws_step(&h,(unsigned[2]){0,0},(unsigned[2]){0,0},1);
        assert(!memcmp(&g,&h,sizeof(g)));
    }
    printf("PASS five shuffled drone patterns; three smooth delayed eye paths/all cameras; independent removal, one-hit kills, no fire, despawn, 30000 deterministic ticks; state %zu bytes\n",sizeof(g));
}
