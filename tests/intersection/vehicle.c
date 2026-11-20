#include <assert.h>
#include <stdio.h>
#include "game.c"

int main(void)
{
#if MF_VEHICLE_AMBUSH
    mf_game g;
    int directions=0, warnings=0, last=0, passes=0;
    mf_game_init(&g);
    g.started=1;
    g.camera=2080;
    g.players[0].x=(MF_VEHICLE_TRIGGER_X-1)*256;
    vehicle_step(&g);
    assert(!g.vehicle_tick);
    g.players[0].x=MF_VEHICLE_TRIGGER_X*256;
    recover_player(&g,1,1);
    g.players[1].x=g.players[0].x;
    g.players[0].y=g.players[1].y=MF_VEHICLE_LANE*256;
    g.players[0].invulnerable=g.players[1].invulnerable=0;
    g.players[1].height=24*256;
    for(int i=0;i<MF_ENEMIES;i++){
        g.enemies[i]=(mf_enemy){.x=g.players[0].x,.y=MF_VEHICLE_LANE*256,
                               .hp=MF_ENEMY_MAX_HP,.state=MF_ENEMY_ACTIVE};
    }
    g.enemies[2].y=229*256;
    for(int t=0;t<=VEHICLE_END;t++){
        g.events=0;
        vehicle_step(&g);
        warnings+=(g.events&MF_VEHICLE_WARNING)!=0;
        if(g.vehicle_dir && g.vehicle_dir!=last)passes++;
        last=g.vehicle_dir;
        directions|=g.vehicle_dir==1?1:g.vehicle_dir==-1?2:0;
        if(t==VEHICLE_WARN+VEHICLE_FIRST){
            assert(g.players[0].health==50 && g.players[0].knockback>0);
            assert(g.players[1].health==100);
            g.players[0].invulnerable=0;
            g.players[0].y=168*256;
            g.players[1].height=0;
        }
    }
    assert(g.enemies[0].state==MF_ENEMY_DYING && g.enemies[1].state==MF_ENEMY_DYING);
    assert(g.enemies[2].hp==MF_ENEMY_MAX_HP && !g.stage_kills && !g.score);
    assert(passes==2 && directions==3 && warnings==2);
    assert(g.players[0].health==50 && g.players[1].health==50);
    assert(g.players[1].knockback<0 && !g.vehicle_dir);
    vehicle_step(&g);
    assert(g.vehicle_tick==VEHICLE_END+1);

    /* Chuck solo, invulnerability and lethal contact. */
    g.players[0].active=0;
    g.players[1].health=20;
    g.vehicle_tick=VEHICLE_WARN;
    g.players[1].x=(g.vehicle_camera-100)*256;
    g.players[1].invulnerable=10;
    g.vehicle_hits=0;
    vehicle_step(&g);
    assert(g.players[1].health==20 && !g.vehicle_hits);
    g.players[1].invulnerable=0;
    vehicle_step(&g);
    assert(!g.players[1].health && g.players[1].defeated && g.vehicle_hits==2);
    while(g.vehicle_tick<=VEHICLE_END)vehicle_step(&g);
    assert(!g.vehicle_dir);

    /* Stage handoff cancels a live pass, while a new game rearms it. */
    g.vehicle_dir=1;
    g.stage=MF_STAGE_LEVEL2_ENTRY;
    mf_game_step(&g,0,0);
    assert(!g.vehicle_dir && g.vehicle_tick>VEHICLE_END);
    mf_game_init(&g);
    assert(!g.vehicle_tick && !g.vehicle_dir);
    puts("PASS vehicle warning, two passes, lane/jump avoidance, independent hits, invulnerability, lethal hit, stage transition and reset");
#endif
    return 0;
}
