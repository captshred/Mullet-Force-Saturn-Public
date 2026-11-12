#include "build-info.h"
#include "arcade_fx_config.h"
#if MF_ANIMATION_PREVIEW
#include <jo/jo.h>
#include "input.h"
#include "street.h"
#include "animation_preview.h"
#include "animation_data.h"
#include "animation_polish_data.h"
#include "dash_config.h"
#include "run_bat_config.h"
#include "running_bat_visual_config.h"
#include "combat_animation_config.h"
#include "bat_momentum_config.h"
#include "attack_sequence_config.h"
#include "jab_visual.h"
#include "hq_torch_config.h"
#include "hq_jump_config.h"
#if MF_HQ_JUMP
#include "hq_jump_data.h"
static int hj_ids[MF_HJ_NEW],hj_upper[2],hj_compress_lower[2];
#endif
#if MF_HQ_TORCH
#include "hq_torch_data.h"
#include "original_three_timing.h"
static int ht_ids[MF_HT_NEW],ht_enemy_palette,ht_lower[2][4];
#endif
#if MF_COMBAT_ANIMATION
#include "game.h"
#endif
#if MF_COMBAT_ANIMATION
#if MF_ATTACK_SEQUENCE
#include "attack_sequence_data.h"
#elif MF_BAT_MOMENTUM
#include "bat_momentum_data.h"
#else
#include "combat_animation_data.h"
#endif
static int ca_ids[MF_CA_NEW];
#if !MF_BAT_MOMENTUM || MF_ATTACK_SEQUENCE
static int ca_last_run[2];
#endif
#endif
#if MF_RUNNING_BAT_VISUALS
#include "running_bat_visual_data.h"
static int rbv_ids[MF_RBV_NEW];
#endif
#if MF_RUN_BAT
#include "running_data.h"
#else
#define MF_RUN_NEW 0
#define MF_RUN_BYTES 0u
#endif
#if MF_CORPORATE_PUNK
#include "corporate_bank.h"
/* CPHQ BEGIN */
#if MF_CP_HQ_COMBAT
#define MF_CP_EXTRA (MF_CP_TEXTURE_BYTES+MF_CPHQ_BYTES-MF_CPHQ_REPLACED)
#else
/* CPHQ END */
#define MF_CP_EXTRA MF_CP_TEXTURE_BYTES
/* CPHQ BEGIN */
#endif
/* CPHQ END */
#else
#define MF_CP_EXTRA 0u
#endif
#if MF_ORIGINAL_THREE_WALK
#include "original_three_data.h"
#endif
#if MF_SWAGGER_WALK
#include "swagger_data.h"
#define MF_REVIEW_RESOURCES (42+MF_POLISH_NEW+MF_SWAGGER_NEW)
#else
#define MF_REVIEW_RESOURCES (42+MF_POLISH_NEW+MF_RUN_NEW)
#endif
/* All frames remain resident for this comparison. This is not a live cache. */
static int resource_ids[MF_REVIEW_RESOURCES],last_resource;
static jo_palette *resource_palette;
static int palette_id,active,walking,paused,facing=1,polished=1;
/* transition: 1 start bridge, 2 finish support phase, 3 stop bridge. */
static int transition;
static unsigned phase,idle_phase[2],bridge_tick,texture_bytes;
/* PLAYERHURT BEGIN */
#if MF_PLAYER_HURT
#include "player_hurt_data.h"
static int ph_ids[MF_PH_NEW],ph_loaded;
#define MF_PH_EXTRA (ph_loaded?MF_PH_BYTES:0u)
#define MF_PH_REMOVED MF_PH_REPLACED
#else
#define MF_PH_EXTRA 0u
#define MF_PH_REMOVED 0u
#endif
/* PLAYERHURT END */
/* PLAYERDEATH BEGIN */
#if MF_PLAYER_DEATH
#include "player_death_data.h"
static int pd_ids[MF_PD_NEW],pd_loaded;
#define MF_PD_EXTRA (pd_loaded?MF_PD_BYTES:0u)
#define MF_PD_REMOVED MF_PD_REPLACED
#else
#define MF_PD_EXTRA 0u
#define MF_PD_REMOVED 0u
#endif
/* PLAYERDEATH END */
static unsigned end_of(int id)
{
    return (unsigned)((unsigned long)jo_sprite_get_raw_data(id)-JO_VDP1_VRAM)
        +((jo_sprite_get_width(id)*jo_sprite_get_height(id)+31u)&~31u);
}
static void resource_info(int rid,const char **name,int *width,int *height,unsigned *bytes)
{
    if(rid<42) {
        int slot=rid%21;
        const mf_animation_piece *p=&animation_parts[rid/21][slot/3][slot%3];
        *name=p->name;*width=p->width;*height=p->height;
        *bytes=((unsigned)*width*(unsigned)*height+31u)&~31u;
    }else {
        const mf_polish_resource *p;
#if MF_SWAGGER_WALK
        if(rid>=42+MF_POLISH_NEW)p=&swagger_resources[rid-42-MF_POLISH_NEW];
        else
#endif
#if MF_RUN_BAT
        if(rid>=81)p=&run_resources[rid-81];else
#endif
        p=&polish_resources[rid-42];
        *name=p->name;*width=p->width;*height=p->height;*bytes=p->bytes;
/* PLAYERHURT BEGIN */
#if MF_PLAYER_HURT
        if(rid==99)*name="RC0.TGA";
        if(rid==100)*name="RC1.TGA";
#endif
/* PLAYERHURT END */
/* PLAYERDEATH BEGIN */
#if MF_PLAYER_DEATH
        if(rid==99)*name="RD0.TGA";
        if(rid==100)*name="RD1.TGA";
#endif
/* PLAYERDEATH END */
    }
}
static int load_bank(int full)
{
    int rid,w,h;unsigned bytes,needed=0,end=end_of(last_resource);
    const char *name;
    for(rid=0;rid<MF_REVIEW_RESOURCES;rid++) {
#if MF_ORIGINAL_THREE_WALK
        if(!full && rid<81 && !original_three_required[rid])continue;
#elif MF_SWAGGER_WALK
        if(!full && !swagger_required[rid])continue;
#else
        (void)full;
#endif
        if(resource_ids[rid]>=0)continue;
        resource_info(rid,&name,&w,&h,&bytes);needed+=bytes;
    }
#if MF_RUNNING_BAT_VISUALS
    needed+=MF_RBV_BYTES-MF_LEGACY_RBV_SAVED_BYTES;
#if MF_COMBAT_ANIMATION
    needed+=MF_CA_BYTES-MF_LEGACY_CA_SAVED_BYTES-MF_DUPLICATE_SAVED_BYTES;
#endif
#endif
    /* Entire optional expansion is preflighted before the first CD read/upload. */
    if(end+needed>0x7fef8u)return 0;
    if(needed)jo_set_tga_default_palette(resource_palette);
    for(rid=0;rid<MF_REVIEW_RESOURCES;rid++) {
        int id;
#if MF_ORIGINAL_THREE_WALK
        if(!full && rid<81 && !original_three_required[rid])continue;
#elif MF_SWAGGER_WALK
        if(!full && !swagger_required[rid])continue;
#endif
        if(resource_ids[rid]>=0)continue;
        resource_info(rid,&name,&w,&h,&bytes);
        id=jo_sprite_add_tga(JO_ROOT_DIR,name,1);
        if(id<0 || jo_sprite_get_width(id)!=w || jo_sprite_get_height(id)!=h || end_of(id)>0x7fef8u) {
            jo_set_tga_default_palette(JO_NULL);return 0;
        }
        resource_ids[rid]=id;last_resource=id;
    }
    if(needed)jo_set_tga_default_palette(JO_NULL);
    texture_bytes=end_of(last_resource)-0x10000u;
#if MF_ORIGINAL_THREE_WALK
    return texture_bytes==MF_CP_EXTRA-MF_FX_SAVED_BYTES-MF_LEGACY_SAVED_BYTES-MF_LEGACY_PLAYER_SAVED_BYTES-MF_PH_REMOVED+MF_PH_EXTRA-MF_PD_REMOVED+MF_PD_EXTRA+MF_RUN_BYTES+(full?MF_ORIGINAL_THREE_FULL_BYTES:MF_ORIGINAL_THREE_BOOT_BYTES)-MF_HT_REPLACED-MF_HJ_REPLACED;
#elif MF_SWAGGER_WALK
    return texture_bytes==MF_CP_EXTRA-MF_FX_SAVED_BYTES-MF_LEGACY_SAVED_BYTES-MF_LEGACY_PLAYER_SAVED_BYTES-MF_PH_REMOVED+MF_PH_EXTRA-MF_PD_REMOVED+MF_PD_EXTRA+MF_RUN_BYTES+(full?MF_SWAGGER_FULL_BYTES:MF_SWAGGER_BOOT_BYTES);
#else
    return texture_bytes==MF_CP_EXTRA-MF_FX_SAVED_BYTES-MF_LEGACY_SAVED_BYTES-MF_LEGACY_PLAYER_SAVED_BYTES-MF_PH_REMOVED+MF_PH_EXTRA-MF_PD_REMOVED+MF_PD_EXTRA+302336u+MF_ANIMATION_BYTES+MF_POLISH_BYTES;
#endif
}
int mf_animation_load(jo_palette *palette,const int idle_ids[2][3])
{
    int actor,part,rid;
    resource_palette=palette;palette_id=palette->id;last_resource=idle_ids[1][2];texture_bytes=0;
    for(rid=0;rid<MF_REVIEW_RESOURCES;rid++)resource_ids[rid]=-1;
    for(actor=0;actor<2;actor++)for(part=0;part<3;part++)resource_ids[actor*21+part]=idle_ids[actor][part];
    if(!load_bank(0))return 0;
#if MF_RUNNING_BAT_VISUALS
    jo_set_tga_default_palette(resource_palette);
    for(rid=0;rid<MF_RBV_NEW;rid++) {
#if MF_LEGACY_SPRITE_PHASE2
        if(rid!=0){rbv_ids[rid]=-1;continue;} /* RBV00 is the live carry. */
#endif
        const mf_polish_resource *p=&rbv_resources[rid];
        int id=jo_sprite_add_tga(JO_ROOT_DIR,p->name,1);
        if(id<0 || jo_sprite_get_width(id)!=p->width || jo_sprite_get_height(id)!=p->height || end_of(id)>0x7fef8u){jo_set_tga_default_palette(JO_NULL);return 0;}
        rbv_ids[rid]=id;last_resource=id;
    }
    jo_set_tga_default_palette(JO_NULL);
    texture_bytes=end_of(last_resource)-0x10000u;
    if(texture_bytes!=MF_CP_EXTRA-MF_FX_SAVED_BYTES-MF_LEGACY_SAVED_BYTES-MF_LEGACY_PLAYER_SAVED_BYTES-MF_PH_REMOVED+MF_PH_EXTRA-MF_PD_REMOVED+MF_PD_EXTRA+MF_ORIGINAL_THREE_BOOT_BYTES+MF_RUN_BYTES+MF_RBV_BYTES-MF_LEGACY_RBV_SAVED_BYTES-MF_HT_REPLACED-MF_HJ_REPLACED)return 0;
#endif
#if MF_COMBAT_ANIMATION
    jo_set_tga_default_palette(resource_palette);
    for(rid=0;rid<MF_CA_NEW;rid++) {
#if MF_LEGACY_SPRITE_PHASE2
        /* Live jab/cross lower and horizontal fast-bat contact only. */
        if(!((rid>=0 && rid<=7) || (rid>=28 && rid<=35))){ca_ids[rid]=-1;continue;}
#endif
#if MF_DUPLICATE_TEXTURE_CLEANUP
        if(rid==2 || rid==30) {
            /* Gallery GB2/GC2 are byte-identical indexed feet on this palette.
               Reuse the handle, not a new definition. Do not rewind the
               allocator's last_resource to an earlier canonical allocation. */
            int id=idle_ids[rid==30][2];
            if(id<0 || jo_sprite_get_width(id)!=ca_resources[rid].width ||
               jo_sprite_get_height(id)!=ca_resources[rid].height)return 0;
            ca_ids[rid]=id;continue;
        }
#endif
        const mf_polish_resource *p=&ca_resources[rid];
/* PLAYERHURT BEGIN */
#if MF_PLAYER_HURT
/* PLAYERDEATH BEGIN */
#if MF_PLAYER_DEATH
        int id=jo_sprite_add_tga("COMBAT",rid==51?"DT0.TGA":rid==52?"DT1.TGA":p->name,1);
#else
/* PLAYERDEATH END */
        int id=jo_sprite_add_tga("COMBAT",rid==51?"CT0.TGA":rid==52?"CT1.TGA":p->name,1);
/* PLAYERDEATH BEGIN */
#endif
/* PLAYERDEATH END */
#else
/* PLAYERHURT END */
        int id=jo_sprite_add_tga("COMBAT",p->name,1);
/* PLAYERHURT BEGIN */
#endif
/* PLAYERHURT END */
        if(id<0 || jo_sprite_get_width(id)!=p->width || jo_sprite_get_height(id)!=p->height || end_of(id)>0x7fef8u){jo_set_tga_default_palette(JO_NULL);return 0;}
        ca_ids[rid]=id;last_resource=id;
    }
    jo_set_tga_default_palette(JO_NULL);
    texture_bytes=end_of(last_resource)-0x10000u;
    if(texture_bytes!=MF_CP_EXTRA-MF_FX_SAVED_BYTES-MF_LEGACY_SAVED_BYTES-MF_LEGACY_PLAYER_SAVED_BYTES-MF_PH_REMOVED+MF_PH_EXTRA-MF_PD_REMOVED+MF_PD_EXTRA+MF_ORIGINAL_THREE_BOOT_BYTES+MF_RUN_BYTES+MF_RBV_BYTES-MF_LEGACY_RBV_SAVED_BYTES+MF_CA_BYTES-MF_LEGACY_CA_SAVED_BYTES-MF_DUPLICATE_SAVED_BYTES-MF_HT_REPLACED-MF_HJ_REPLACED)return 0;
#endif
    return 1;
}
unsigned mf_animation_texture_bytes(void){return texture_bytes;}
int mf_animation_active(void){return active;}
int mf_animation_toggle(void)
{
    /* Only a stopped gallery-mode entry may expand the resident review bank.
       No gameplay/update/draw function uploads textures or reads the disc. */
#if !MF_RUN_BAT
    if(!active && !load_bank(1))return 0;
#endif
    active=!active;walking=paused=transition=0;phase=idle_phase[0]=idle_phase[1]=bridge_tick=0;
    return 1;
}
void mf_animation_leave(void){active=transition=0;}

#if !MF_RUN_BAT
static unsigned idle_total(int a)
{return (unsigned)(polish_idle_ticks[a][0]+polish_idle_ticks[a][1]+polish_idle_ticks[a][2]+polish_idle_ticks[a][3]);}

#endif

#if !MF_RUN_BAT
static int idle_frame(int a)
{
    unsigned t=idle_phase[a];int f;
    for(f=0;f<3;f++){if(t<(unsigned)polish_idle_ticks[a][f])return f;t-=(unsigned)polish_idle_ticks[a][f];}
    return 3;
}

#endif
static int current_frame(int a)
{
#if MF_RUN_BAT
    (void)a;
    return walking?18+(int)(phase/MF_RUN_FRAME_HOLD)%4:15+(int)(phase/10)%3;
#else
    if(!polished)return walking?1+(int)(phase/5)%6:0;
    if(transition==1)return bridge_tick<5?11:10;
    if(transition==3)return bridge_tick<5?10:11;
    if(walking || transition==2)return 4+(int)(phase/5)%6;
    return idle_frame(a);
#endif
}
static void advance_tick(void)
{
    int a;(void)a;
    if(polished && (transition==1 || transition==3)) {
        if(++bridge_tick>=10){transition=0;phase=idle_phase[0]=idle_phase[1]=0;}
        return;
    }
    if(polished && transition==2) {
        if(phase%15==0){transition=3;bridge_tick=0;return;}
        phase=(phase+1)%30;
        if(phase%15==0){transition=3;bridge_tick=0;}
        return;
    }
#if MF_RUN_BAT
    phase=(phase+1)%(walking?24:30);
#else
    if(walking)phase=(phase+1)%30;
    else if(polished)for(a=0;a<2;a++)idle_phase[a]=(idle_phase[a]+1)%idle_total(a);
#endif
}
void mf_animation_update(unsigned held,unsigned pressed,unsigned ticks)
{
    unsigned i;
    if((held&(MF_A|MF_B))==(MF_A|MF_B) && (pressed&(MF_A|MF_B))) {
        polished=!polished;transition=0;idle_phase[0]=idle_phase[1]=0;
        pressed&=~(MF_A|MF_B);
    }
    if(pressed&MF_A)facing=-facing;
    if(pressed&MF_B)paused=!paused;
    if(pressed&MF_UP) {
        walking=!walking;
        if(polished && !paused && !MF_RUN_BAT){transition=walking?1:2;bridge_tick=0;}
        else {transition=0;phase=idle_phase[0]=idle_phase[1]=0;}
    }
    if(pressed&(MF_LEFT|MF_RIGHT)) {
        int dir=(pressed&MF_LEFT)?-1:1,a;(void)a;
        paused=1;transition=0;
#if MF_RUN_BAT
        phase=(unsigned)(((int)(phase/(walking?6:10))+dir+(walking?4:3))%(walking?4:3))*(walking?6:10);
#else
        if(walking)phase=(unsigned)(((int)(phase/5)+dir+6)%6)*5;
        else if(polished)for(a=0;a<2;a++) {
            int f=(idle_frame(a)+dir+4)%4,j;idle_phase[a]=0;
            for(j=0;j<f;j++)idle_phase[a]+=(unsigned)polish_idle_ticks[a][j];
        }
#endif
        return;
    }
    if(ticks>6)ticks=6;
    if(!paused)for(i=0;i<ticks;i++)advance_tick();
}
#if MF_RUNNING_BAT_VISUALS
static void rbv_draw(int resource,int left,int top,int direction,int center,int ground,int depth)
{
    const mf_polish_resource *p=&rbv_resources[resource];
    int x=direction>0?center+left:center-left-p->width;
    jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();jo_sprite_set_palette(palette_id);
    if(direction<0)jo_sprite_enable_horizontal_flip();
    jo_sprite_draw3D2(rbv_ids[resource],x,ground+top,depth);
    jo_sprite_disable_horizontal_flip();
}
static void rbv_carry_draw(int actor,int frame,int center,int ground,int direction,int depth)
{
    int x=rbv_hands[actor][frame][0]-64-rbv_carry[1];
    int y=rbv_hands[actor][frame][1]-92-rbv_carry[2];
    rbv_draw(rbv_carry[0],x,y,direction,center,ground,depth+1);
}
void mf_running_bat_metal_draw(int actor,int frame,int center,int ground,int direction,int depth)
{
    const short *p;
    if(actor<0 || actor>=2 || frame<0 || frame>=7 || !texture_bytes)return;
    p=rbv_overlay[actor][frame];if(p[0]<0)return;rbv_draw(p[0],p[1],p[2],direction,center,ground,depth);
}
#endif
#if MF_PUNCH_COMBO
static int cross_ids[2],cross_loaded;
int mf_cross_load(void)
{
    unsigned base=end_of(last_resource);int a;
    if(cross_loaded)return 1;
    /* Exactly two remaining definitions; no removal/redefinition of old views. */
    if(base+7040u>0x7fef8u || jo_get_last_sprite_id()+2>=JO_MAX_SPRITE)return 0;
    jo_set_tga_default_palette(resource_palette);
    for(a=0;a<2;a++) {
        int id=jo_sprite_add_tga("COMBO",a?"XC1.TGA":"XC0.TGA",1);
        if(id<0 || jo_sprite_get_width(id)!=80 || jo_sprite_get_height(id)!=44 || end_of(id)>0x7fef8u)return 0;
        cross_ids[a]=id;last_resource=id;
    }
    jo_set_tga_default_palette(JO_NULL);texture_bytes=end_of(last_resource)-0x10000u;
    cross_loaded=1;return end_of(last_resource)==base+7040u;
}
#endif
#if MF_COMBAT_ANIMATION
static void ca_draw_list(const mf_polish_piece *p,int center,int ground,int direction,int depth)
{
    for(;p->resource>=0;p++) {
        int x=direction>0?center-64+p->x:center+64-p->x-p->width;
        jo_sprite_draw3D2(ca_ids[p->resource],x,ground-108+p->y,depth);
    }
}
#if MF_JAB_COHESION
static int jab_recovery_draw(int actor,int center,int ground,int direction,int depth)
{
    int part;jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();jo_sprite_set_palette(palette_id);
    if(direction<0)jo_sprite_enable_horizontal_flip();
    for(part=0;part<3;part++){
        const mf_polish_piece *p=&polish_parts[actor][0][part];int dx=part<2?1:0,dy=0;
        int x=direction>0?center-64+p->x+dx:center+64-p->x-p->width-dx;
        jo_sprite_draw3D2(resource_ids[p->resource],x,ground-92+p->y+dy,depth-(part==2));
    }
    jo_sprite_disable_horizontal_flip();jo_sprite_restore_sprite_scale();return 1;
}
static void jab_adjusted_draw(const mf_polish_piece *p,int actor,int impact,int upper,int center,int ground,int direction,int depth)
{
    for(;p->resource>=0;p++){
        int group=upper?(p->y<48?0:1):(p->y<80?2:p->y<96?3:4);
        int dx=jab_offsets[actor][impact][group][0],dy=jab_offsets[actor][impact][group][1];
        int x=direction>0?center-64+p->x+dx:center+64-p->x-p->width-dx;
        jo_sprite_draw3D2(ca_ids[p->resource],x,ground-108+p->y+dy,depth-((upper && group==1) || (!upper && group>=3)));
    }
}
#endif
int mf_combat_prototype_draw(const mf_game *g,int actor,int center,int ground,int depth)
{
    const mf_player *p;int key;
#if MF_ATTACK_SEQUENCE
    int weapon,phase;
#else
    int lower=0;
#endif
    if(actor<0 || actor>=2 || !texture_bytes)return 0;
    p=&g->players[actor];
#if !MF_BAT_MOMENTUM || MF_ATTACK_SEQUENCE
    if(g->dash[actor].dir)ca_last_run[actor]=((unsigned)g->dash[actor].anim/(MF_RUN_FRAME_HOLD*MF_DASH_ANIM_NUM))%4;
#endif
    /* Keep aerial, hurt, torch and opening carried-run windup on approved paths. */
    if(!p->active || !p->health || p->hurt || p->height || p->vz || p->torch || !p->attack)return 0;
#if MF_PUNCH_COMBO
    if(!p->bat && !p->attack_air && g->combo[actor].phase==2 && cross_loaded) {
        /* Same hit window6..10. Contact remains visible through post-step11. */
        if(p->attack<=11) {
            jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();jo_sprite_set_palette(palette_id);
            if(p->facing<0)jo_sprite_enable_horizontal_flip();
            ca_draw_list(seq_lower[actor],center,ground,p->facing,depth);
            jo_sprite_draw3D2(cross_ids[actor],p->facing>0?center-24:center-56,ground-88,depth-1);
            jo_sprite_disable_horizontal_flip();return 1;
        }
        if(p->attack<=16+MF_CROSS_RECOVERY_EXTRA)return jab_recovery_draw(actor,center,ground,p->facing,depth);
        return mf_animation_draw_actor(actor,0,center,ground,p->facing,depth);
    }
#endif
#if MF_FAST_RUNNING_BAT
    if(p->bat==MF_BAT_RUNNING && g->running_bat[actor].active) {
        /* Reuse the exact current four-piece carry, including waist fixes.
           The horizontal contact upper already contains its connected grip. */
        if(p->attack<MF_FAST_BAT_ACTIVE_FIRST)
            return mf_animation_draw_actor(actor,18+(g->running_bat[actor].active-1),center,ground,p->facing,depth);
        if(p->attack>=MF_FAST_BAT_RECOVERY_FIRST)
            return mf_animation_draw_actor(actor,0,center,ground,p->facing,depth);
        jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();jo_sprite_set_palette(palette_id);
        if(p->facing<0)jo_sprite_enable_horizontal_flip();
        ca_draw_list(seq_lower[actor],center,ground,p->facing,depth);
        ca_draw_list(seq_upper[actor][1],center,ground,p->facing,depth-1);
        jo_sprite_disable_horizontal_flip();jo_sprite_restore_sprite_scale();return 1;
    }
#endif
#if MF_ATTACK_SEQUENCE
    phase=g->running_bat[actor].active?ca_last_run[actor]:0;
    key=mf_sequence_key(p->attack,p->bat,phase,&weapon);
#if MF_JAB_COHESION
    if(key==-2)return jab_recovery_draw(actor,center,ground,p->facing,depth);
#endif
    if(key<0)return mf_animation_draw_actor(actor,0,center,ground,p->facing,depth);
#else
    if(p->bat) {
#if !MF_BAT_MOMENTUM
        if(g->running_bat[actor].active && p->attack<6)return 0;
#endif
        key=(p->attack<12 || p->attack>=28)?2:3;
#if MF_BAT_MOMENTUM
        lower=1; /* One planted lower body throughout every bat counter. */
#else
        if(g->running_bat[actor].active)lower=1+(ca_last_run[actor]+(p->attack-6)/MF_RUN_FRAME_HOLD)%4;
#endif
    }else {
        if(p->attack<3 || p->attack>=16)return mf_animation_draw_actor(actor,0,center,ground,p->facing,depth);
        key=(p->attack<6 || p->attack>10)?0:1;
    }
#endif
    jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();jo_sprite_set_palette(palette_id);
    if(p->facing<0)jo_sprite_enable_horizontal_flip();
#if MF_ATTACK_SEQUENCE
#if MF_JAB_COHESION
    if(!p->bat){
        jab_adjusted_draw(seq_lower[actor],actor,p->attack>=6,0,center,ground,p->facing,depth);
        jab_adjusted_draw(seq_upper[actor][0],actor,p->attack>=6,1,center,ground,p->facing,depth-1);
        jo_sprite_disable_horizontal_flip();jo_sprite_restore_sprite_scale();return 1;
    }
#endif
    ca_draw_list(seq_lower[actor],center,ground,p->facing,depth);
    if(weapon==0)rbv_carry_draw(actor,phase,center,ground,p->facing,depth);
    else if(weapon>0){
        const mf_polish_piece *q=seq_weapon[weapon-1];
        for(;q->resource>=0;q++){
            int ox=q->x-40+rbv_hands[actor][phase][0]-64;
            int x=p->facing>0?center+ox:center-ox-q->width;
            jo_sprite_draw3D2(ca_ids[q->resource],x,ground+q->y-40+rbv_hands[actor][phase][1]-92,depth+1);
        }
    }
    /* The shared RBV helper restores flip state; reapply it for the upper. */
    jo_sprite_disable_horizontal_flip();if(p->facing<0)jo_sprite_enable_horizontal_flip();
    /* Upper weapon/arms may overlap the thighs during the lower arc. */
    ca_draw_list(seq_upper[actor][key],center,ground,p->facing,depth-1);
#else
    ca_draw_list(ca_lower[actor][lower],center,ground,p->facing,depth);
    ca_draw_list(ca_upper[actor][key],center,ground,p->facing,depth);
#endif
    jo_sprite_disable_horizontal_flip();jo_sprite_restore_sprite_scale();return 1;
}
#endif
/* Reuses the loader's exact IDs/palette; no allocation, I/O or preview state. */
int mf_animation_draw_actor(int actor,int frame,int center,int ground,int direction,int depth)
{
    int part;
    const mf_polish_piece *pieces;
    if(!texture_bytes || actor<0 || actor>=2 || frame<0)return 0;
#if MF_ORIGINAL_THREE_WALK
#if MF_RUN_BAT
    if(frame>=22 || (frame>=12 && frame<15))return 0;
    if(frame>=18)pieces=run_parts[actor][frame-18];else
#else
    if(frame>=18 || (frame>=12 && frame<15))return 0;
#endif
    if(frame>=15)pieces=original_three_parts[actor][frame-15];else
#elif MF_SWAGGER_WALK
    if(frame>=15)return 0;
    if(frame>=12)pieces=swagger_parts[actor][frame-12];else
#else
    if(frame>=12)return 0;
#endif
    pieces=polish_parts[actor][frame];
    /* Reject an unavailable optional pose before submitting any pieces. */
    for(part=0;part<3;part++)if(resource_ids[pieces[part].resource]<0)return 0;
#if MF_RUNNING_BAT_VISUALS
    if(frame>=18)rbv_carry_draw(actor,frame-18,center,ground,direction,depth);
#endif
    jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();
    jo_sprite_set_palette(palette_id);
    if(direction<0)jo_sprite_enable_horizontal_flip();
    for(part=0;part<3;part++) {
        const mf_polish_piece *p=&pieces[part];
        int x=direction>0?center-64+p->x:center+64-p->x-p->width;
        jo_sprite_draw3D2(resource_ids[p->resource],x,ground-92+p->y,depth);
    }
    jo_sprite_disable_horizontal_flip();jo_sprite_restore_sprite_scale();
    return 1;
}
void mf_animation_draw(const int street[5],int street_palette_id)
{
    int line,actor,part;
    const int centers[2]={90,226};
    jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();mf_street_draw(street,street_palette_id,280);jo_sprite_set_palette(palette_id);
#if MF_RUNNING_BAT_VISUALS
    for(actor=0;actor<2;actor++){int frame=current_frame(actor);if(frame>=18)rbv_carry_draw(actor,frame-18,centers[actor],210,facing,230);}
#endif
    if(facing<0)jo_sprite_enable_horizontal_flip();
    for(actor=0;actor<2;actor++)for(part=0;part<3;part++) {
        int frame=current_frame(actor),rid,x,y,w;
#if MF_RUN_BAT
        {
            const mf_polish_piece *p=frame>=18?&run_parts[actor][frame-18][part]:&original_three_parts[actor][frame-15][part];rid=p->resource;x=p->x;y=p->y;w=p->width;
        }
#else
        if(polished) {
            const mf_polish_piece *p=&polish_parts[actor][frame][part];rid=p->resource;x=p->x;y=p->y;w=p->width;
        }else {
            const mf_animation_piece *p=&animation_parts[actor][frame][part];rid=actor*21+frame*3+part;x=p->x;y=p->y;w=p->width;
        }
#endif
        x=facing>0?centers[actor]-64+x:centers[actor]+64-x-w;
        jo_sprite_draw3D2(resource_ids[rid],x,210-92+y,230);
    }
    jo_sprite_disable_horizontal_flip();jo_sprite_restore_sprite_scale();
    jo_clear_screen_line(2);jo_clear_screen_line(4);jo_clear_screen_line(6);for(line=25;line<30;line++)jo_clear_screen_line(line);
#if MF_RUN_BAT
    jo_print(2,2,"RUN / APPROVED WALK REVIEW");
#else
    jo_print(2,2,polished?"ANIMATION POLISH REVIEW":"FF24C5E ORIGINAL PROTOTYPE");
#endif
    jo_printf(2,4,"%s B%02d C%02d %s",MF_RUN_BAT?(walking?"RUN":"WALK"):(walking?"WALK":"IDLE"),current_frame(0),current_frame(1),paused?"PAUSED":"PLAY");
    jo_printf(2,6,"VDP1 %u / 458488 BYTES",texture_bytes);
    jo_print(1,27,"UP IDLE/WALK B PAUSE A MIRROR");jo_print(1,28,MF_RUN_BAT?"L R STEP   UP WALK/RUN":"L R STEP A+B ORIGINAL/POLISH");jo_print(1,29,"DOWN GALLERY START GAME C DIAG");
}
#endif

#if MF_HQ_TORCH
/* Definitions are stable until draw completion: SGL resolves texno later.
   Alias only already-resident rows. A final tail definition preserves Jo's next
   allocation cursor even if a future initialization stage adds another asset. */
static int ht_alias(int source,int row,int height)
{
    /* Pinned Jo allows a zero-payload registration. Replace its metadata
       before any draw; no zero-height definition is ever submitted to VDP1. */
    jo_img_8bits empty={.width=8,.height=0,.data=JO_NULL};
    int id;
    if(source<0 || source>=JO_MAX_SPRITE || row<0 || height<=0 ||
       row+height>__jo_sprite_def[source].height || (__jo_sprite_def[source].width&7))return -1;
    id=jo_sprite_add_8bits_image(&empty);
    if(id<0)return -1;
    __jo_sprite_def[id]=__jo_sprite_def[source];
    __jo_sprite_def[id].adr+=row*__jo_sprite_def[source].width/8;
    __jo_sprite_def[id].height=height;
    __jo_sprite_def[id].size=(__jo_sprite_def[id].width/8<<8)|height;
    __jo_sprite_pic[id]=__jo_sprite_pic[source];
    __jo_sprite_pic[id].index=id;
    __jo_sprite_pic[id].data=(void *)((unsigned long)__jo_sprite_pic[source].data+row*__jo_sprite_def[source].width);
    return id;
}
int mf_hq_torch_load(int enemy_palette)
{
    int rid,a,f;unsigned end=end_of(last_resource);
    if(end+MF_HT_BYTES>0x7fef8u || last_resource+MF_HT_NEW+9>=JO_MAX_SPRITE)return 0;
    ht_enemy_palette=enemy_palette;jo_set_tga_default_palette(JO_NULL);
    for(rid=0;rid<MF_HT_NEW;rid++){
        const mf_polish_resource *p=&ht_resources[rid];
        int id=jo_sprite_add_tga("HQTORCH",p->name,1);
        if(id<0 || jo_sprite_get_width(id)!=p->width || jo_sprite_get_height(id)!=p->height || end_of(id)>0x7fef8u)return 0;
        ht_ids[rid]=id;last_resource=id;
    }
    texture_bytes=end_of(last_resource)-0x10000u;
    for(a=0;a<2;a++)for(f=0;f<4;f++){
        const mf_polish_piece *q=f?&original_three_parts[a][f-1][1]:&polish_parts[a][0][1];
        ht_lower[a][f]=ht_alias(resource_ids[q->resource],48-q->y,q->height-(48-q->y));
        if(ht_lower[a][f]<0)return 0;
    }
    if(ht_alias(last_resource,0,jo_sprite_get_height(last_resource))<0)return 0;
    return texture_bytes==MF_CP_EXTRA-MF_FX_SAVED_BYTES-MF_LEGACY_SAVED_BYTES-MF_LEGACY_PLAYER_SAVED_BYTES-MF_PH_REMOVED+MF_PH_EXTRA-MF_PD_REMOVED+MF_PD_EXTRA+MF_ORIGINAL_THREE_BOOT_BYTES+MF_RUN_BYTES+MF_RBV_BYTES-MF_LEGACY_RBV_SAVED_BYTES+MF_CA_BYTES-MF_LEGACY_CA_SAVED_BYTES-MF_DUPLICATE_SAVED_BYTES-MF_HT_REPLACED-MF_HJ_REPLACED+MF_HT_BYTES;
}
int mf_hq_torch_draw(const mf_game *g,int actor,int center,int ground,int depth)
{
    const mf_player *p;const mf_polish_piece *lower,*head;int pose,i,frame;
    if(actor<0 || actor>=2 || !texture_bytes)return 0;
    p=&g->players[actor];
    if(!p->active || !p->health || p->hurt || !p->torch)return 0;
    pose=p->torch==MF_TORCH_EQUIP?0:p->torch==MF_TORCH_FIRE?1:2;
    frame=(unsigned)p->walk/MF_ORIGINAL_FRAME_HOLD%3;
    lower=p->moving?original_three_parts[actor][frame]:polish_parts[actor][0];
    head=&polish_parts[actor][0][0];
    jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();
    if(p->facing<0)jo_sprite_enable_horizontal_flip();
    jo_sprite_set_palette(palette_id);
    for(i=1;i<3;i++){
        const mf_polish_piece *q=&lower[i];
        int top=i==1?48:q->y;
        int x=p->facing>0?center-64+q->x:center+64-q->x-q->width;
        int id=i==1?ht_lower[actor][p->moving?frame+1:0]:resource_ids[q->resource];
        jo_sprite_draw3D2(id,x,ground-92+top,depth);
    }
    jo_sprite_draw3D2(resource_ids[head->resource],p->facing>0?center-64+head->x:center+64-head->x-head->width,ground-92+head->y,depth-1);
    for(i=0;i<2;i++){
        const mf_polish_piece *q=&ht_parts[actor][pose][i];
        int x=p->facing>0?center-64+q->x:center+64-q->x-q->width;
        jo_sprite_set_palette(i?ht_enemy_palette:palette_id);
        jo_sprite_draw3D2(ht_ids[q->resource],x,ground-92+q->y,depth-1-i);
    }
    jo_sprite_disable_horizontal_flip();jo_sprite_restore_sprite_scale();return 1;
}
#endif

#if MF_HQ_JUMP
int mf_hq_jump_load(void)
{
    int i,a;unsigned end=end_of(last_resource);
    /* Nine Stage A views follow last_resource; five new views follow this bank. */
    if(end+MF_HJ_BYTES>0x7fef8u || last_resource+MF_HJ_NEW+14>=JO_MAX_SPRITE)return 0;
    jo_set_tga_default_palette(JO_NULL);
    for(i=0;i<MF_HJ_NEW;i++){
        const mf_polish_resource *q=&hj_resources[i];
        int id=jo_sprite_add_tga("HQJUMP",q->name,1);
        if(id<0 || jo_sprite_get_width(id)!=q->width || jo_sprite_get_height(id)!=q->height || end_of(id)>0x7fef8u)return 0;
        hj_ids[i]=id;last_resource=id;
    }
    texture_bytes=end_of(last_resource)-0x10000u;
    for(a=0;a<2;a++){
        const mf_polish_piece *q=&polish_parts[a][0][1];
        hj_upper[a]=ht_alias(resource_ids[q->resource],0,48-q->y);
        hj_compress_lower[a]=ht_alias(resource_ids[q->resource],48-q->y,30);
        if(hj_upper[a]<0 || hj_compress_lower[a]<0)return 0;
    }
    if(ht_alias(last_resource,0,jo_sprite_get_height(last_resource))<0)return 0;
    return texture_bytes==MF_CP_EXTRA-MF_FX_SAVED_BYTES-MF_LEGACY_SAVED_BYTES-MF_LEGACY_PLAYER_SAVED_BYTES-MF_PH_REMOVED+MF_PH_EXTRA-MF_PD_REMOVED+MF_PD_EXTRA+MF_ORIGINAL_THREE_BOOT_BYTES+MF_RUN_BYTES+MF_RBV_BYTES-MF_LEGACY_RBV_SAVED_BYTES+MF_CA_BYTES-MF_LEGACY_CA_SAVED_BYTES-MF_DUPLICATE_SAVED_BYTES-MF_HT_REPLACED-MF_HJ_REPLACED+MF_HT_BYTES+MF_HJ_BYTES;
}
static void hj_piece(int id,const mf_polish_piece *q,int center,int ground,int facing,int depth,int dy)
{
    int x=facing>0?center-64+q->x:center+64-q->x-q->width;
    jo_sprite_draw3D2(id,x,ground-92+q->y+dy,depth);
}
int mf_hq_jump_draw(const mf_game *g,int actor,int center,int ground,int depth)
{
    const mf_player *p;const mf_polish_piece *head;int phase;
    if(actor<0 || actor>=2 || !texture_bytes)return 0;
    p=&g->players[actor];phase=mf_hq_jump_phase(p);if(!phase)return 0;
    ground-=p->height/256;head=&polish_parts[actor][0][0];
    if(phase==5 && p->landing<3)return mf_animation_draw_actor(actor,0,center,ground,p->facing,depth);
    jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();jo_sprite_set_palette(palette_id);
    if(p->facing<0)jo_sprite_enable_horizontal_flip();
    if(phase==1 || phase==5){
        const mf_polish_piece *mid=&polish_parts[actor][0][1],*boot=&polish_parts[actor][0][2];
        mf_polish_piece low=*mid;int compression=phase==1?2:(actor?2:3);
        low.y=48;low.height=32;
        hj_piece(hj_compress_lower[actor],&low,center,ground,p->facing,depth,2);
        hj_piece(hj_upper[actor],mid,center+(phase==1?p->facing:0),ground,p->facing,depth-1,compression);
        hj_piece(resource_ids[head->resource],head,center+(phase==1?p->facing:0),ground,p->facing,depth-1,compression);
        hj_piece(resource_ids[boot->resource],boot,center,ground,p->facing,depth-2,0);
    }else{
        int pose=phase==2?0:phase==3?1:phase==4?2:3;
        const mf_polish_piece *low=&hj_lower_parts[actor][pose],*upper=&hj_upper_parts[actor];
        hj_piece(hj_ids[low->resource],low,center,ground,p->facing,depth,0);
/* ANATOMY BEGIN */
        low=&hj_lower_extra[actor][pose];
        if(low->resource>=0)hj_piece(hj_ids[low->resource],low,center,ground,p->facing,depth,0);
/* ANATOMY END */
        if(phase==4)hj_piece(hj_upper[actor],&polish_parts[actor][0][1],center,ground,p->facing,depth-1,0);
        else hj_piece(hj_ids[upper->resource],upper,center,ground,p->facing,depth-1,0);
        hj_piece(resource_ids[head->resource],head,center,ground,p->facing,depth-2,0);
    }
    jo_sprite_disable_horizontal_flip();jo_sprite_restore_sprite_scale();return 1;
}
#endif
/* PLAYERHURT BEGIN */
#if MF_PLAYER_HURT
int mf_player_hurt_load(void)
{
    int r;unsigned base=end_of(last_resource);
    if(ph_loaded)return 1;
    /* Five registered jump views follow the last jump payload. */
    if(base+MF_PH_BYTES>0x7fef8u || last_resource+MF_PH_NEW+5>=JO_MAX_SPRITE)return 0;
    jo_set_tga_default_palette(resource_palette);
    for(r=0;r<MF_PH_NEW;r++){
        const mf_polish_resource *p=&ph_resources[r];int id=jo_sprite_add_tga("HQHURT",p->name,1);
        if(id<0 || jo_sprite_get_width(id)!=p->width || jo_sprite_get_height(id)!=p->height || end_of(id)>0x7fef8u)return 0;
        ph_ids[r]=id;last_resource=id;
    }
    jo_set_tga_default_palette(JO_NULL);ph_loaded=1;
    texture_bytes=end_of(last_resource)-0x10000u;
    return end_of(last_resource)==base+MF_PH_BYTES;
}
int mf_player_hurt_phase(const mf_game *g,int actor)
{
    const mf_player *p;if(actor<0 || actor>=2)return -1;p=&g->players[actor];
    if(!p->active || p->health<=0 || p->hurt<=0)return -1;
    return p->hurt>8?0:p->hurt>4?1:2;
}
int mf_player_hurt_draw(const mf_game *g,int actor,int center,int ground,int depth)
{
    int f=mf_player_hurt_phase(g,actor),part;if(f<0 || !ph_loaded)return 0;
    jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();jo_sprite_set_palette(palette_id);
    if(g->players[actor].facing<0)jo_sprite_enable_horizontal_flip();
    for(part=0;part<2;part++){
        const mf_polish_piece *p=part?&ph_upper[actor][f]:&ph_lower[actor][f?1:0];
        int id=ph_ids[p->resource];
        int x=g->players[actor].facing>0?center-64+p->x:center+64-p->x-p->width;
        jo_sprite_draw3D2(id,x,ground-92-g->players[actor].height/256+p->y,depth);
    }
    jo_sprite_disable_horizontal_flip();return 1;
}
#endif
/* PLAYERHURT END */
/* PLAYERDEATH BEGIN */
#if MF_PLAYER_DEATH
int mf_player_death_load(void)
{
    int r;unsigned base=end_of(last_resource);
    if(pd_loaded)return 1;
    if(!ph_loaded || base+MF_PD_BYTES>0x7fef8u || last_resource+MF_PD_NEW>=JO_MAX_SPRITE)return 0;
    jo_set_tga_default_palette(resource_palette);
    for(r=0;r<MF_PD_NEW;r++){
        const mf_polish_resource *p=&pd_resources[r];int id=jo_sprite_add_tga("HQDEATH",p->name,1);
        if(id<0 || jo_sprite_get_width(id)!=p->width || jo_sprite_get_height(id)!=p->height || end_of(id)>0x7fef8u)return 0;
        pd_ids[r]=id;last_resource=id;
    }
    jo_set_tga_default_palette(JO_NULL);pd_loaded=1;texture_bytes=end_of(last_resource)-0x10000u;
    return end_of(last_resource)==base+MF_PD_BYTES;
}
int mf_player_death_phase(const mf_game *g,int actor)
{
    const mf_player *p;int elapsed;
    if(actor<0 || actor>=2)return -1;
    p=&g->players[actor];
    if(!p->active || p->health>0 || p->defeated<=0)return -1;
    elapsed=MF_BUCK_RECOVERY_TICKS-p->defeated;
    return elapsed<8?0:elapsed<24?1:2;
}
int mf_player_death_draw(const mf_game *g,int actor,int center,int ground,int depth)
{
    int f=mf_player_death_phase(g,actor),part,elapsed,air;
    const mf_player *p=&g->players[actor];if(f<0 || !pd_loaded)return 0;
    elapsed=MF_BUCK_RECOVERY_TICKS-p->defeated;
    /* A lethal airborne hit freezes simulation height. Only the visual falls to ground. */
    air=elapsed<24?(p->height/256)*(24-elapsed)/24:0;
    jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();jo_sprite_set_palette(palette_id);
    if(p->facing<0)jo_sprite_enable_horizontal_flip();
    for(part=0;part<2;part++){
        const mf_polish_piece *q;
        int id,x,y;
        if(f==2 && !part){q=&pd_lower[actor];id=pd_ids[q->resource];}
        else {q=part?&ph_upper[actor][f?2:0]:&ph_lower[actor][f?1:0];id=ph_ids[q->resource];}
        x=p->facing>0?center-64+q->x:center+64-q->x-q->width;
        y=ground-92-air+q->y+(f==2 && part?14:0);
        jo_sprite_draw3D2(id,x,y,depth);
    }
    jo_sprite_disable_horizontal_flip();return 1;
}
#endif
/* PLAYERDEATH END */
