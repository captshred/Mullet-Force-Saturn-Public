#ifndef MF_DEV_STAGE_SKIP_H
#define MF_DEV_STAGE_SKIP_H
#ifndef MF_DEV_STAGE_SKIP
#define MF_DEV_STAGE_SKIP 0
#endif
#if MF_LEVEL2_WINGSUIT && MF_LEVEL1_STAGE_CLEAR
static void mf_dev_stage_skip(mf_game *g,const unsigned pressed[2])
{
#if MF_DEV_STAGE_SKIP
    if(g->started && !g->paused && g->stage==MF_STAGE_LEVEL1 && ((pressed[0]|pressed[1])&MF_X)){
        g->stage=MF_STAGE_SETTLING;g->stage_timer=1;g->hitstop=0;
    }
#else
    (void)g;(void)pressed;
#endif
}
#endif
#endif
