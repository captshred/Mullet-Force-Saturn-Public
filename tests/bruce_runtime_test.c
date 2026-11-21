#include "bruce.h"
#include <assert.h>

int main(void)
{
    mf_game game = {0};
    mf_bruce bruce = {0};
    unsigned poses = 0;
    int i;

    game.players[0].active = 1;
    game.players[0].health = 10;
    game.players[0].x = 2757 * 256;
    game.players[0].y = 180 * 256;
    assert(!mf_bruce_approach(&bruce, &game));
    game.players[0].x = 2758 * 256;
    assert(mf_bruce_approach(&bruce, &game));

    mf_bruce_step(&bruce, &game);
    assert(bruce.active && bruce.x == 3015 * 256 && bruce.y == 203 * 256 && bruce.facing == -1);
    for (i = 0; i < 90; ++i) {
        mf_bruce_step(&bruce, &game);
        poses |= 1u << mf_bruce_pose(&bruce);
    }
    assert(bruce.x < 3015 * 256 && bruce.y < 203 * 256);
    assert(bruce.target == 0 && poses == 28);

    game.players[1] = game.players[0];
    game.players[1].x = bruce.x + 24 * 256;
    game.players[1].y = bruce.y;
    mf_bruce_step(&bruce, &game);
    assert(bruce.target == 0); /* New co-op join waits for the retarget clock. */
    for (i = 0; i < 24; ++i) mf_bruce_step(&bruce, &game);
    assert(bruce.target == 1 && bruce.facing == 1 && !bruce.moving);
    poses = 0;
    for (i = 0; i < 44; ++i) {
        mf_bruce_step(&bruce, &game);
        poses |= 1u << mf_bruce_pose(&bruce);
    }
    assert(poses == 3);
    game.players[1].health = 0;
    mf_bruce_step(&bruce, &game);
    assert(bruce.target == 0 && bruce.facing == -1);
    game.players[0].x = 2639 * 256;
    assert(!mf_bruce_approach(&bruce, &game));
    return 0;
}
