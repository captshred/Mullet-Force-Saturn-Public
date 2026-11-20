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
        g.players[1].height=avoidance==0?VEHICLE_JUMP_CLEARANCE:0;
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
/* Run the production input, tether and jump physics with no other
   enemies, sweeping the jump press across an entire pass. */
static int play_pass(unsigned pass,int player,int jump_tick,int lane,unsigned dodge)
{
    mf_game g;
    fixture(&g);
    g.spawn_wait=1000;
    g.vehicle_tick=vehicle_passes[pass].start;
    g.players[0].active=player!=1;
    g.players[1].active=player==1;
    g.players[player].y=lane*256;
    g.players[player].invulnerable=0;
    for(int t=0;t<vehicle_passes[pass].duration;t++){
        unsigned held[2]={0,0},pressed[2]={0,0};
        if(t>=jump_tick && jump_tick>=0)held[player]=MF_B;
        if(t==jump_tick)pressed[player]=MF_B;
        held[player]|=dodge;
        mf_game_step_inputs(&g,held,pressed,player?3:1);
        assert(g.camera==2080);
    }
    return g.players[player].health;
}

static void check_policy(void)
{
    const int camp[]={MF_ROAD_BACK,VEHICLE_MID,MF_ROAD_FRONT};
    const int lanes[]={214,187,200};
    for(int player=0;player<MF_PLAYERS;player++){
        for(unsigned i=0;i<3;i++){
            int hits=0;
            for(unsigned pass=0;pass<3;pass++)
                hits+=play_pass(pass,player,-1,camp[i],0)==50;
            assert(hits>0);
        }
        assert(play_pass(0,player,-1,MF_ROAD_FRONT,0)==50);
        assert(play_pass(1,player,-1,MF_ROAD_BACK,0)==50);
        assert(play_pass(0,player,-1,214,MF_UP)==100);
        assert(play_pass(1,player,-1,187,MF_DOWN)==100);
        assert(play_pass(2,player,-1,MF_ROAD_BACK,0)==100);
        assert(play_pass(2,player,-1,MF_ROAD_FRONT,0)==100);

        for(unsigned pass=0;pass<3;pass++){
            int streak=0,best=0;
            int duration=vehicle_passes[pass].duration;
            assert(play_pass(pass,player,0,lanes[pass],0)==50);
            assert(play_pass(pass,player,duration-1,lanes[pass],0)==50);
            for(int t=1;t<duration-1;t++){
                streak=play_pass(pass,player,t,lanes[pass],0)==100?streak+1:0;
                if(streak>best)best=streak;
            }
            assert(best>=6);
            printf("PASS hero %d pass %u: %d consecutive safe jump-press ticks at mid-screen\n",
                   player+1,pass+1,best);
        }
    }
}
static void check_encounter(int coop)
{
    mf_game g;
    fixture(&g);
    g.spawn_wait=1000;
    g.players[1].active=coop;
    for(int i=0;i<MF_PLAYERS;i++){
        g.players[i].y=VEHICLE_MID*256;
        g.players[i].invulnerable=0;
    }
    unsigned pressed[2]={0,0};
    for(int t=1;t<=VEHICLE_END;t++){
        unsigned direction=t<VEHICLE_WARN+VEHICLE_FIRST?MF_UP:MF_DOWN;
        unsigned held[2]={direction,coop?direction:0};
        mf_game_step_inputs(&g,held,pressed,coop?3:1);
        if(t<VEHICLE_END)assert(g.camera==2080);
        for(int i=0;i<=coop;i++)assert(g.players[i].health==100);
    }
    assert(!g.vehicle_dir && g.vehicle_tick==VEHICLE_END+1);
    unsigned forward[2]={MF_RIGHT,coop?MF_RIGHT:0};
    for(int t=0;t<16;t++)mf_game_step_inputs(&g,forward,pressed,coop?3:1);
    assert(g.camera>2080);
    printf("PASS %s full ambush, repositioning on original controls and camera release\n",
           coop?"co-op":"solo");
}
#endif

int main(void)
{
#if MF_VEHICLE_AMBUSH
    mf_game g;
    int passes=0,warnings=1,last=0;
    check_policy();
    check_encounter(0);
    check_encounter(1);
    check_pass(0,214,1,187);
    check_pass(1,187,-1,214);
    check_pass(2,200,1,214);

    /* Tire contact patch extremes in the 192px source, measured at rows
       65–67. Mirror texture X for the uphill pass. Compare ground and curb
       in world coordinates so camera position cancels. */
    const int tire_x[]={32,53,112,138};
    for(unsigned pass=0;pass<3;pass++){
        int direction=vehicle_passes[pass].direction;
        for(int x=MF_WORLD_BEND_X-200;x<=MF_WORLD_WIDTH+200;x++)
            for(unsigned i=0;i<sizeof(tire_x)/sizeof(tire_x[0]);i++){
                int offset=(direction>0?tire_x[i]:191-tire_x[i])-96;
                int local=vehicle_passes[pass].lane+
                    mf_world_road_drop(x)-mf_world_road_drop(x+offset);
                assert(local-3>=168 && local-1<=229);
            }
    }

    fixture(&g);
    for(int t=1;t<=VEHICLE_END;t++){
        g.events=0;
        vehicle_step(&g);
        if(g.events&MF_VEHICLE_WARNING){
            warnings++;
            assert(mf_vehicle_warning_lane(&g)==(warnings==2?187:200));
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
    g.players[1].y=214*256;
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
