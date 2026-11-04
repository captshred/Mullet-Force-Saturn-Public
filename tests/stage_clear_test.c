#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/game.c"
static void setup(mf_game *g)
{
    int i;mf_game_init(g);g->started=1;
    for(i=0;i<MF_DRUMS;i++)g->drums[i].hp=0;
    for(i=0;i<MF_PLAYERS;i++){
        g->players[i].active=1;g->players[i].health=83-i;
        g->players[i].x=(200+i*100)*256;g->players[i].y=200*256;
        g->players[i].invulnerable=0;
    }
}
static void victim(mf_game *g,int slot,int actor)
{
    mf_enemy *e=&g->enemies[slot];*e=(mf_enemy){0};
    e->hp=1;e->state=MF_ENEMY_IDLE;e->timer=0;e->target=-1;
    e->x=g->players[actor].x+30*256;e->y=g->players[actor].y;
    g->enemy_class[slot]=MF_ENEMY_CORPORATE_PUNK;
}
static void strike(mf_game *g,int actor,int air,int bat)
{
    mf_player *p=&g->players[actor];
    p->facing=1;p->attack=bat?MF_FAST_BAT_ACTIVE_FIRST:6;p->attack_air=air;
    p->height=air?8*256:0;p->bat=bat?MF_BAT_RUNNING:0;p->hit_mask=0;
    g->running_bat[actor].active=bat;
    player_hits(g,p);
}
int main(void)
{
    mf_game g,copy;int actor,mode,i,phase,pairs=0,singles=0,seen[4]={0},spawned=0;
    unsigned zero[2]={0,0},pause[2]={MF_START,0};
    for(actor=0;actor<2;actor++)for(mode=0;mode<5;mode++){
        setup(&g);victim(&g,0,actor);
        if(mode<3)strike(&g,actor,mode==1,mode==2);
        else fire_damage(&g,&g.enemies[0],mode==3,actor);
        assert(g.stage_kills==1 && g.enemies[0].state==MF_ENEMY_DYING);
        strike(&g,actor,0,0);fire_damage(&g,&g.enemies[0],1,actor);
        for(i=0;i<700;i++)enemy_step(&g,0);
        assert(g.stage_kills==1);
    }
    /* Singles, staggered pairs, all phases, reaction distance and overlap refill. */
    for(phase=0;phase<4;phase++){
        setup(&g);g.stage_kills=phase*10;
        for(i=0;i<500;i++){
            int k;g.enemies[0].state=g.enemies[1].state=MF_ENEMY_ABSENT;
            g.spawn_wait=0;stage_spawns(&g);
            for(k=0;k<2;k++)if(g.enemies[k].state!=MF_ENEMY_ABSENT){
                mf_enemy *e=&g.enemies[k];int a;
                ++spawned;assert(e->x>=26*256 && e->x<=614*256);
                assert(e->y>=168*256 && e->y<=229*256 && e->grace==120);
                for(a=0;a<2;a++){
                    int dx=abs_i(e->x-g.players[a].x)/256,dy=abs_i(e->y-g.players[a].y)/256;
                    assert(dx>=80 || dy>=40);assert(dx+2*dy>=110);
                }
                seen[(e->y/256==168)?0:(e->y/256==188)?1:(e->y/256==209)?2:3]++;
            }
            if(g.spawn_pair){
                int wait=g.spawn_wait;assert(wait>=18 && wait<=36);pairs++;
                while(wait--)stage_spawns(&g);
                assert(g.enemies[0].hp>0 && g.enemies[1].hp>0);
            }else{
                static const int lo[4]={90,66,45,30},hi[4]={150,120,90,66};
                assert(g.spawn_wait>=lo[phase] && g.spawn_wait<=hi[phase]);singles++;
            }
        }
    }
    assert(pairs && singles && spawned==2000);
    for(i=0;i<4;i++)assert(seen[i]);
    /* Every camera position, spread coop and street extremes. */
    for(i=0;i<=320;i+=8){
        int lane,k;for(lane=168;lane<=229;lane+=61){
            setup(&g);g.camera=i;g.players[0].x=clamp(i+30,26,614)*256;
            g.players[1].x=clamp(i+290,26,614)*256;
            g.players[0].y=g.players[1].y=lane*256;g.spawn_wait=0;
            stage_spawns(&g);
            for(k=0;k<2;k++)if(g.enemies[k].hp){
                int a;for(a=0;a<2;a++){
                    int dx=abs_i(g.enemies[k].x-g.players[a].x)/256;
                    int dy=abs_i(g.enemies[k].y-g.players[a].y)/256;
                    assert(dx>=80 || dy>=40);assert(dx+2*dy>=110);
                }
            }
        }
    }
    /* Simultaneous coop lethal candidates stop at EXACTLY 40 in a real tick. */
    setup(&g);g.stage_kills=39;victim(&g,0,0);victim(&g,1,1);
    g.players[0].attack=g.players[1].attack=6;
    g.players[0].facing=g.players[1].facing=1;
    mf_game_step_inputs(&g,zero,zero,3);
    assert(g.stage_kills==40 && g.enemies[1].hp==1 && g.events&MF_IMPACT);
    assert(g.stage_timer==MF_STAGE_SETTLE_TICKS);
    g.hitstop=0;
    for(i=0;i<MF_STAGE_SETTLE_TICKS-1;i++)mf_game_step_inputs(&g,zero,zero,3);
    assert(g.stage==MF_STAGE_SETTLING && g.enemies[0].state==MF_ENEMY_ABSENT);
    mf_game_step_inputs(&g,zero,zero,3);assert(g.stage==MF_STAGE_CLEAR);
    mf_game_step_inputs(&g,zero,pause,3);copy=g;
    for(i=0;i<100;i++)mf_game_step_inputs(&g,zero,zero,3);
    assert(!memcmp(&g,&copy,sizeof(g)));
    mf_game_step_inputs(&g,zero,pause,3);
    for(i=0;i<MF_STAGE_CLEAR_TICKS-2;i++)mf_game_step_inputs(&g,zero,zero,3);
    assert(g.stage==MF_STAGE_CLEAR);
    mf_game_step_inputs(&g,zero,zero,3);assert(g.stage==MF_STAGE_LEVEL2_ENTRY);
    setup(&g);victim(&g,0,0);g.enemy_class[0]=MF_ENEMY_SPECIAL;
    strike(&g,0,0,0);assert(!g.stage_kills);
    setup(&g);
    for(i=0;i<40;i++){
        victim(&g,0,i&1);g.players[i&1].height=0;strike(&g,i&1,0,0);
        assert(g.stage_kills==i+1);
    }
    assert(g.stage==MF_STAGE_SETTLING);
    victim(&g,1,1);strike(&g,1,0,0);assert(g.enemies[1].hp==1);
    copy=g;stage_spawns(&g);assert(!memcmp(&copy,&g,sizeof(g)));
    mf_game_step_inputs(&g,zero,pause,3);assert(g.paused);
    copy=g;for(i=0;i<180;i++)mf_game_step_inputs(&g,zero,zero,3);
    assert(!memcmp(&copy,&g,sizeof(g)));
    mf_game_step_inputs(&g,zero,pause,3);assert(!g.paused);
    for(i=0;i<1000 && g.stage!=MF_STAGE_LEVEL2_ENTRY;i++)mf_game_step_inputs(&g,zero,zero,3);
    assert(g.stage==MF_STAGE_LEVEL2_ENTRY && g.stage_kills==40);
    assert(g.enemies[1].hp==1 && g.players[0].health==83 && g.players[1].health==82);
    copy=g;for(i=0;i<200;i++)mf_game_step_inputs(&g,zero,zero,3);
    assert(!memcmp(&copy,&g,sizeof(g)));
    printf("PASS stage quota: both players, jab/kick/bat/torch/burn, no duplicates, pause, HP, Level 2 entry; %d singles, %d staggered pairs; lanes %d/%d/%d/%d\n",singles,pairs,seen[0],seen[1],seen[2],seen[3]);
    return 0;
}
