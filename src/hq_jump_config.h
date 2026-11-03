#ifndef MF_HQ_JUMP_CONFIG_H
#define MF_HQ_JUMP_CONFIG_H
#ifndef MF_HQ_JUMP
#define MF_HQ_JUMP 0
#endif
#define MF_HJ_REPLACED (MF_HQ_JUMP ? 22784u : 0u)
#define MF_HJ_TAKEOFF_VZ 1362
#define MF_HJ_APEX_VZ 296
#if MF_HQ_JUMP
#include "game.h"
/* Presentation only: no clocks, input, writes, physics or collision changes. */
static inline int mf_hq_jump_phase(const mf_player *p)
{
    if(!p->active || !p->health || p->hurt || p->torch || p->bat)return 0;
    if(p->height || p->vz){
        if(p->attack && p->attack>=3 && p->attack<=15)return 6;
        if(p->vz>=MF_HJ_TAKEOFF_VZ)return 1;
        if(p->vz<=MF_HJ_APEX_VZ && p->vz>=-MF_HJ_APEX_VZ)return 3;
        return p->vz>0?2:4;
    }
    return p->landing && !p->attack?5:0;
}
#endif
#endif
