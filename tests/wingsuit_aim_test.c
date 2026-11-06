/* Test the real emitter and physics; integer-only expectations. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/wingsuit.c"
static const unsigned zero[2]={0,0};
static void setup(mf_wingsuit *g)
{mf_ws_init(g,1);g->spawn=10000;g->players[0].invulnerable=g->players[1].invulnerable=10000;}
static void speed(const mf_ws_hostile_shot *s)
{
    int v=s->vx*s->vx+s->vy*s->vy;
    assert(v>=(768-2)*(768-2) && v<=(768+2)*(768+2));
}
int main(void)
{
    mf_wingsuit g,copy;mf_ws_hostile_shot shot;int i,j,dx,dy;
    assert(integer_sqrt(0)==0 && integer_sqrt(1)==1 && integer_sqrt(UINT64_MAX)==UINT32_MAX);
    /* Real age-80 muzzle, after the existing drone motion; then one physics step. */
    setup(&g);g.players[0].x=160*S;g.players[0].y=200*S;g.players[1].x=240*S;
    g.enemies[0]=(mf_ws_enemy){1,160*S,60*S-320,79,0,0,0,0,0,0};
    mf_ws_step(&g,zero,zero,3);assert(g.enemies[0].y==60*S && g.enemies[0].age==80);
    shot=g.hostile[0];assert(shot.active && shot.owner==0 && !shot.vx && shot.vy==768);
    assert(shot.x==160*S && shot.y==73*S);speed(&shot);
    for(i=0;i<5;i++)mf_ws_step(&g,zero,zero,3);
    assert(g.enemies[0].age==85 && !g.hostile[1].active); /* unchanged one-shot schedule */
    for(i=-1;i<=1;i++){
        setup(&g);g.players[1].active=0;g.players[0].x=(160+i*60)*S;g.players[0].y=200*S;
        aimed_snapshot(&g,160*S,30*S);shot=g.hostile[0];assert(shot.active && shot.vy>0);
        assert(i<0?shot.vx<0:i>0?shot.vx>0:shot.vx==0);speed(&shot);
        for(j=1;j<=10;j++){
            unsigned held[2]={MF_RIGHT,MF_LEFT};
            mf_ws_step(&g,held,zero,3);
            assert(g.hostile[0].active && g.hostile[0].vx==shot.vx && g.hostile[0].vy==shot.vy);
            assert(g.hostile[0].x==shot.x+j*shot.vx && g.hostile[0].y==shot.y+j*shot.vy);
        }
    }
    /* Nearest exact 24.8 squared distance, including subpixel differences. */
    setup(&g);g.players[0].x=110*S;g.players[1].x=210*S;
    aimed_snapshot(&g,160*S,30*S);assert(g.hostile[0].owner==0 && g.hostile[0].vx<0);
    g.hostile[0].active=0;g.players[0].x--;
    aimed_snapshot(&g,160*S,30*S);assert(g.hostile[0].owner==1 && g.hostile[0].vx>0);
    for(i=0;i<2;i++)for(j=0;j<3;j++){
        setup(&g);g.players[i].x=160*S;g.players[1-i].x=230*S;
        if(j==0)g.players[i].active=0;
        if(j==1)g.players[i].lives=0;
        if(j==2)g.players[i].respawn=5;
        aimed_snapshot(&g,160*S,30*S);
        assert(g.hostile[0].active && g.hostile[0].owner==1-i);
    }
    setup(&g);g.players[0].respawn=4;g.players[1].lives=0;
    aimed_snapshot(&g,160*S,30*S);assert(!g.hostile[0].active);
    setup(&g);g.players[0].x=160*S;g.players[1].x=240*S;
    g.enemies[0]=(mf_ws_enemy){1,160*S,60*S-320,79,0,0,0,0,0,0};
    mf_ws_step(&g,zero,zero,0);assert(g.hostile[0].active && g.hostile[0].owner==0);
    /* A disconnected hero remains present/visible in the existing simulation. */
    /* All octants, subpixel vectors and the zero-distance fallback. */
    setup(&g);g.players[1].active=0;
    for(dx=-64;dx<=64;dx++)for(dy=-64;dy<=64;dy++){
        g.players[0].x=160*S+dx;g.players[0].y=100*S+dy;g.hostile[0].active=0;
        aimed_snapshot(&g,160*S,100*S);speed(&g.hostile[0]);
        if(dx || dy){assert(dx<0?g.hostile[0].vx<=0:g.hostile[0].vx>=0);assert(dy<0?g.hostile[0].vy<=0:g.hostile[0].vy>=0);}
        else assert(!g.hostile[0].vx && g.hostile[0].vy==768);
    }
    for(dx=-80;dx<=80;dx+=5)for(dy=-80;dy<=80;dy+=5){
        g.players[0].x=160*S+dx*S;g.players[0].y=100*S+dy*S;g.hostile[0].active=0;
        aimed_snapshot(&g,160*S,100*S);speed(&g.hostile[0]);
    }
    setup(&g);for(i=0;i<MF_WS_HOSTILE;i++)assert(emit_hostile(&g,100*S,80*S,0,768,-1));
    copy=g;aimed_snapshot(&g,160*S,30*S);assert(!memcmp(g.hostile,copy.hostile,sizeof(g.hostile)));
    assert(!emit_hostile(&g,100*S,80*S,1,2,-1));
    /* Generic velocity emission does not depend on aimed targeting. */
    setup(&g);assert(emit_hostile(&g,100*S,80*S,512,0,-1));mf_ws_step(&g,zero,zero,3);
    assert(g.hostile[0].x==100*S+512 && g.hostile[0].y==80*S);
    for(i=0;i<5;i++){
        setup(&g);g.hostile[0]=(mf_ws_hostile_shot){1,160*S,100*S,0,120,0,0};
        if(i==0){g.hostile[0].x=-4*S;g.hostile[0].vx=-543;g.hostile[0].vy=543;}
        if(i==1){g.hostile[0].x=(MF_WS_STAGE_WIDTH+4)*S;g.hostile[0].vx=543;g.hostile[0].vy=543;}
        if(i==2){g.hostile[0].y=-8*S;g.hostile[0].vx=543;g.hostile[0].vy=-543;}
        if(i==3){g.hostile[0].y=248*S;g.hostile[0].vx=-543;g.hostile[0].vy=543;}
        if(i==4)g.hostile[0].ttl=1;
        mf_ws_step(&g,zero,zero,3);assert(!g.hostile[0].active);
    }
    setup(&g);for(i=0;i<5000;i++){
        int live=0;emit_hostile(&g,64*S,16*S,-543,-543,-1);mf_ws_step(&g,zero,zero,3);
        for(j=0;j<MF_WS_HOSTILE;j++)live+=g.hostile[j].active;
        assert(live<=MF_WS_HOSTILE);
    }
    assert(sizeof(mf_ws_shot)==24 && sizeof(mf_ws_hostile_shot)==28 && sizeof(g)==1672);
    puts("PASS aimed drones: age-80 muzzle, nearest living/active/nonrespawning hero, exact Buck ties and subpixel distances; all octants/zero vector normalized; snapshot-only/no homing; fixed pool, generic velocity emission and four-edge/TTL cleanup; state 1672 bytes");
}
