/* Production simulation, no mock attack scheduler or duplicated AI. */
#include <string.h>
#define main ai2_tests
#include "punk_ai_test.c"
#undef main
static void scenario(mf_game *g,int behavior,int lane)
{
    setup(g,0,1);g->punk[0]=(mf_punk_ai){0};
    g->punk[0].rng=0x12345678u;g->punk[0].behavior=behavior;g->punk[0].lane=lane;
    g->enemies[0].x=100*256;g->enemies[0].y=190*256;
    g->players[0].x=300*256;g->players[0].y=200*256;g->players[0].invulnerable=100000;
}
static int attacking(const mf_game *g)
{return g->enemies[0].state==MF_ENEMY_WINDUP && g->punk[0].phase!=MF_PUNK_PREP;}
int main(void)
{
    mf_game g,copy;int b,lane,i,n,x,y,prep,rush,attacks,counts[4]={0},max_wait=0;
    unsigned seed;
    for(b=0;b<4;b++)for(lane=-1;lane<=1;lane+=2){
        scenario(&g,b,lane);g.enemies[0].x=330*256;g.enemies[0].y=200*256;
        g.punk[0].phase=MF_PUNK_PREP;g.enemies[0].state=MF_ENEMY_WINDUP;g.enemies[0].timer=9;
        enemy_step(&g,0);assert(attacking(&g) && g.enemies[0].timer==14);
        /* Every pattern attacks on recovery expiry; no idle decision tick. */
        g.enemies[0].state=MF_ENEMY_RECOVER;g.enemies[0].timer=1;
        enemy_step(&g,0);assert(attacking(&g) && g.enemies[0].timer==14);
        for(i=MF_PUNK_PREP;i<=MF_PUNK_RUSH;i++){
            g.punk[0].phase=i;g.enemies[0].state=MF_ENEMY_HURT;g.enemies[0].timer=5;g.enemies[0].vx=0;
            x=g.enemies[0].x;y=g.enemies[0].y;
            enemy_step(&g,0);assert(g.enemies[0].state==MF_ENEMY_HURT && g.enemies[0].timer==4);
            assert(g.enemies[0].x==x && g.enemies[0].y==y && g.punk[0].phase==MF_PUNK_CLOSE);
        }
        scenario(&g,b,lane);g.enemies[0].y=lane>0?178*256:222*256;
        x=g.enemies[0].x;y=g.enemies[0].y;enemy_step(&g,0);
        if(g.punk[0].phase==MF_PUNK_PREP){
            for(n=0;n<12 && g.punk[0].phase==MF_PUNK_PREP;n++)enemy_step(&g,0);
            enemy_step(&g,0);
        }
        assert(g.enemies[0].x>x && g.enemies[0].y!=y); /* X and Y on same tick. */
        if(b==MF_PUNK_FLANKER || b==MF_PUNK_AMBUSHER){
            scenario(&g,b,lane);g.enemies[0].y=(200+lane*24)*256;
            for(i=0;i<30;i++)enemy_step(&g,0);
            assert((g.enemies[0].y-g.players[0].y)*lane>12*256);
        }
        /* All routes close and attack a stationary player, both lane signs. */
        scenario(&g,b,lane);g.enemies[0].y=(200+lane*24)*256;prep=rush=attacks=0;
        for(i=0;i<1200;i++){
            enemy_step(&g,0);
            if(g.punk[0].phase==MF_PUNK_PREP)prep++;
            if(g.punk[0].phase==MF_PUNK_RUSH)rush++;
            if(attacking(&g)){attacks++;break;}
        }
        assert(attacks && i<1200);if(i>max_wait)max_wait=i;
        if(b==MF_PUNK_FLANKER || b==MF_PUNK_AMBUSHER)assert(prep && rush);
        /* Counter windup cannot be replaced by a movement preparation. */
        scenario(&g,b,lane);g.enemies[0].x=330*256;g.enemies[0].y=200*256;
        g.punk[0].punches=5;g.punk[0].expiry=180;
        enemy_step(&g,0);assert(attacking(&g) && g.enemies[0].timer==10);
    }
    /* Fixed 5/3 burst velocity; launch capture does not home on the player. */
    scenario(&g,MF_PUNK_AMBUSHER,1);g.enemies[0].x=220*256;g.enemies[0].y=224*256;
    enemy_step(&g,0);assert(g.punk[0].phase==MF_PUNK_PREP);
    n=g.enemies[0].timer;assert(n>=8 && n<=10);x=g.enemies[0].x;y=g.enemies[0].y;
    for(i=0;i<n;i++){
        enemy_step(&g,0);assert(g.enemies[0].x==x && g.enemies[0].y==y);
        assert(g.players[0].health==100);
    }
    assert(g.punk[0].phase==MF_PUNK_RUSH && g.punk[0].clock>=10 && g.punk[0].clock<=18);
    n=g.punk[0].clock;g.players[0].x=500*256;g.players[0].y=229*256;
    for(i=0;i<n;i++){
        x=g.enemies[0].x;y=g.enemies[0].y;enemy_step(&g,0);
        assert(g.enemies[0].x-x==500 && g.enemies[0].y-y==-366);
        assert(g.players[0].health==100);
    }
    assert(g.punk[0].phase==MF_PUNK_CLOSE);
    /* Arrival through a rush still needs the complete interruptible windup. */
    g.players[0].x=g.enemies[0].x+30*256;g.players[0].y=g.enemies[0].y;
    g.players[0].invulnerable=0;enemy_step(&g,0);assert(attacking(&g) && g.enemies[0].timer==14);
    for(i=0;i<13;i++){enemy_step(&g,0);assert(g.players[0].health==100);}
    punch(&g,0);assert(g.enemies[0].state==MF_ENEMY_HURT); /* Can interrupt final ready tick. */
    /* Opportunist travels to the actual rear side; does not choose a random side. */
    scenario(&g,MF_PUNK_OPPORTUNIST,1);g.enemies[0].x=430*256;g.enemies[0].y=224*256;
    g.players[0].attack=8;
    for(i=0;i<800 && !attacking(&g);i++)enemy_step(&g,0);
    assert(attacking(&g) && g.enemies[0].x<g.players[0].x);
    /* Coincident roots and depth/X corners cannot deadlock. */
    for(b=0;b<4;b++)for(lane=0;lane<4;lane++){
        scenario(&g,b,1);g.players[0].x=(lane&1?614:26)*256;
        g.players[0].y=(lane&2?229:168)*256;
        g.enemies[0].x=g.players[0].x;g.enemies[0].y=g.players[0].y;
        for(i=0;i<800 && !attacking(&g);i++)enemy_step(&g,0);
        assert(attacking(&g));
    }
    /* Identical seeds/inputs produce identical simulation state. Exercise all
       borders, moving/co-op targets, retargeting and every state for 50k ticks. */
    scenario(&g,MF_PUNK_FLANKER,-1);g.players[1]=g.players[0];g.players[1].active=1;
    g.enemies[1]=g.enemies[0];g.enemies[1].x=500*256;g.enemies[1].y=222*256;
    g.punk[1]=g.punk[0];g.punk[1].behavior=MF_PUNK_OPPORTUNIST;g.punk[1].lane=1;
    copy=g;
    for(i=0;i<50000;i++){
        for(b=0;b<2;b++){
            int px=26+(i*(b?3:2))%589,py=168+(i*(b?2:1))%62;
            g.players[b].x=copy.players[b].x=px*256;g.players[b].y=copy.players[b].y=py*256;
            g.players[b].facing=copy.players[b].facing=i%60<30?1:-1;
            g.players[b].invulnerable=copy.players[b].invulnerable=10000;
            enemy_step(&g,b);enemy_step(&copy,b);
            assert(g.enemies[b].x>=26*256 && g.enemies[b].x<=614*256);
            assert(g.enemies[b].y>=168*256 && g.enemies[b].y<=229*256);
            assert(g.enemies[b].timer>=0 && g.punk[b].clock>=0);
        }
        assert(!memcmp(&g,&copy,sizeof g));
    }
    /* Confirm actual commitment cadence and frozen simulation clocks. */
    for(b=0;b<2;b++)for(lane=0;lane<2;lane++){
        int first=-1,period=0;
        scenario(&g,MF_PUNK_BRAWLER,1);g.enemies[0].x=330*256;g.enemies[0].y=200*256;
        if(b){g.enemies[1]=g.enemies[0];g.enemies[0].state=MF_ENEMY_ABSENT;}
        g.punk[b].punches=lane?5:0;g.punk[b].expiry=180;
        for(i=0;i<100;i++){
            int prior=g.enemies[b].state;enemy_step(&g,b);
            if(prior!=MF_ENEMY_WINDUP && g.enemies[b].state==MF_ENEMY_WINDUP){
                if(first<0)first=i;else{period=i-first;break;}
            }
        }
        assert(period==(lane?35:39)+b*6);
    }
    scenario(&g,MF_PUNK_FLANKER,1);g.punk[0].phase=MF_PUNK_RUSH;
    g.punk[0].clock=12;g.punk[0].burst_x=1;g.punk[0].burst_y=1;
    g.enemies[0].state=MF_ENEMY_WALK;g.punk[0].expiry=180;g.hitstop=3;
    copy=g;
    {unsigned z[2]={0,0};mf_game_step_inputs(&g,z,z,1);}
    assert(g.enemies[0].x==copy.enemies[0].x && g.enemies[0].y==copy.enemies[0].y);
    assert(g.punk[0].clock==12 && g.punk[0].expiry==180);
    g.stage=MF_STAGE_LEVEL2_ENTRY;copy=g;enemy_step(&g,0);assert(!memcmp(&g,&copy,sizeof g));
    /* A player repeatedly running up/down remains attackable. No target
       teleportation: use the actual player speed and production input step. */
    for(b=0;b<4;b++){
        int dir=1,opportunities=0;
        scenario(&g,b,1);
        for(i=0;i<1800;i++){
            int prior=g.enemies[0].state;
            if(g.players[0].y>=229*256)dir=-1;
            if(g.players[0].y<=168*256)dir=1;
            player_step(&g,0,dir>0?MF_DOWN:MF_UP,0);enemy_step(&g,0);
            if(prior!=MF_ENEMY_WINDUP && attacking(&g))opportunities++;
        }
        assert(opportunities>10);
    }
    /* Assignment never advances the approved stage RNG or repeats a pair type. */
    scenario(&g,0,1);g.enemies[0].state=g.enemies[1].state=MF_ENEMY_ABSENT;
    for(i=0;i<10000;i++){
        mf_game reference=g;
        seed=g.spawn_rng;enemy_spawn(&g,i&1,0);
        /* Match the original spawn candidate generator, not an extra AI draw. */
        reference.punk[0].rng=reference.punk[1].rng=0;
        enemy_spawn(&reference,i&1,0);assert(g.spawn_rng==reference.spawn_rng);
        assert(g.spawn_rng!=seed);
        b=g.punk[i&1].behavior;assert(b>=0 && b<4);counts[b]++;
        assert(g.punk[0].behavior!=g.punk[1].behavior);
    }
    for(b=0;b<4;b++)assert(counts[b]>2000 && counts[b]<3000);
    printf("PASS AI3: all patterns/lanes, immediate legal attacks and recovery, hurt cancellation, prepared nonhoming 5/3 rushes, full interruptible telegraphs, rear pursuit, corner/coincident recovery, 50000 deterministic moving-target ticks; max stationary approach %d; 10000 spawn distribution %d/%d/%d/%d; game state %zu bytes\n",max_wait,counts[0],counts[1],counts[2],counts[3],sizeof g);
    return 0;
}
