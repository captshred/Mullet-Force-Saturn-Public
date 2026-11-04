#ifndef MF_ARCADE_FX_H
#define MF_ARCADE_FX_H
#include "game.h"
#include "arcade_fx_config.h"

/* Presentation state only. The simulation and mf_game ABI stay unchanged.
   player_hits resolves players in order, then drums before enemies. New hit-mask
   bits identify the last impact even when a KO and a prop break share a tick.
   Keep that classification through hit-stop, pause and render catch-up. */
static inline int mf_fx_spark_explosion(const mf_game *g,
                                      const unsigned previous[MF_PLAYERS], int current)
{
#if MF_ARCADE_FX
    int a,i,result=0;
    if(!(g->events&MF_IMPACT))return current;
    for(a=0;a<MF_PLAYERS;a++) {
        unsigned hits=(unsigned)g->players[a].hit_mask&~previous[a];
        for(i=0;i<MF_DRUMS;i++)if(hits&(1u<<i))result=!g->drums[i].hp;
        for(i=0;i<MF_ENEMIES;i++)if(hits&(1u<<(MF_DRUMS+i)))result=0;
    }
    return result;
#else
    (void)g;(void)previous;(void)current;return 0;
#endif
}

static inline void mf_fx_draw_drum(const mf_drum *d,int impact,int explosion,
                                   int x,int y,int depth)
{
#if MF_ARCADE_FX
    int sprite=d->hp?impact:explosion;
#else
    int sprite=impact;(void)explosion;
#endif
    if(d->flash || (!d->hp && d->respawn<12))
        jo_sprite_draw3D2(sprite,x-16,y-40,depth-1);
}

static inline void mf_fx_draw_spark(const mf_game *g,int impact,int explosion,
                                    int is_explosion,int depth)
{
#if MF_ARCADE_FX
    int sprite=is_explosion?explosion:impact;
#else
    int sprite=impact;(void)explosion;(void)is_explosion;
#endif
    if(g->spark)jo_sprite_draw3D2(sprite,g->spark_x-g->camera-16,
                                g->spark_y-g->spark_z-16,depth);
}
#endif
