#include "bruce.h"
#include <assert.h>

static void tick(mf_bruce *bruce, const mf_game *game, int count)
{
    while (count-- > 0) mf_bruce_step(bruce,game);
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
        for(int i=0;i<18;++i) mf_game_step(&g,0,0);
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
        assert(bruce.height == 44 && mf_bruce_pose(&bruce) == 9 && !mf_bruce_strike(&bruce,buck));
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
        assert(bruce.state == MF_BRUCE_READY && bruce.cooldown == 38);
    }
}

int main(void)
{
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
    assert(bruce.health == 60 && mf_bruce_pose(&bruce) == 11);
    for(i=0;i<48;i++) {
        assert(!mf_bruce_strike(&bruce,player) && !mf_bruce_vulnerable(&bruce));
        mf_bruce_step(&bruce,&game);
        if(bruce.height > apex) apex = bruce.height;
    }
    assert(apex == 62 && bruce.state == MF_BRUCE_ENTRANCE_IMPACT);
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
    assert(bruce.health == 59 && bruce.state == MF_BRUCE_PUNCH);
    mf_bruce_receive(&bruce,1,0,1);
    assert(bruce.health == 59);

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
    assert(!mf_bruce_approach(&bruce,&game));
    verify_game_dispatch();
    verify_bat_interruptions();
    verify_slam_lunge();
    return 0;
}
