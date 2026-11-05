#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/game.c"
#include "dev_stage_skip.h"
int main(void)
{
    mf_game g,copy;unsigned edge[2]={MF_X,0},held[2]={MF_X,0},zero[2]={0,0};int i;
    mf_game_init(&g);copy=g;mf_dev_stage_skip(&g,edge);assert(!memcmp(&g,&copy,sizeof(g)));
    g.started=1;g.paused=1;copy=g;mf_dev_stage_skip(&g,edge);assert(!memcmp(&g,&copy,sizeof(g)));
    g.paused=0;g.stage_kills=7;copy=g;mf_dev_stage_skip(&g,zero);assert(!memcmp(&g,&copy,sizeof(g)));
    mf_dev_stage_skip(&g,edge);
#if MF_DEV_STAGE_SKIP
    assert(g.stage==MF_STAGE_SETTLING && g.stage_timer==1 && g.stage_kills==7);
    mf_game_step_inputs(&g,held,zero,1);assert(g.stage==MF_STAGE_CLEAR);
    for(i=0;i<MF_STAGE_CLEAR_TICKS;i++){
        copy=g;mf_dev_stage_skip(&g,edge);assert(!memcmp(&g,&copy,sizeof(g)));
        mf_game_step_inputs(&g,held,zero,1);
    }
    assert(g.stage==MF_STAGE_LEVEL2_ENTRY && g.stage_kills==7);
    copy=g;mf_dev_stage_skip(&g,edge);assert(!memcmp(&g,&copy,sizeof(g)));
    mf_game_init(&g);g.started=1;edge[0]=0;edge[1]=MF_X;mf_dev_stage_skip(&g,edge);
    assert(g.stage==MF_STAGE_SETTLING);
#else
    (void)i;(void)held;assert(!memcmp(&g,&copy,sizeof(g)));
#endif
    puts("PASS Saturn X dev skip: title/pause guards, pressed edge only, normal settling/clear/entry transition; release configuration compiles shortcut out");
}
