#include "build-info.h"
#include "ricky_animation.h"
#if MF_RICKY_ENEMY
#include "ricky_data.h"
static int ids[MF_RICKY_DEFS],resident;
static jo_palette *colors,*burn_colors;
static unsigned color_hash;
static unsigned hash(void) {
    unsigned i,h=2166136261u;
    if(!colors || !colors->data || !burn_colors || !burn_colors->data)return 0;
    for(i=0;i<255;i++){h=(h^colors->data[i])*16777619u;h=(h^burn_colors->data[i])*16777619u;}
    return h;
}
int mf_ricky_palette(jo_palette *p,jo_palette *burn) {
    unsigned i;
    if(colors || !p || p->id!=2 || !p->data || !burn || burn->id!=3 || !burn->data)return 0;
    colors=p;for(i=0;i<255;i++)p->data[i]=mf_ricky_colors[i];
    /* Reclaim dormant legacy Chuck slot 3; no palette allocation or base writes
       after boot. Exact corporate punk RGB555 warm-red transformation. */
    burn_colors=burn;
    for(i=0;i<255;i++) {
        unsigned c=p->data[i];unsigned r=(c&31)+10,g=((c>>5)&31)+3,b=((c>>10)&31)/2;
        if(r>31)r=31;
        if(g>31)g=31;
        burn->data[i]=0x8000|r|(g<<5)|(b<<10);
    }
    color_hash=hash();return 1;
}
static void invalidate(void) {
    int i;resident=0;for(i=0;i<MF_RICKY_DEFS;i++)ids[i]=-1;
    mf_corporate_bank_spec.invalidate();
}
static int install(jo_palette *p) {
    int i,id;char name[]="RK00.TGA";
    if(hash()!=color_hash || !colors || !mf_corporate_bank_spec.install(p))return 0;
    jo_set_tga_default_palette(JO_NULL); /* Palette 2 is installed once, never during a swap. */
    for(i=0;i<MF_RICKY_DEFS;i++) {
        name[2]='0'+i/10;name[3]='0'+i%10;
        id=jo_sprite_add_tga("RICKY",name,1);ids[i]=id;
        if(id<0 || jo_sprite_get_width(id)!=mf_ricky_frames[i].width ||
           jo_sprite_get_height(id)!=mf_ricky_frames[i].height)return 0;
    }
    resident=1;return 1;
}
static int validate(int first) {
    int i,id;unsigned end=0x10000u+MF_ENEMY_PREFIX_BYTES+MF_ENEMY_CP_BYTES;
    if(!resident || hash()!=color_hash || !mf_corporate_bank_spec.validate(first))return 0;
    for(i=0;i<MF_RICKY_DEFS;i++) {
        const mf_ricky_frame *f=&mf_ricky_frames[i];id=ids[i];
        if(id!=first+MF_ENEMY_CP_DEFS+i || jo_sprite_get_width(id)!=f->width ||
           jo_sprite_get_height(id)!=f->height || __jo_sprite_pic[id].color_mode!=COL_256 ||
           (unsigned long)jo_sprite_get_raw_data(id)-JO_VDP1_VRAM!=end)return 0;
        end+=(f->width*f->height+31u)&~31u;
    }
    return end==0x10000u+MF_ENEMY_PREFIX_BYTES+MF_ENEMY_CP_BYTES+MF_RICKY_BYTES &&
           end+49152u<=0x10000u+458488u;
}
const mf_enemy_bank_spec mf_ricky_bank_spec={2,MF_ENEMY_CP_DEFS+MF_RICKY_DEFS,
    MF_ENEMY_CP_BYTES+MF_RICKY_BYTES,install,invalidate,validate};
int mf_ricky_pose(const mf_game *g,int a) {
    const mf_enemy *e=&g->enemies[a];
    switch(e->state) {
    case MF_ENEMY_IDLE:return (unsigned)g->ticks/12%3;
    case MF_ENEMY_WALK:return 3+(unsigned)e->walk/6%6;
    case MF_ENEMY_WINDUP:return g->ricky_punch[a]?(e->timer>5?9:10):
        (e->timer>14?12:e->timer>6?13:14);
    case MF_ENEMY_ACTIVE:return g->ricky_punch[a]?10:15;
    case MF_ENEMY_RECOVER:return g->ricky_punch[a]?11:12;
    case MF_ENEMY_HURT:return e->timer>9?18:19;
    case MF_ENEMY_DYING:return e->timer>20?20:e->timer>10?21:22;
    default:return -1;
    }
}
static int draw_pose(int pose,int facing,int x,int ground,int depth,int palette) {
    const mf_ricky_frame *f;
    if(!resident || !mf_enemy_bank_ready() || pose<0 || pose>=MF_RICKY_DEFS)return 0;
    f=&mf_ricky_frames[pose];jo_sprite_set_palette(palette);
    jo_sprite_draw3D2(ids[pose],x-(facing>0?f->ax:f->width-f->ax),ground-f->ay,depth);
    return 1;
}
int mf_ricky_draw_pose(int pose,int facing,int x,int ground,int depth) {
    return draw_pose(pose,facing,x,ground,depth,2);
}
int mf_ricky_draw(const mf_game *g,int a,int x,int ground,int depth) {
    return draw_pose(mf_ricky_pose(g,a),g->enemies[a].facing,x,ground,depth,g->enemies[a].fire_flash?3:2);
}
#endif
