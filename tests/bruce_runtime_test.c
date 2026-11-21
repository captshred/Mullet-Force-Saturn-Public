#include "bruce.h"
#include <assert.h>

static void tick(mf_bruce *bruce, const mf_game *game, int count)
{
    while (count-- > 0) mf_bruce_step(bruce,game);
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
    assert(bruce.health == 30 && mf_bruce_pose(&bruce) == 11);
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
    assert(bruce.health == 29 && bruce.state == MF_BRUCE_PUNCH);
    mf_bruce_receive(&bruce,1,0,1);
    assert(bruce.health == 29);

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

    bruce.state = MF_BRUCE_SLAM;
    bruce.timer = 14;
    tick(&bruce,&game,1);
    assert(bruce.height == 8 && !mf_bruce_strike(&bruce,player));
    tick(&bruce,&game,4);
    assert(!bruce.height && bruce.impact && mf_bruce_strike(&bruce,player) == 24);
    player->y = bruce.y + 24 * 256;
    assert(!mf_bruce_strike(&bruce,player));
    player->y = bruce.y;
    player->invulnerable = 1;
    assert(!mf_bruce_strike(&bruce,player));
    player->invulnerable = 0;

    tick(&bruce,&game,16);
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
    return 0;
}
