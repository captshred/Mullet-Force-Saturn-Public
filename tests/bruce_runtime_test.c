#include "bruce.h"
#include <assert.h>
#include <stdio.h>

static void tick(mf_bruce *bruce, const mf_game *game, int count)
{
    while (count-- > 0) mf_bruce_step(bruce,game);
}

static void verify_entrance_events(void)
{
    mf_game game = {0};
    int launches=0, landings=0;
    game.started=1;
    game.camera=2700;
    game.street_spawns_suspended=1;
    game.bruce.ready=1;
    for(int frame=0;frame<80;frame++) {
        mf_game_step(&game,0,0);
        if(game.events&MF_BRUCE_ENTRANCE_JUMP) {
            assert(game.bruce.state==MF_BRUCE_ENTRANCE && frame==0);
            ++launches;
        }
        if(game.events&MF_BRUCE_SFX_LAND) {
            assert(frame==48 && game.bruce.state==MF_BRUCE_ENTRANCE_IMPACT && !game.bruce.height);
            ++landings;
        }
    }
    assert(launches==1 && landings==1 && game.bruce.state==MF_BRUCE_READY);
}

static void verify_game_dispatch(void)
{
    mf_game game = {0};
    mf_bruce *bruce = &game.bruce;
    int i;
    game.started = 1;
    game.camera = 2700;
    game.street_spawns_suspended = 1;
    bruce->active = bruce->ready = 1;
    bruce->health = 30;
    bruce->x = 2840 * 256;
    bruce->y = 200 * 256;
    bruce->facing = -1;
    bruce->state = MF_BRUCE_PUNCH;
    bruce->timer = 25;
    for(i=0;i<MF_PLAYERS;i++) {
        game.players[i].active = 1;
        game.players[i].health = 100;
        game.players[i].x = bruce->x - (28+i*8)*256;
        game.players[i].y = bruce->y;
    }
    mf_game_step(&game,0,0);
    assert(bruce->hit_players == 3);
    assert(game.players[0].health == 76 && game.players[1].health == 76);
    game.players[0].invulnerable = game.players[1].invulnerable = 0;
    game.hitstop = 0;
    mf_game_step(&game,0,0);
    assert(game.players[0].health == 76 && game.players[1].health == 76);

    /* A real player bat contact routes damage into Bruce's private HP. */
    game.players[1].active = 0;
    game.players[0].hurt = game.players[0].knockback = 0;
    game.players[0].x = bruce->x - 36*256;
    game.players[0].y = bruce->y;
    game.players[0].facing = 1;
    game.players[0].bat = 1;
    game.players[0].attack = MF_BAT_ACTIVE_FIRST;
    bruce->state = MF_BRUCE_READY;
    bruce->cooldown = 24;
    mf_game_step(&game,0,0);
    assert(bruce->health == 27 && bruce->state == MF_BRUCE_FALL);
}

static void verify_bat_interruptions(void)
{
    int slot, slam;
    for(slot=0;slot<MF_PLAYERS;++slot) for(slam=0;slam<2;++slam) {
        mf_game g = {0};
        mf_bruce *b = &g.bruce;
        mf_player *p = &g.players[slot];
        int x = 2910*256, y = 203*256;
        g.started = g.street_spawns_suspended = 1;
        g.camera = 2740;
        *b = (mf_bruce){.active=1,.ready=1,.health=60,.facing=-1,.x=x,.y=y,
            .state=slam?MF_BRUCE_SLAM:MF_BRUCE_CHARGE,.timer=slam?49:26,.height=slam?5:0,
            .start_x=x+100*256,.land_x=x-3*256,.slam_start_y=y,.slam_land_y=y};
        g.players[0] = (mf_player){.active=1,.health=100,.x=x-36*256,.y=y,.facing=1};
        if(slot) *p = g.players[0];
        p->bat = 1; p->attack = MF_BAT_ACTIVE_FIRST;
        mf_game_step(&g,0,0);
        assert(b->health == 57 && b->state == MF_BRUCE_HURT);
        assert(b->x == x && b->y == y && !b->impact && !b->hit_players);
        assert(p->health == 100 && g.players[0].health == 100);
        assert(mf_bruce_pose(b)==13 && !mf_bruce_strike(b,p));
        for(int i=0;i<18;++i) {
            mf_game_step(&g,0,0);
            assert(!(g.events&MF_BRUCE_SFX_LAND));
        }
        assert(b->health == 57 && p->health == 100);
    }

    mf_game g = {0};
    mf_bruce b = {.active=1,.ready=1,.health=60,.state=MF_BRUCE_SLAM,.timer=34,
                   .height=44,.x=2910*256,.y=203*256};
    int x=b.x, y=b.y;
    mf_bruce_receive(&b,1,0,1);
    assert(b.health==59 && b.state==MF_BRUCE_SLAM);
    b.invulnerable=0;
    mf_bruce_receive(&b,3,1,1);
    assert(b.health==56 && b.state==MF_BRUCE_HURT && b.height==44);
    for(int i=0;i<9;++i) {
        assert(b.x==x && b.y==y && b.height>0 && !b.impact);
        mf_bruce_step(&b,&g);
    }
    assert(!b.height && mf_bruce_pose(&b)==13);
    tick(&b,&g,6);
    assert(mf_bruce_pose(&b)==14);
    tick(&b,&g,9);
    assert(mf_bruce_pose(&b)==8);
    tick(&b,&g,8);
    assert(b.state==MF_BRUCE_READY && b.cooldown==18 && !b.invulnerable);

    b.health=3; b.state=MF_BRUCE_SLAM; b.timer=34; b.height=44;
    mf_bruce_receive(&b,3,1,1);
    assert(b.health==0 && b.state==MF_BRUCE_HURT && b.height==44);
    tick(&b,&g,9);
    assert(!b.height && b.state==MF_BRUCE_FALL);
    tick(&b,&g,14);
    assert(b.state==MF_BRUCE_DEFEATED && !b.impact);
}

static void verify_slam_lunge(void)
{
    mf_game game = {0};
    mf_bruce bruce = {0};
    mf_player *buck = &game.players[0], *chuck = &game.players[1];
    int direction;
    for(direction=-1;direction<=1;direction+=2) {
        bruce = (mf_bruce){.active=1,.ready=1,.health=30,.state=MF_BRUCE_READY,
                           .x=2910*256,.y=201*256,.target=0,.retarget=10,.attack_cycle=2};
        *buck = (mf_player){.active=1,.health=100,.x=(2910+direction*135)*256,.y=199*256};
        *chuck = (mf_player){.active=1,.health=100,.x=(2910+direction*108)*256,.y=231*256};
        mf_bruce_step(&bruce,&game);
        assert(bruce.state == MF_BRUCE_SLAM && bruce.target == 1 && bruce.facing == direction);
        assert(bruce.land_x == (2910+direction*108)*256 && bruce.slam_land_y == 229*256);
        /* Retain the target even if it moves, then leaves the encounter. */
        chuck->x = 2910*256;
        chuck->y = 168*256;
        chuck->active = 0;
        tick(&bruce,&game,17);
        assert(bruce.x == 2910*256 && bruce.y == 201*256 && mf_bruce_pose(&bruce) == 11);
        tick(&bruce,&game,17);
        assert(bruce.x == (2910+direction*54)*256 && bruce.y == 215*256);
        assert(bruce.height == 55 && mf_bruce_pose(&bruce) == 9 && !mf_bruce_strike(&bruce,buck));
        tick(&bruce,&game,16);
        assert(bruce.x == bruce.land_x && bruce.y == 229*256 && !bruce.height);
        assert(bruce.impact && mf_bruce_pose(&bruce) == 12);
        assert(!mf_bruce_strike(&bruce,buck)); /* Buck moved outside the landing ellipse. */
        buck->x = bruce.x;
        buck->y = bruce.y;
        assert(mf_bruce_strike(&bruce,buck) == 24);
        buck->height = 18*256;
        assert(!mf_bruce_strike(&bruce,buck));
        buck->height = 0;
        buck->invulnerable = 1;
        assert(!mf_bruce_strike(&bruce,buck));
        buck->invulnerable = 0;
        tick(&bruce,&game,1);
        assert(!mf_bruce_strike(&bruce,buck)); /* Impact hold is visual only. */
        tick(&bruce,&game,7);
        assert(mf_bruce_pose(&bruce) == 8);
        tick(&bruce,&game,8);
        assert(bruce.state == MF_BRUCE_READY && bruce.cooldown == 30);
    }
}


static void verify_counter(int coop)
{
    mf_game g = {0};
    mf_bruce *b = &g.bruce;
    int x = 2910*256, y = 202*256;
    g.started = g.street_spawns_suspended = 1;
    g.camera = 2740;
    g.players[0] = (mf_player){.active=1,.health=100,.x=x-24*256,.y=y,.facing=1};
    g.players[1] = (mf_player){.active=coop,.health=100,.x=x+25*256,.y=y,.facing=-1};
    *b = (mf_bruce){.active=1,.ready=1,.health=75,.state=MF_BRUCE_READY,.x=x,.y=y,.target=-1};

    /* Same boss pressure record regardless of which player lands the jab. */
    for (int hit=0; hit<3; ++hit) {
        mf_player *p=&g.players[coop && (hit&1)];
        p->attack=6;
        p->hit_mask=0;
        mf_game_step(&g,0,0);
        assert(b->health==74-hit);
        if (hit<2) {
            assert(b->state==MF_BRUCE_HURT && b->pressure_hits==hit+1);
            for (int frame=0; frame<20; ++frame) mf_game_step(&g,0,0);
        }
    }
    assert(b->state==MF_BRUCE_COUNTER && mf_bruce_pose(b)==11);
#if MF_VEHICLE_AMBUSH
    assert(g.events&MF_BRUCE_SFX_JUMP);
#endif
    assert(b->counter_cooldown==MF_BRUCE_COUNTER_COOLDOWN);
    assert(!mf_bruce_strike(b,&g.players[0]));
    tick(b,&g,MF_BRUCE_COUNTER_WINDUP-1);
    mf_bruce_receive(b,1,0,1); /* Ordinary hit during the windup. */
    assert(b->health==71 && b->state==MF_BRUCE_COUNTER && b->timer==19);
    g.players[0].x=x-47*256;g.players[0].y=y+12*256;
    g.players[1].x=x+68*256;
    tick(b,&g,1);
    assert(b->land_x==g.players[0].x && b->slam_land_y==g.players[0].y);
    assert(b->x==x && b->y==y && mf_bruce_pose(b)==9);
    g.players[0].x=x-112*256;
    tick(b,&g,MF_BRUCE_COUNTER_AIR/2);
    assert(b->height==60 && b->land_x==x-47*256);
    mf_bruce_receive(b,2,0,-1); /* Flame/light contact in the arc. */
    assert(b->health==69 && b->state==MF_BRUCE_COUNTER && b->height==60);
    mf_game landing=g;
    landing.hitstop=0;
    landing.players[0].active=landing.players[1].active=0;
    for(int i=1;i<=MF_BRUCE_COUNTER_AIR/2+1;++i) {
        mf_game_step(&landing,0,0);
        assert(!!(landing.events&MF_BRUCE_SFX_LAND)==(i==MF_BRUCE_COUNTER_AIR/2));
    }
    tick(b,&g,MF_BRUCE_COUNTER_AIR/2);
    assert(b->x==b->land_x && b->y==b->slam_land_y && !b->height && mf_bruce_pose(b)==12);
    assert(!mf_bruce_strike(b,&g.players[0]));
    g.players[0].x=b->x;g.players[0].y=b->y;
    assert(mf_bruce_strike(b,&g.players[0])==24);
    g.players[0].height=18*256;
    assert(!mf_bruce_strike(b,&g.players[0]));
    g.players[0].height=0;
    tick(b,&g,1);
    assert(b->state==MF_BRUCE_COUNTER_RECOVERY && !mf_bruce_strike(b,&g.players[0]));
    mf_bruce_receive(b,3,1,1);
    assert(b->health==66 && b->state==MF_BRUCE_FALL);
    assert(b->counter_cooldown>0);
}

static void verify_torch_pressure(void)
{
    mf_game g={0};
    mf_bruce *b=&g.bruce;
    g.started=g.street_spawns_suspended=1;
    g.camera=2740;
    g.players[0]=(mf_player){.active=1,.health=100,.x=2850*256,.y=202*256,
                            .facing=1,.torch=MF_TORCH_FIRE};
    *b=(mf_bruce){.active=1,.ready=1,.health=75,.state=MF_BRUCE_READY,
                  .x=2910*256,.y=202*256,.target=-1,.cooldown=24};
    for(int frame=0;frame<50 && b->state!=MF_BRUCE_COUNTER;++frame)
        mf_game_step_coop(&g,(unsigned[2]){MF_A,0},(unsigned[2]){0,0});
    assert(b->health==75-3*MF_TORCH_DAMAGE && b->state==MF_BRUCE_COUNTER);
    for(int frame=0;frame<20;++frame)
        mf_game_step_coop(&g,(unsigned[2]){MF_A,0},(unsigned[2]){0,0});
    assert(b->state==MF_BRUCE_COUNTER && b->timer==20 && b->health<75-3*MF_TORCH_DAMAGE);
}

static void verify_counter_vulnerability_and_pursuit(void)
{
    mf_game g={0};
    mf_bruce b={.active=1,.ready=1,.health=75,.state=MF_BRUCE_COUNTER,.timer=19,
                .x=3000*256,.y=170*256,.counter_cooldown=130,.target=-1};
    g.players[0]=(mf_player){.active=1,.health=100,.x=3060*256,.y=229*256};
    mf_bruce_receive(&b,3,1,-1);
    assert(b.state==MF_BRUCE_HURT && b.health==72 && !b.impact);
    b.state=MF_BRUCE_COUNTER;b.timer=25;b.height=25;b.invulnerable=0;
    mf_bruce_receive(&b,72,0,1);
    assert(b.state==MF_BRUCE_HURT && b.height==25 && b.health==0);
    tick(&b,&g,19);
    assert(b.state==MF_BRUCE_DEFEATED && !b.impact);
    b=(mf_bruce){.active=1,.ready=1,.health=75,.state=MF_BRUCE_READY,
                 .x=3049*256,.y=168*256,.target=-1,.attack_cycle=1};
    tick(&b,&g,80);
    assert(b.x<=3049*256 && b.y>=216*256 && b.y<=229*256 && b.state==MF_BRUCE_PUNCH);
    b.state=MF_BRUCE_PUNCH;b.timer=52;b.health=38;
    tick(&b,&g,1);assert(b.cooldown==26);
    b.state=MF_BRUCE_PUNCH;b.timer=52;b.health=37;
    tick(&b,&g,1);assert(b.cooldown==20);
    b.state=MF_BRUCE_READY;b.cooldown=24;b.counter_cooldown=60;
    for(int hit=0;hit<3;++hit){
        b.invulnerable=0;
        mf_bruce_receive(&b,1,0,1);
        assert(b.state==MF_BRUCE_READY && b.pressure_hits==0);
    }
    b.counter_cooldown=0;b.invulnerable=0;b.pressure_window=1;b.pressure_hits=2;
    tick(&b,&g,1);
    assert(!b.pressure_hits && b.state==MF_BRUCE_READY);
}

#if MF_VEHICLE_AMBUSH
static void verify_bruce_cues(void)
{
    for(int slot=0;slot<MF_PLAYERS;++slot){
        mf_game g={0};
        mf_bruce *b=&g.bruce;
        mf_player *p=&g.players[slot];
        g.started=g.street_spawns_suspended=1;
        g.vehicle_tick=10000;
        g.camera=2740;
        *b=(mf_bruce){.ready=1,.active=1,.health=17,.state=MF_BRUCE_READY,
                    .x=2910*256,.y=203*256,.target=-1,.cooldown=24};
        *p=(mf_player){.active=1,.health=100,.x=b->x-35*256,.y=b->y,.facing=1,
                     .bat=1,.attack=MF_BAT_ACTIVE_FIRST};
        mf_game_step(&g,0,0);
        assert(b->health==14 && (g.events&MF_BRUCE_SFX_HURT) && (g.events&MF_BRUCE_SFX_LAUGH));
        mf_game_step(&g,0,0);
        assert(!(g.events&(MF_BRUCE_SFX_LAUGH|MF_BRUCE_SFX_HURT)));
        g.hitstop=0;b->health=3;b->invulnerable=0;b->state=MF_BRUCE_READY;
        p->hit_mask=0;p->attack=MF_BAT_ACTIVE_FIRST;
        mf_game_step(&g,0,0);
        assert(!b->health && (g.events&MF_BRUCE_SFX_DEATH) &&
               !(g.events&(MF_BRUCE_SFX_LAUGH|MF_BRUCE_SFX_HURT|MF_COMBAT_HUMAN_DEATH(slot))));
    }
    for(int attack=1;attack<=2;++attack){
        mf_game g={0};
        mf_bruce *b=&g.bruce;
        unsigned event=attack==1?MF_BRUCE_SFX_CHARGE:MF_BRUCE_SFX_JUMP;
        g.started=g.street_spawns_suspended=1;
        g.vehicle_tick=10000;
        g.camera=2740;
        *b=(mf_bruce){.ready=1,.active=1,.health=75,.state=MF_BRUCE_READY,
                    .x=2910*256,.y=203*256,.target=-1,.attack_cycle=attack};
        g.players[0]=(mf_player){.active=1,.health=100,.x=b->x-95*256,.y=b->y,.facing=1};
        mf_game_step(&g,0,0);
        assert((g.events&event) && !b->timer);
        for(int i=1;i<=60;++i){
            mf_game_step(&g,0,0);
            assert(!(g.events&event));
            assert(!!(g.events&MF_BRUCE_SFX_LAND)==(attack==2 && i==50));
        }
    }
}
#endif


#if MF_DASH_ENABLED
static void verify_running_jumps(void)
{
    for(int mode=0;mode<3;++mode) {
        mf_game walk={0}, run;
        unsigned held[2]={MF_RIGHT,MF_RIGHT}, jump[2]={MF_B,MF_B}, none[2]={0,0};
        unsigned connected=mode==0?1:3;
        int start[2], peak=0, frames=0;
        walk.started=walk.street_spawns_suspended=1;
        walk.camera=400;
        walk.vehicle_tick=10000;
        for(int i=0;i<2;++i) {
            start[i]=(470+i*35)*256;
            walk.players[i]=(mf_player){.active=mode!=0 || !i,.health=100,.x=start[i],.y=200*256};
        }
        run=walk;
        for(int i=0;i<2;++i)if(mode!=1 || i)run.dash[i].dir=1,run.dash[i].ready=1;
        do {
            mf_game_step_inputs(&walk,held,frames?none:jump,connected);
            mf_game_step_inputs(&run,held,frames?none:jump,connected);
            for(int i=0;i<2;++i)assert(run.players[i].height==walk.players[i].height);
            if(peak<run.players[0].height)peak=run.players[0].height;
            if(!frames) {
                mf_game reverse=run;
                unsigned back[2]={MF_LEFT,MF_LEFT}, kick[2]={MF_A,MF_A};
                mf_game_step_inputs(&reverse,none,none,connected);
                for(int i=0;i<2;++i)assert(reverse.players[i].x==run.players[i].x);
                mf_game_step_inputs(&reverse,back,kick,connected);
                for(int i=0;i<2;++i)if(run.players[i].active) {
                    int speed=(mode!=1 || i)?390*MF_DASH_SPEED_NUM/MF_DASH_SPEED_DEN:390;
                    assert(reverse.players[i].x==run.players[i].x-speed && reverse.players[i].attack_air);
                }
            }
            ++frames;
            assert(frames<=42);
        } while(run.players[0].height);
        assert(frames==42 && peak==16170);
        for(int i=0;i<2;++i)if(run.players[i].active) {
            int speed=(mode!=1 || i)?390*MF_DASH_SPEED_NUM/MF_DASH_SPEED_DEN:390;
            assert(walk.players[i].x-start[i]==390*frames);
            assert(run.players[i].x-start[i]==speed*frames && !run.running_jump[i]);
        }
    }
    puts("PASS solo and co-op running jumps, reversal, neutral, kicks, 42 ticks, unchanged 16170/256 px apex");
}
#endif

static void verify_arena_progression(void)
{
    mf_game game;
    mf_game_init(&game);
    game.started = 1;
    game.camera = MF_BRUCE_CAMERA_MIN;
    game.vehicle_tick = 1000;
    game.players[0].x = MF_BRUCE_LOT_FIRST * 256;
    game.players[1] = game.players[0];
    game.players[1].x = MF_BRUCE_LOT_RETURN * 256;

    assert(mf_bruce_approach(&game.bruce, &game));
    game.bruce.ready = 1;
    mf_game_step(&game, 0, 0);
    assert(game.events & MF_BRUCE_ENTRANCE_JUMP);
    assert(game.bruce.active && game.street_spawns_suspended);
    assert(game.players[1].x == MF_BRUCE_ARENA_REAR * 256);

    /* The bank request remains latched even if a position is outside the lot. */
    game.players[1].x = (MF_BRUCE_LOT_RETURN - 1) * 256;
    assert(mf_bruce_approach(&game.bruce, &game));
    game.camera = MF_BRUCE_CAMERA_MIN;
    game.players[0].hurt = 2;
    game.players[0].knockback = -900;
    mf_game_step_coop(&game, (unsigned[2]){MF_LEFT, MF_LEFT},
                      (unsigned[2]){0, MF_B});
    assert(game.players[0].x == MF_BRUCE_ARENA_REAR * 256);
    assert(game.players[1].x == MF_BRUCE_ARENA_REAR * 256);
    assert(game.players[1].height > 0);

    /* Advance the approved entrance and join at the far side of the arena. */
    mf_game_step_inputs(&game, (unsigned[2]){0}, (unsigned[2]){0}, 1);
    game.players[0].x = MF_BRUCE_ARENA_FRONT * 256;
    game.camera = MF_BRUCE_CAMERA_MAX;
    mf_game_step_coop(&game, (unsigned[2]){0, MF_START},
                      (unsigned[2]){0, MF_START});
    assert(game.players[1].active);
    assert(game.players[1].x >= MF_BRUCE_ARENA_REAR * 256);
    assert(game.players[1].x <= MF_BRUCE_ARENA_FRONT * 256);
    for (int tick = 0; tick < 68; ++tick) mf_game_step(&game, MF_RIGHT, 0);
    assert(game.bruce.state == MF_BRUCE_READY);
    assert(game.players[0].x == MF_BRUCE_ARENA_FRONT * 256);

    mf_bruce_receive(&game.bruce, MF_BRUCE_MAX_HP, 0, 1);
    for (int tick = 0; tick < 13; ++tick) {
        mf_game_step(&game, MF_RIGHT, 0);
        assert(game.bruce.state == MF_BRUCE_FALL);
        assert(game.players[0].x == MF_BRUCE_ARENA_FRONT * 256);
        assert(game.camera <= MF_BRUCE_CAMERA_MAX);
    }
    mf_game_step(&game, MF_RIGHT, 0);
    assert(game.bruce.state == MF_BRUCE_DEFEATED);
    for (int tick = 0; tick < 140; ++tick)
        mf_game_step_inputs(&game, (unsigned[2]){MF_RIGHT}, (unsigned[2]){0}, 1);
    assert(game.players[0].x >= MF_BRUCE_ARCADE_DOORS * 256);
    for (int tick = 0; tick < 550; ++tick) mf_game_step(&game, MF_LEFT, 0);
    assert(game.players[0].x == MF_BRUCE_ARENA_REAR * 256);
    assert(game.camera == MF_BRUCE_CAMERA_MIN);
    assert(game.bruce.state == MF_BRUCE_DEFEATED);
    assert(game.street_spawns_suspended && mf_enemy_count(&game) == 0);
}

int main(void)
{
#if MF_DASH_ENABLED
    verify_running_jumps();
#endif
    mf_game game = {0};
    mf_bruce bruce = {0};
    mf_player *player = &game.players[0];
    int apex = 0, i;

    game.camera = 2620;
    player->active = 1;
    player->health = 100;
    player->x = 2757 * 256;
    player->y = 203 * 256;
    assert(!mf_bruce_approach(&bruce,&game));
    player->x = 2758 * 256;
    assert(mf_bruce_approach(&bruce,&game));
    mf_bruce_step(&bruce,&game);
    assert(!bruce.active);
    bruce.ready = 1;
    mf_bruce_step(&bruce,&game);
    assert(bruce.active && bruce.x / 256 > game.camera + 320 && bruce.facing == -1);
    assert(bruce.health == MF_BRUCE_MAX_HP && MF_BRUCE_MAX_HP == 75 && mf_bruce_pose(&bruce) == 11);
    for(i=0;i<48;i++) {
        assert(!mf_bruce_strike(&bruce,player) && !mf_bruce_vulnerable(&bruce));
        mf_bruce_step(&bruce,&game);
        if(bruce.height > apex) apex = bruce.height;
    }
    assert(apex == 78 && bruce.state == MF_BRUCE_ENTRANCE_IMPACT);
    assert(!bruce.height && bruce.x == bruce.land_x && bruce.impact && mf_bruce_pose(&bruce) == 12);
    tick(&bruce,&game,20);
    assert(bruce.state == MF_BRUCE_READY && bruce.cooldown == 34);

    player->x = bruce.x - 54 * 256;
    player->y = bruce.y;
    tick(&bruce,&game,34);
    assert(bruce.state == MF_BRUCE_PUNCH && !mf_bruce_strike(&bruce,player));
    tick(&bruce,&game,26);
    assert(mf_bruce_strike(&bruce,player) == 24);
    player->y += 13 * 256;
    assert(!mf_bruce_strike(&bruce,player));
    player->y = bruce.y;
    mf_bruce_receive(&bruce,1,0,1);
    assert(bruce.health == 74 && bruce.state == MF_BRUCE_PUNCH);
    mf_bruce_receive(&bruce,1,0,1);
    assert(bruce.health == 74);

    bruce.state = MF_BRUCE_CHARGE;
    bruce.timer = 26;
    i = bruce.x;
    mf_bruce_step(&bruce,&game);
    assert(bruce.x == i - 896);
    player->x = bruce.x - 24 * 256;
    assert(mf_bruce_strike(&bruce,player) == 18);
    player->height = 50 * 256;
    assert(!mf_bruce_strike(&bruce,player));
    player->height = 0;

    tick(&bruce,&game,60);
    assert(bruce.state == MF_BRUCE_READY);
    mf_bruce_receive(&bruce,1,0,1);
    assert(bruce.state == MF_BRUCE_HURT && mf_bruce_pose(&bruce) == 13);
    tick(&bruce,&game,6);
    assert(mf_bruce_pose(&bruce) == 14);
    tick(&bruce,&game,17);
    mf_bruce_receive(&bruce,3,1,1);
    assert(bruce.state == MF_BRUCE_FALL && mf_bruce_pose(&bruce) == 15);
    tick(&bruce,&game,14);
    assert(bruce.state == MF_BRUCE_DOWN && mf_bruce_pose(&bruce) == 17);
    tick(&bruce,&game,22);
    assert(bruce.state == MF_BRUCE_RISE && mf_bruce_pose(&bruce) == 18);
    tick(&bruce,&game,22);

    game.players[1] = *player;
    game.players[1].x = bruce.x + 16 * 256;
    bruce.retarget = 1;
    mf_bruce_step(&bruce,&game);
    assert(bruce.target == 1 && bruce.facing == 1);
    mf_bruce_receive(&bruce,bruce.health,0,-1);
    tick(&bruce,&game,120);
    assert(bruce.state == MF_BRUCE_DEFEATED && mf_bruce_pose(&bruce) == 17);
    game.players[0].x = 2639 * 256;
    assert(mf_bruce_approach(&bruce,&game));
    verify_arena_progression();
    verify_game_dispatch();
    verify_entrance_events();
    verify_bat_interruptions();
    verify_slam_lunge();
    verify_counter(0);
    verify_counter(1);
    verify_counter_vulnerability_and_pursuit();
    verify_torch_pressure();
#if MF_VEHICLE_AMBUSH
    verify_bruce_cues();
#endif
    return 0;
}
