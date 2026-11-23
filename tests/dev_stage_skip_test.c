#include <assert.h>
#include <stdio.h>
#include "../src/game.c"
#include "dev_stage_skip.h"

static void step(mf_game *game,unsigned held0,unsigned held1,unsigned edge0,unsigned edge1)
{
    const unsigned held[2]={held0,held1};
    unsigned pressed[2]={edge0,edge1};
    mf_dev_stage_skip(game,pressed);
    if(game->stage==MF_STAGE_LEVEL2_ENTRY)assert(!(pressed[0]&MF_X) && !(pressed[1]&MF_X));
    mf_game_step_inputs(game,held,pressed,3);
}

int main(void)
{
    for(int port=0;port<2;++port){
        mf_game game;
        unsigned x0=port?0:MF_X,x1=port?MF_X:0;
        mf_game_init(&game);
        step(&game,x0,x1,x0,x1);
        assert(!game.started && game.stage==MF_STAGE_LEVEL1);
        step(&game,0,0,MF_START,MF_START);
        assert(game.started && game.players[1].active);
        step(&game,x0,x1,x0,x1);
        assert(!game.paused && game.stage==MF_STAGE_LEVEL1);
        step(&game,x0,x1,MF_START,0);
        assert(game.paused && game.stage==MF_STAGE_LEVEL1);
        int ticks=game.ticks;
        step(&game,x0,x1,0,0);
        assert(game.paused && game.ticks==ticks);
        step(&game,0,0,MF_START,0);
        assert(!game.paused);
        step(&game,x0,x1,MF_START|x0,x1);
        assert(game.paused && game.stage==MF_STAGE_LEVEL1);
        step(&game,0,0,0,0);
        step(&game,x0,x1,x0,x1);
#if MF_DEV_STAGE_SKIP
        assert(!game.paused && game.stage==MF_STAGE_LEVEL2_ENTRY);
        step(&game,x0,x1,0,0);
        assert(!game.paused && game.stage==MF_STAGE_LEVEL2_ENTRY && game.players[1].active);
#else
        assert(game.paused && game.stage==MF_STAGE_LEVEL1);
#endif
    }
    puts("PASS active X ignored, START pause/resume, fresh paused X on either port, held X and simultaneous START+X guarded");
}
