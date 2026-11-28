#include <assert.h>
#include <stdio.h>
#include "../src/game.c"
#include "dev_stage_skip.h"

static void tick(mf_game *g, unsigned p1, unsigned p2, unsigned connected)
{
    const unsigned held[]={p1,p2}, pressed[]={0,0};
    int camera=g->camera, floor=g->camera_floor;
    mf_game_step_inputs(g,held,pressed,connected);
    if(!g->bruce.active) {
        assert(abs_i(g->camera-camera)<=MF_WORLD_CAMERA_STEP);
        assert(g->camera_floor>=floor && g->camera>=g->camera_floor);
    }
    if(encounter_locked(g)) {
        const mf_encounter_definition *e=encounter(g);
        assert(g->camera<=e->camera_limit);
        for(int i=0;i<MF_PLAYERS;i++)
            if(living(&g->players[i]))assert(g->players[i].x<=e->player_limit*256);
    }
}

static void wait_for_spawn(mf_game *g, int coop)
{
    for(int t=0;t<180 && !live_enemies(g);t++)
        tick(g,MF_RIGHT,coop?MF_RIGHT:0,coop?3:1);
    assert(live_enemies(g)>0);
}

static void complete_street(int coop)
{
    static const int quotas[]={6,8,7,9};
    mf_game g;
    mf_game_init(&g);
    g.started=1;
    g.god_mode=1;
    if(coop)recover_player(&g,1,1);
    for(unsigned index=0;index<MF_ENCOUNTER_COUNT;index++) {
        const mf_encounter_definition *e=encounter(&g);
        assert(g.encounter_index==index && mf_encounter_quota(&g)==quotas[index]);
        assert(!g.encounter_kos && !mf_encounter_go(&g));
        for(int t=0;t<2100 && g.players[0].x<e->player_limit*256;t++) {
            tick(&g,MF_RIGHT,coop?MF_RIGHT:0,coop?3:1);
            assert(mf_enemy_count(&g)<=mf_enemy_limit(&g));
        }
        assert(g.players[0].x==e->player_limit*256);
        if(e->dependencies&MF_ENCOUNTER_WAIT_VEHICLE)assert(g.vehicle_tick>0);
        for(int credit=1;credit<=e->quota;credit++) {
            wait_for_spawn(&g,coop);
            int slot=0;
            while(!g.enemies[slot].hp)++slot;
            mf_enemy *victim=&g.enemies[slot];
            assert(victim->x<=e->player_limit*256);
            victim->hp=1;
            if(credit==1) {
                mf_player *p=&g.players[0];
                p->facing=-1;
                p->attack=6;
                p->hit_mask=0;
                victim->x=p->x-30*256;
                victim->y=p->y;
                victim->grace=0;
                player_hits(&g,p);
                p->attack=0;
            }else fire_damage(&g,victim,credit&1,coop?1:0);
            assert(victim->state==MF_ENEMY_DYING && g.encounter_kos==credit);
            int score=g.score, total=g.stage_kills;
            fire_damage(&g,victim,1,0);
            assert(g.score==score && g.stage_kills==total && g.encounter_kos==credit);
        }
        assert(!mf_encounter_go(&g));
        unsigned rng=g.spawn_rng;
        for(int t=0;t<VEHICLE_END+60 && !mf_encounter_go(&g);t++) {
            tick(&g,MF_RIGHT,coop?MF_RIGHT:0,coop?3:1);
            assert(g.spawn_rng==rng && g.encounter_index==index);
        }
        assert(!mf_enemy_count(&g) && mf_encounter_go(&g));
        if(index+1<MF_ENCOUNTER_COUNT) {
            for(int t=0;t<400 && g.encounter_index==index;t++)
                tick(&g,MF_RIGHT,coop?MF_RIGHT:0,coop?3:1);
            assert(g.encounter_index==index+1 && !mf_encounter_go(&g));
        }
    }
    assert(g.stage_kills==30 && g.stage==MF_STAGE_LEVEL1);
    for(int t=0;t<400 && !mf_bruce_approach(&g.bruce,&g);t++)
        tick(&g,MF_RIGHT,coop?MF_RIGHT:0,coop?3:1);
    assert(g.bruce.approach && !mf_encounter_go(&g));
    g.bruce.ready=1;g.street_spawns_suspended=1;
    tick(&g,0,0,coop?3:1);
    assert(g.bruce.active && g.bruce.health==MF_BRUCE_MAX_HP && !mf_encounter_go(&g));
    assert(g.events&MF_BRUCE_ENTRANCE_JUMP);
    for(int i=0;i<=coop;i++)assert(g.players[i].x>=MF_BRUCE_ARENA_REAR*256);
    g.bruce.state=MF_BRUCE_READY;
    mf_bruce_receive(&g.bruce,MF_BRUCE_MAX_HP,0,1);
    for(int t=0;t<120;t++)tick(&g,0,0,coop?3:1);
    assert(g.bruce.state==MF_BRUCE_DEFEATED && g.stage_kills==30);
    assert(g.stage==MF_STAGE_LEVEL1);
}

static void check_menu_and_population(void)
{
    static const unsigned rows[]={0,0,1,2,2,3,3,3};
    mf_game g;
    mf_game_init(&g);
    for(int section=0;section<MF_SECTION_COUNT;section++) {
        mf_section_init(&g,(mf_section)section);
        assert(g.encounter_index==rows[section] && !g.encounter_kos);
        assert((section>=MF_SECTION_BRUCE)==g.encounter_cleared);
        if(section<MF_SECTION_BRUCE) {
            assert(g.camera<=encounter(&g)->camera_limit);
            assert(g.players[0].x<=encounter(&g)->player_limit*256);
            unsigned index=g.encounter_index;
            g.encounter_kos=2;
            assert(mf_encounter_restart(&g));
            assert(g.encounter_index==index && !g.encounter_kos && !g.encounter_cleared);
            assert(g.players[0].x==encounter(&g)->restart_x*256);
            assert(g.camera_floor==mf_world_checkpoint(g.camera));
        }else assert(!mf_encounter_restart(&g));
    }

    mf_section_init(&g,MF_SECTION_INTERSECTION);
    g.spawn_wait=1000;
    g.encounter_kos=2;
    for(int t=0;t<420;t++)tick(&g,MF_LEFT,0,1);
    assert(g.camera==1280 && g.camera_floor==1280 && g.players[0].x==1306*256);
    assert(g.encounter_index==1 && g.encounter_kos==2);

    mf_section_init(&g,MF_SECTION_VEHICLE);
    int camera=g.camera;
    g.encounter_kos=mf_encounter_quota(&g);
    tick(&g,0,0,1);
    assert(g.vehicle_tick==1 && (g.events&MF_VEHICLE_WARNING) && !mf_encounter_go(&g));
    assert(g.camera==camera);
    g.vehicle_tick=VEHICLE_END;
    tick(&g,0,0,1);
    assert(mf_encounter_go(&g));

    mf_section_init(&g,MF_SECTION_VEHICLE);
    tick(&g,0,0,1);
    g.vehicle_tick=vehicle_passes[0].start;
    g.enemies[0]=(mf_enemy){.x=g.players[0].x,.y=214*256,.hp=6,.state=MF_ENEMY_IDLE,.target=-1};
    while(g.enemies[0].hp>0 && g.vehicle_tick<vehicle_passes[0].start+vehicle_passes[0].duration)
        vehicle_step(&g);
    assert(g.enemies[0].state==MF_ENEMY_DYING && !g.encounter_kos && !g.stage_kills && !g.score);

    mf_section_init(&g,MF_SECTION_OPENING);
    mf_game_step_coop(&g,(unsigned[2]){0,0},(unsigned[2]){0,MF_START});
    assert(g.players[1].active && mf_enemy_limit(&g)==3);
    for(int i=0;i<MF_ENEMIES;i++)
        g.enemies[i]=(mf_enemy){.x=(110+i*60)*256,.y=169*256,.hp=6,.state=MF_ENEMY_IDLE,.target=-1};
    g.encounter_kos=2;
    tick(&g,0,0,1);
    assert(!g.players[1].active && live_enemies(&g)==2 && g.encounter_kos==2);
    mf_game_step_coop(&g,(unsigned[2]){0,0},(unsigned[2]){0,MF_START});
    assert(g.players[1].active && g.encounter_kos==2);
    g.players[1].health=0;g.players[1].defeated=1;
    tick(&g,0,0,3);
    assert(g.players[1].health==100 && g.encounter_kos==2);

    unsigned pressed[2]={MF_X,0};
    mf_dev_stage_skip(&g,pressed);
    assert(g.stage==MF_STAGE_LEVEL1);
    g.paused=1;
    mf_game saved=g;
    tick(&g,0,0,3);
    assert(g.ticks==saved.ticks && g.camera==saved.camera && g.encounter_kos==saved.encounter_kos);
    mf_dev_stage_skip(&g,pressed);
    assert(g.stage==MF_STAGE_LEVEL2_ENTRY && !g.paused && !mf_encounter_go(&g));
    tick(&g,MF_RIGHT,MF_RIGHT,3);
    assert(g.stage==MF_STAGE_LEVEL2_ENTRY && g.encounter_kos==2);
}

static void check_empty_gate_spawn(void)
{
    mf_game g;
    mf_game_init(&g);
    g.started=1;
    recover_player(&g,1,1);
    for(unsigned i=0;i<MF_ENCOUNTER_COUNT;i++) {
        g.encounter_index=i;
        const mf_encounter_definition *e=encounter(&g);
        g.camera=e->camera_limit;
        g.camera_floor=mf_world_checkpoint(g.camera);
        for(int x=g.camera+26;x<=e->player_limit;x+=13)
            for(int y=x;y<=e->player_limit;y+=13)
                for(int lane=168;lane<=229;lane+=15) {
                    g.players[0].x=x*256;g.players[1].x=y*256;
                    g.players[0].y=lane*256;g.players[1].y=(397-lane)*256;
                    g.enemies[0]=(mf_enemy){0};
                    g.spawn_wait=0;
                    stage_spawns(&g);
                    assert(live_enemies(&g)==1 && g.enemies[0].x<=e->player_limit*256);
                }
    }
}

int main(void)
{
    assert(mf_encounter_config_valid());
    assert(MF_ENCOUNTER_COUNT==4);
    complete_street(0);
    complete_street(1);
    check_menu_and_population();
    check_empty_gate_spawn();
    puts("PASS P1: four encounter quotas, gates, exact credit, spawn cutoff, solo/co-op, checkpoints, vehicle, Bruce and pause handoff");
}
