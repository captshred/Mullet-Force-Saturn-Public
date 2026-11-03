#include "build-info.h"
#if MF_PLAYABLE_ANIMATION
#include <jo/jo.h>
#include "player_animation.h"
#include "animation_preview.h"
/* RBV BEGIN */
#include "running_bat_visual_config.h"
#if MF_RUNNING_BAT_VISUALS
static int rbv_last_pose[MF_PLAYERS]={18,18};
#endif
/* RBV END */
#if MF_ORIGINAL_THREE_WALK
#include "original_three_timing.h"
#elif MF_SWAGGER_WALK
#include "swagger_timing.h"
#endif
/* Small per-player clocks only; all texture IDs belong to the existing loader. */
static unsigned idle_ticks[MF_PLAYERS];
static int last_mode[MF_PLAYERS];
static const unsigned holds[2][4]={{24,16,24,16},{30,18,24,18}};
static int mode(const mf_player *p)
{
    if(!p->active || !p->health || p->hurt || p->attack || p->height || p->vz || p->landing || p->torch)return 0;
    return p->moving?2:1;
}
void mf_player_animation_step(const mf_game *g)
{
    int a;
    for(a=0;a<MF_PLAYERS;a++) {
        int m=mode(&g->players[a]);
/* RBV BEGIN */
#if MF_RUNNING_BAT_VISUALS
        if(g->dash[a].dir)rbv_last_pose[a]=18+(unsigned)g->dash[a].anim/(MF_RUN_FRAME_HOLD*MF_DASH_ANIM_NUM);
#endif
/* RBV END */
        if(m==1 && last_mode[a]==1)idle_ticks[a]=(idle_ticks[a]+1)%(a?90u:80u);
        else idle_ticks[a]=0;
        last_mode[a]=m;
    }
}
int mf_player_animation_pose(const mf_game *g,int actor)
{
    unsigned t;int f,m;
    if(actor<0 || actor>=MF_PLAYERS)return -1;
    m=mode(&g->players[actor]);
    if(!m)return -1;
    /* Walk presentation is separate from movement/combat. The swagger and
       six-pose variants share roots/resources, not animation state. */
    if(m==2) {
#if MF_DASH_ENABLED
#if MF_RUN_BAT
        if(g->dash[actor].dir)return 18+((unsigned)g->dash[actor].anim/(MF_RUN_FRAME_HOLD*MF_DASH_ANIM_NUM))%4;
#endif
        if(g->dash[actor].dir)return 15+(unsigned)g->dash[actor].anim/(MF_DASH_BASE_HOLD*MF_DASH_ANIM_DEN);
#endif
#if MF_ORIGINAL_THREE_WALK
        return 15+((unsigned)g->players[actor].walk/(unsigned)MF_ORIGINAL_FRAME_HOLD)%3;
#elif MF_SWAGGER_WALK
        static const unsigned swagger_holds[2][3]={MF_SWAGGER_BUCK_HOLDS,MF_SWAGGER_CHUCK_HOLDS};
        const unsigned *v=swagger_holds[actor];
        unsigned tick=(unsigned)g->players[actor].walk%(v[0]+v[1]+v[2]);
        if(tick<v[0])return 12;
        if(tick<v[0]+v[1])return 13;
        return 14;
#else
        return 4+((g->players[actor].walk%40)*3)/20;
#endif
    }
    t=idle_ticks[actor];
    for(f=0;f<3;f++){if(t<holds[actor][f])return f;t-=holds[actor][f];}
    return 3;
}
int mf_player_animation_draw(const mf_game *g,int actor,int x,int ground,int depth)
{
/* RBV BEGIN */
#if MF_RUNNING_BAT_VISUALS
    if(actor>=0 && actor<MF_PLAYERS && g->running_bat[actor].active && g->players[actor].attack>0 && g->players[actor].attack<6 && g->players[actor].health && !g->players[actor].hurt && !g->players[actor].height && !g->players[actor].vz)
        return mf_animation_draw_actor(actor,rbv_last_pose[actor],x,ground,g->players[actor].facing,depth);
#endif
/* RBV END */
    int f=mf_player_animation_pose(g,actor);
    if(f<0)return 0;
    return mf_animation_draw_actor(actor,f,x,ground,g->players[actor].facing,depth);
}
#endif
