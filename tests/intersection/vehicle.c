#include <assert.h>
#include <stdio.h>
#include "game.c"

#if MF_VEHICLE_AMBUSH
static void fixture(mf_game *g)
{
    mf_game_init(g);
    g->started=1;
    g->camera=2080;
    g->players[0].x=(MF_VEHICLE_TRIGGER_X-1)*256;
    vehicle_step(g);
    assert(!g->vehicle_tick);
    g->players[0].x=MF_VEHICLE_TRIGGER_X*256;
    recover_player(g,1,1);
    g->players[1].x=g->players[0].x;
    vehicle_step(g);
    assert(g->vehicle_tick==1 && g->vehicle_camera==2080);
}

static void check_pass(unsigned pass,int expected_lane,int direction,int off_lane)
{
    mf_game g;
    fixture(&g);
    for(int avoidance=0;avoidance<3;avoidance++){
        g.vehicle_tick=vehicle_passes[pass].start;
        g.vehicle_hits=0;
        g.players[0].health=g.players[1].health=100;
        g.players[0].invulnerable=0;
        g.players[0].y=expected_lane*256;
        g.players[1].invulnerable=avoidance==2?120:0;
        g.players[1].y=(avoidance==1?off_lane:expected_lane)*256;
        g.players[1].height=avoidance==0?24*256:0;
        g.enemies[0]=(mf_enemy){.x=g.players[0].x,.y=expected_lane*256,
                               .hp=MF_ENEMY_MAX_HP,.state=MF_ENEMY_ACTIVE};
        g.enemies[1]=g.enemies[0];
        g.enemies[1].y=off_lane*256;
        while(g.vehicle_tick<vehicle_passes[pass].start+vehicle_passes[pass].duration){
            vehicle_step(&g);
            assert(g.vehicle_dir==direction && g.vehicle_lane==expected_lane);
        }
        assert(g.players[0].health==50 && g.players[0].knockback*direction>0);
        assert(g.players[1].health==100 && g.vehicle_hits==1);
        assert(g.enemies[0].state==MF_ENEMY_DYING && !g.enemies[0].hp);
        assert(g.enemies[1].hp==MF_ENEMY_MAX_HP && !g.stage_kills && !g.score);
    }
}
#endif

int main(void)
{
#if MF_VEHICLE_AMBUSH
    mf_game g;
    int passes=0,warnings=1,last=0;
    check_pass(0,216,1,180);
    check_pass(1,180,-1,216);
    check_pass(2,198,1,216);

    fixture(&g);
    for(int t=1;t<=VEHICLE_END;t++){
        g.events=0;
        vehicle_step(&g);
        if(g.events&MF_VEHICLE_WARNING){
            warnings++;
            assert(mf_vehicle_warning_lane(&g)==(warnings==2?180:198));
        }
        if(g.vehicle_dir && !last)passes++;
        last=g.vehicle_dir;
    }
    assert(passes==3 && warnings==3 && !g.vehicle_dir);
    assert(g.vehicle_x-96>=g.vehicle_camera+320);
    vehicle_step(&g);
    assert(g.vehicle_tick==VEHICLE_END+1);

    g.players[0].active=0;
    g.players[1].health=50;
    g.players[1].invulnerable=0;
    g.players[1].y=216*256;
    g.players[1].x=(g.vehicle_camera-100)*256;
    g.vehicle_tick=VEHICLE_WARN;
    g.vehicle_hits=0;
    vehicle_step(&g);
    assert(!g.players[1].health && g.players[1].defeated && g.vehicle_hits==2);

    g.stage=MF_STAGE_LEVEL2_ENTRY;
    mf_game_step(&g,0,0);
    assert(!g.vehicle_dir && g.vehicle_tick>VEHICLE_END);
    mf_game_init(&g);
    assert(!g.vehicle_tick && !g.vehicle_dir);
    puts("PASS three directions/lanes, warning timing, jump, depth, co-op hits and invulnerability, enemy KO, exit, stage handoff and reset");
#endif
    return 0;
}
