#include "build-info.h"
#if MF_CORPORATE_PUNK
#include "corporate_animation.h"
#include "corporate_bank.h"
static int cp_ids[MF_CP_RESOURCES];
#if MF_CP_HQ_COMBAT
static int cphq_ids[MF_CPHQ_NEW];
#endif
static unsigned cp_idle[MF_ENEMIES];
static int cp_last_state[MF_ENEMIES];
int mf_corporate_load(jo_palette *palette)
{
    int r;
    jo_set_tga_default_palette(palette);
    for(r=0;r<MF_CP_RESOURCES;r++) {
        int id=jo_sprite_add_tga(JO_ROOT_DIR,cp_resources[r].name,1);
        if(id<0 || jo_sprite_get_width(id)!=cp_resources[r].width ||
           jo_sprite_get_height(id)!=cp_resources[r].height ||
           (unsigned long)jo_sprite_get_raw_data(id)-JO_VDP1_VRAM+
            ((cp_resources[r].width*cp_resources[r].height+31u)&~31u)>0x7fef8u) {
            jo_set_tga_default_palette(JO_NULL);return 0;
        }
        cp_ids[r]=id;
    }
#if MF_CP_HQ_COMBAT
    for(r=0;r<MF_CPHQ_NEW;r++) {
        int id=jo_sprite_add_tga(JO_ROOT_DIR,cphq_resources[r].name,1);
        if(id<0 || jo_sprite_get_width(id)!=cphq_resources[r].width ||
           jo_sprite_get_height(id)!=cphq_resources[r].height ||
           (unsigned long)jo_sprite_get_raw_data(id)-JO_VDP1_VRAM+
            ((cphq_resources[r].width*cphq_resources[r].height+31u)&~31u)>0x7fef8u) {
            jo_set_tga_default_palette(JO_NULL);return 0;
        }
        cphq_ids[r]=id;
    }
#endif
    jo_set_tga_default_palette(JO_NULL);return 1;
}
void mf_corporate_step(const mf_game *g)
{
    int a;
    for(a=0;a<MF_ENEMIES;a++) {
        int state=g->enemies[a].state;
        if(state==MF_ENEMY_IDLE && cp_last_state[a]==MF_ENEMY_IDLE)cp_idle[a]=(cp_idle[a]+1)%54;
        else cp_idle[a]=0;
        cp_last_state[a]=state;
    }
}
int mf_corporate_pose(const mf_game *g,int actor)
{
    const mf_enemy *e;
    if(actor<0 || actor>=MF_ENEMIES)return -1;
    e=&g->enemies[actor];
    if(e->state==MF_ENEMY_WALK)return 3+(unsigned)e->walk/7%3;
    if(e->state==MF_ENEMY_IDLE)return cp_idle[actor]<24?0:cp_idle[actor]<36?1:2;
#if MF_CP_HQ_COMBAT
    if(e->state==MF_ENEMY_WINDUP)return e->timer>16?0:6;
    if(e->state==MF_ENEMY_ACTIVE)return 7;
    if(e->state==MF_ENEMY_RECOVER){
        if(g->enemy_class[actor]==MF_ENEMY_CORPORATE_PUNK)
            return e->timer==MF_PUNK_ATTACK_RECOVERY+actor*6?7:e->timer>12?6:0;
        return e->timer==MF_ENEMY_RECOVERY_TICKS+actor*12?7:e->timer>28?6:0;
    }
    if(e->state==MF_ENEMY_HURT)return 8;
    if(e->state==MF_ENEMY_DYING)return e->timer>25?8:e->timer>12?9:10;
#endif
    return -1;
}
int mf_corporate_draw(const mf_game *g,int actor,int x,int ground,int depth)
{
    int f=mf_corporate_pose(g,actor),p;
    if(f<0)return 0;
#if MF_CP_HQ_COMBAT
    if(f>=8) {
        const mf_cp_piece *v=&cphq_full[f-8];
        int left=g->enemies[actor].facing>0?x-48+v->x:x+48-v->x-v->width;
        jo_sprite_draw3D2(cphq_ids[v->resource-10],left,ground-92+v->y,depth);
        return 1;
    }
#endif
    for(p=0;p<MF_CP_PARTS;p++) {
        const mf_cp_piece *v=&cp_poses[f<6?f:0][p];
#if MF_CP_HQ_COMBAT
        mf_cp_piece adjusted;
        if(f==7 && p==1)v=&cphq_strike_upper;
        if(f==6 && p<2){adjusted=*v;adjusted.x--;v=&adjusted;}
#endif
        int left=g->enemies[actor].facing>0?x-48+v->x:x+48-v->x-v->width;
#if MF_CP_HQ_COMBAT
        if(v->resource>=10)jo_sprite_draw3D2(cphq_ids[v->resource-10],left,ground-92+v->y,depth);
        else
#endif
        jo_sprite_draw3D2(cp_ids[v->resource],left,ground-92+v->y,depth);
    }
    return 1;
}
#endif
