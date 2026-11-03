#ifndef MF_JAB_REPEAT_H
#define MF_JAB_REPEAT_H
#include "jab_config.h"
#if MF_JAB_COHESION
static int mf_jab_repeat_valid(const mf_player *p)
{
    return p->active && p->health && !p->hurt && p->attack && !p->bat &&
        !p->attack_air && !p->height && !p->vz && !p->landing && !p->torch;
}
/* Called even during hit-stop. Capture one fresh physical edge, never a held A.
   Queue age advances only when player_step advances the simulation. */
static void mf_jab_repeat_capture(mf_game *g,int actor,unsigned held,unsigned pressed,int connected)
{
    mf_player *p=&g->players[actor];int fresh=(pressed&MF_A) && !(g->jab[actor].previous&MF_A);
    g->jab[actor].previous=held&MF_A;
    if(!connected || !mf_jab_repeat_valid(p) || g->running_bat[actor].pending || g->running_bat[actor].active || (pressed&MF_B)) {g->jab[actor].buffer=0;return;}
    if(fresh)g->jab[actor].buffer=MF_JAB_BUFFER_TICKS;
}
static int mf_jab_repeat_consume(mf_game *g,int actor)
{
    if(!mf_jab_repeat_valid(&g->players[actor]) || g->running_bat[actor].pending || g->running_bat[actor].active){g->jab[actor].buffer=0;return 0;}
    if(g->jab[actor].buffer>0) {
        int earliest=MF_JAB_REPEAT_COUNTER;
#if MF_PUNCH_COMBO
        if(g->combo[actor].phase==2)earliest+=MF_CROSS_RECOVERY_EXTRA;
#endif
        if(g->players[actor].attack>=earliest){g->jab[actor].buffer=0;return 1;}
        --g->jab[actor].buffer;
    }
    return 0;
}
#endif
#endif
