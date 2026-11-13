#include "wingsuit_audio.h"
#include <jo/jo.h>
#include "game.h"
#include "music.h"
#include "art_data.h"
#include "build-info.h"
#if MF_LEVEL2_WINGSUIT
#include "wingsuit_runtime.h"
#include "dev_stage_skip.h"
static volatile int stage2_owned;
#endif
#include "arcade_fx.h"
#include "street.h"
#if MF_CORPORATE_PUNK
#include "corporate_animation.h"
#include "enemy_sprite_bank.h"
#include "ricky_animation.h"
#endif
#if MF_ANIMATION_PREVIEW
#include "animation_preview.h"
#endif
#if MF_PLAYABLE_ANIMATION
#include "player_animation.h"
#include "running_bat_visual_config.h"
#include "combat_animation_config.h"
#endif
#if MF_PARALLAX_DEMO
#include "parallax.h"
#endif
#if MF_SPRITE_GALLERY
#include "gallery.h"
#endif

static mf_game game;
static int explosion=-1,spark_explosion;
static int street[5],buck[MF_BUCK_FRAMES],chuck[MF_BUCK_FRAMES],enemy[MF_ENEMY_FRAMES],bat[2][MF_BAT_FRAMES],bat_legs,air_legs[3],normal_lower[MF_NORMAL_LOWERS],torch_art[2][3],flame[4],embers[2],charge_cue,drum[3],shadow,spark,bar,panel;
static jo_palette street_palette,buck_palette,chuck_palette,enemy_palette,burn_palette,fire_palette;
static int asset_error,asset_stage,asset_index,overlay=-1;
#if MF_SPRITE_GALLERY
static int asset_diagnostic_view;
#endif
static char asset_item[16];
static int core_init_complete;
static void asset_failure(int code,const char *name,int index)
{
    int i;
    if(asset_error)return;
    asset_error=code;asset_index=index;
    for(i=0;i<15 && name[i];i++)asset_item[i]=name[i];
    asset_item[i]=0;
}
static int create_palette(jo_palette *palette,int code)
{
    palette->id=-1;palette->data=JO_NULL;jo_create_palette(palette);
    if(!palette->data || palette->id<0 || palette->id>=8) {
        asset_failure(code,"PALETTE",0);return 0;
    }
    return 1;
}
static int load_indexed(const char *name,int index)
{
    int id=jo_sprite_add_tga(JO_ROOT_DIR,name,1);
    if(id<0)asset_failure(asset_stage,name,index);
    return id;
}
static void draw_asset_diagnostics(void)
{
    jo_print(1,2,asset_error?"ASSET INITIALIZATION FAILED":"ASSET INITIALIZATION OK");
    jo_printf(1,4,"ASSET E%03d ITEM %s I%d",asset_error,asset_item,asset_index);
    jo_printf(1,5,"JO CORE%d FS ROOT READY%d",core_init_complete,
        mf_street_diagnostics()->root_executable>=0 && mf_street_diagnostics()->root_street>=0);
    mf_street_diagnostic_draw(7);
    jo_printf(1,17,"MUSIC READY%d",mf_music_ready());
    jo_printf(1,19,"VDP2 %d  GALLERY %d",MF_VDP2_STREET,MF_SPRITE_GALLERY);
    jo_printf(1,21,"BUILD %.12s",MF_BUILD_COMMIT);
    jo_printf(1,22,"SRC %.12s",MF_BUILD_SOURCE);
    if(!asset_error)jo_print(1,25,"C RETURN TO GALLERY");
}
static volatile unsigned int vblanks;
static unsigned int last_vblank,last_input_vblank=~0u,pending[2];
static mf_input sampled_input[2];
static void clock_tick(void)
{
    ++vblanks;
#if MF_CITY_NEON
    #if MF_LEVEL2_WINGSUIT
    if(!stage2_owned)
    #endif
    mf_street_animate(vblanks);
#endif
}
static int load(const char *name)
{
    int id=jo_sprite_add_tga(JO_ROOT_DIR,name,JO_COLOR_RGB(255,0,255));
    if(id<0)asset_failure(asset_stage,name,0);
    return id;
}
static void load_assets(void)
{
    int i;
    static const char *bu[]={"BU00.TGA","BU01.TGA","BU02.TGA","BU03.TGA","BU04.TGA","BU05.TGA","BU06.TGA","BU07.TGA","BU08.TGA","BU09.TGA","BU10.TGA","BU11.TGA","BU12.TGA","BU13.TGA","BU14.TGA"};
    static const char *dr[]={"DR0.TGA","DR1.TGA","DR2.TGA"};
    jo_color *pixels;
    jo_img img;
    if(!create_palette(&street_palette,100))return;
    if(!mf_street_load(&street_palette,street)){asset_failure(110,"STREET",0);return;}
    if(!create_palette(&buck_palette,200))return;
    asset_stage=210;
    jo_set_tga_default_palette(&buck_palette);
    for(i=0;i<MF_BUCK_FRAMES;i++) {
        /* The pinned 8-bit TGA loader adds one to raw indices. Raw zero
           is our magenta key, so transparent palette index is one. */
/* PLAYERHURT BEGIN */
        #if MF_PLAYER_HURT
        if(i==8){buck[i]=-1;continue;}
/* PLAYERDEATH BEGIN */
#if MF_PLAYER_DEATH
        if(i==13){buck[i]=-1;continue;}
#endif
/* PLAYERDEATH END */
        #endif
/* PLAYERHURT END */
#if MF_ARCADE_FX
        if(i==1) {
            jo_set_tga_default_palette(JO_NULL);
            explosion=load("EXPLODE.TGA");
            jo_set_tga_default_palette(&buck_palette);
            buck[i]=-1;
            if(explosion<0 || jo_sprite_get_width(explosion)!=32 || jo_sprite_get_height(explosion)!=32)
                asset_failure(211,"EXPLODE.TGA",i);
            continue;
        }
#endif
#if MF_LEGACY_SPRITE_PHASE2
        buck[i]=-1; /* All fallback pieces are superseded; EXPLODE above stays. */
#else
        if(MF_HQ_JUMP && (i==11 || i==12 || i==14))buck[i]=-1;
        else buck[i]=load_indexed(bu[i],i);
#endif
        (void)bu;

    }
#if MF_LEGACY_SPRITE_CLEANUP
    /* No production input creates the old planted/aerial bat. Keep explicit
       invalid IDs instead of accidentally treating static zero as a sprite. */
    for(i=0;i<MF_BAT_FRAMES;i++)bat[0][i]=-1;
    bat_legs=-1;for(i=0;i<3;i++)air_legs[i]=-1;
#else
    for(i=0;i<MF_BAT_FRAMES;i++) {
        char name[12]="BT00.TGA";name[2]='0'+i/10;name[3]='0'+i%10;
        bat[0][i]=load_indexed(name,i);
    }
    bat_legs=load_indexed("LEGS.TGA",0);
    for(i=0;i<3;i++) {
        char name[12]="AL0.TGA";name[2]='0'+i;
        air_legs[i]=load_indexed(name,i);
    }
#endif
    for(i=0;i<MF_NORMAL_LOWERS;i++) {
#if MF_LEGACY_SPRITE_PHASE2
        normal_lower[i]=-1;continue;
#endif
        char name[12]="NL00.TGA";name[2]='0'+i/10;name[3]='0'+i%10;
/* PLAYERDEATH BEGIN */
#if MF_PLAYER_DEATH
        if(i==13){normal_lower[i]=-1;continue;}
#endif
/* PLAYERDEATH END */
        if(MF_HQ_JUMP && (i==11 || i==12 || i==14))normal_lower[i]=-1;
        else normal_lower[i]=load_indexed(name,i);
    }
    #if !MF_HQ_TORCH
    for(i=0;i<3;i++) {
        char name[12]="TU0.TGA";name[2]='0'+i;
        torch_art[0][i]=load_indexed(name,i);
    }
    #endif
    if(!create_palette(&chuck_palette,300))return;
    asset_stage=310;
    jo_set_tga_default_palette(&chuck_palette);
    for(i=0;i<MF_BUCK_FRAMES;i++) {
        char name[12]="CH00.TGA";
#if MF_LEGACY_SPRITE_PHASE2
        chuck[i]=-1;continue;
#endif
        name[2]='0'+i/10;name[3]='0'+i%10;
/* PLAYERHURT BEGIN */
        #if MF_PLAYER_HURT
        if(i==8){chuck[i]=-1;continue;}
/* PLAYERDEATH BEGIN */
#if MF_PLAYER_DEATH
        if(i==13){chuck[i]=-1;continue;}
#endif
/* PLAYERDEATH END */
        #endif
/* PLAYERHURT END */
        if(MF_HQ_JUMP && (i==11 || i==12 || i==14))chuck[i]=-1;
        else chuck[i]=load_indexed(name,i);
    }
#if MF_LEGACY_SPRITE_CLEANUP
    for(i=0;i<MF_BAT_FRAMES;i++)bat[1][i]=-1;
#else
    for(i=0;i<MF_BAT_FRAMES;i++) {
        char name[12]="CT00.TGA";name[2]='0'+i/10;name[3]='0'+i%10;
        bat[1][i]=load_indexed(name,i);
    }
#endif
    #if !MF_HQ_TORCH
    for(i=0;i<3;i++) {
        char name[12]="TC0.TGA";name[2]='0'+i;
        torch_art[1][i]=load_indexed(name,i);
    }
    #endif
    if(!create_palette(&enemy_palette,400))return;
    asset_stage=410;
    jo_set_tga_default_palette(&enemy_palette);
    for(i=0;i<MF_ENEMY_FRAMES;i++) {
        char name[12]="EN00.TGA";
        name[2]='0'+i/10;name[3]='0'+i%10;
/* CPHQ BEGIN */
        #if MF_CP_HQ_COMBAT
        enemy[i]=-1; /* Every existing state is covered by the shared HQ bank. */
        (void)name;
        #else
/* CPHQ END */
        enemy[i]=load_indexed(name,i);
/* CPHQ BEGIN */
        #endif
/* CPHQ END */

    }
    #if MF_CORPORATE_PUNK && !MF_ENEMY_SPRITE_BANKS
    asset_stage=415;
    if(!mf_corporate_load(&enemy_palette)){asset_failure(415,"CP TEXTURES",0);return;}
    #endif
    /* Palette-only warm flashes: no duplicated enemy texture bank. */
    if(!create_palette(&burn_palette,420))return;
#if !MF_ENEMY_SPRITE_BANKS
    for(i=0;i<255;i++) {
        unsigned c=enemy_palette.data[i];unsigned r=(c&31)+10,g=((c>>5)&31)+3,b=((c>>10)&31)/2;
        if(r>31)r=31;
        if(g>31)g=31;
        burn_palette.data[i]=0x8000|r|(g<<5)|(b<<10);
    }
#endif
    if(!create_palette(&fire_palette,500))return;
    asset_stage=510;jo_set_tga_default_palette(&fire_palette);
    for(i=0;i<4;i++) {
        char name[12]="FL0.TGA";name[2]='0'+i;
        flame[i]=load_indexed(name,i);
    }
    embers[0]=load_indexed("EM0.TGA",0);embers[1]=load_indexed("EM1.TGA",1);
    charge_cue=load_indexed("CHARGE.TGA",0);

    jo_set_tga_default_palette(JO_NULL);
    asset_stage=600;
    for(i=0;i<3;i++) drum[i]=load(dr[i]);
    shadow=load("SHADOW.TGA"); spark=load("HIT.TGA");
    /* Small opaque HUD and title panel; all texture allocation is budgeted. */
    pixels=jo_malloc(256*40*sizeof(*pixels));
    if(!pixels) {asset_failure(610,"HUD MEMORY",0);return;}
    img.width=80; img.height=8; img.data=pixels;
    for(i=0;i<80*8;i++) pixels[i]=(i/80==0 || i/80==7 || i%80==0 || i%80==79)?JO_COLOR_RGB(164,201,195):JO_COLOR_RGB(64,187,155);
    bar=jo_sprite_add(&img);
    if(bar<0)asset_failure(620,"HUD BAR",0);
    img.width=MF_HUD_PANEL_WIDTH; img.height=40;
    for(i=0;i<MF_HUD_PANEL_WIDTH*40;i++) pixels[i]=(i/MF_HUD_PANEL_WIDTH==0 || i/MF_HUD_PANEL_WIDTH==39)?JO_COLOR_RGB(124,66,112):JO_COLOR_RGB(12,18,34);
    panel=jo_sprite_add(&img);
    if(panel<0)asset_failure(621,"HUD PANEL",0);
    jo_free(pixels);
    mf_music_init();
#if MF_SPRITE_GALLERY
    if(!asset_error && !mf_gallery_load(panel))asset_failure(700,"GALLERY",0);
#if MF_HQ_TORCH
    if(!asset_error && !mf_hq_torch_load(enemy_palette.id))asset_failure(710,"HQ TORCH",0);
#if MF_HQ_JUMP
    if(!asset_error && !mf_hq_jump_load())asset_failure(720,"HQ JUMP",0);
/* PLAYERHURT BEGIN */
#if MF_PLAYER_HURT
    if(!asset_error && !mf_player_hurt_load())asset_failure(721,"HQ HURT",0);
/* PLAYERDEATH BEGIN */
#if MF_PLAYER_DEATH
    if(!asset_error && !mf_player_death_load())asset_failure(722,"HQ DEATH",0);
#endif
/* PLAYERDEATH END */
#endif
/* PLAYERHURT END */
#endif
#endif
#if MF_PUNCH_COMBO
    if(!asset_error && !mf_cross_load())asset_failure(730,"CROSS",0);
#if MF_ARCADE_FX
    if(!asset_error && (jo_get_last_sprite_id()+1!=MF_FX_DEFINITIONS-MF_RICKY_EXTRA_DEFS-(MF_ENEMY_SPRITE_BANKS?MF_ENEMY_CP_DEFS:0) ||
                       mf_animation_texture_bytes()!=MF_FX_TEXTURE_BYTES-MF_RICKY_EXTRA_BYTES-MF_ENEMY_DEFERRED_BYTES))
        asset_failure(731,"FX BUDGET",0);
#endif
#endif
#if MF_ENEMY_SPRITE_BANKS
#if MF_RICKY_ENEMY
    if(!asset_error && !mf_ricky_palette(&buck_palette,&chuck_palette))asset_failure(734,"RICKY PALETTE",0);
    if(!asset_error && !mf_enemy_bank_boot(&mf_ricky_bank_spec,&enemy_palette))
#else
    if(!asset_error && !mf_enemy_bank_boot(&mf_corporate_bank_spec,&enemy_palette))
#endif
        asset_failure(732,"ENEMY BANK",mf_enemy_bank_diagnostics()->error);
    if(!asset_error) {
    for(i=0;i<255;i++) {
        unsigned c=enemy_palette.data[i];unsigned r=(c&31)+10,g=((c>>5)&31)+3,b=((c>>10)&31)/2;
        if(r>31)r=31;
        if(g>31)g=31;
        burn_palette.data[i]=0x8000|r|(g<<5)|(b<<10);
    }
        if(jo_get_last_sprite_id()+1!=MF_FX_DEFINITIONS || mf_animation_texture_bytes()!=MF_FX_TEXTURE_BYTES)
            asset_failure(733,"BANK BUDGET",0);
    }
#endif
#if MF_PARALLAX_DEMO
    if(!asset_error && !mf_parallax_load())asset_failure(800,"PARALLAX",mf_parallax_error());
#endif
#endif
}
static int depth_key(int ground,int tag) {return 650-2*ground+tag;}
static void draw_shadow(int x,int ground,int height)
{
    int scale=65536-height*180;
    jo_sprite_change_sprite_scale_xy_fixed(scale,65536);
    jo_sprite_draw3D(shadow,x-160,ground-2-120,400);
    jo_sprite_restore_sprite_scale();
}
static void health_bar(int x,int y,int width,int value,int maximum)
{
    int fill=width*value/maximum;
    jo_sprite_change_sprite_scale_xy_fixed(width*65536/MF_HUD_PANEL_WIDTH,8*65536/40);
    jo_sprite_draw3D(panel,x+width/2-160,y+4-120,185);
    if(fill>0) {
        jo_sprite_change_sprite_scale_xy_fixed(fill*65536/80,65536);
        jo_sprite_draw3D(bar,x+fill/2-160,y+4-120,180);
    }
    jo_sprite_restore_sprite_scale();
}
static void draw_anchored(int sprite,int x,int y,const short *anchor,int facing,int depth)
{
    jo_sprite_draw3D2(sprite,x-(facing>0?anchor[0]:jo_sprite_get_width(sprite)-anchor[0]),y-anchor[1],depth);
}
static void draw_game(void)
{
    int i,j,x,y,depth,mode,engaged;
    mf_street_draw(street,street_palette.id,game.camera);
    for(i=0;i<3;i++) {
        mf_drum *d=&game.drums[i];x=d->x/256-game.camera;y=d->y/256;depth=depth_key(y,0);
        if(x<-32 || x>352)continue;
        if(d->hp || d->respawn<20)draw_shadow(x,y,0);
        if(d->hp && !(d->flash&1))jo_sprite_draw3D2(drum[3-d->hp],x-16,y-46,depth);
        mf_fx_draw_drum(d,spark,explosion,x,y,depth);
    }
    for(j=0;j<MF_ENEMIES;j++) {
        mf_enemy *e=&game.enemies[j];int frame=mf_enemy_frame(&game,j);
        x=e->x/256-game.camera;y=e->y/256;
        if(e->state==MF_ENEMY_ABSENT || x<-100 || x>420)continue;
#if MF_RICKY_ENEMY
        draw_shadow(x,y,game.enemy_class[j]==MF_ENEMY_RICKY && game.ricky_jump[j].active && e->state==MF_ENEMY_ACTIVE?24+game.ricky_jump[j].height:0);
#else
        draw_shadow(x,y,0);
#endif
        if(e->facing<0)jo_sprite_enable_horizontal_flip();
        jo_sprite_set_palette(e->fire_flash?burn_palette.id:enemy_palette.id);i=enemy[frame];
        #if MF_RICKY_ENEMY
        if(game.enemy_class[j]==MF_ENEMY_RICKY)mf_ricky_draw(&game,j,x,y,depth_key(y,0));
        else
        #endif
        #if MF_CORPORATE_PUNK
        if(!mf_corporate_draw(&game,j,x,y,depth_key(y,0)))
        #endif
        jo_sprite_draw3D2(i,x-(e->facing>0?enemy_anchor[frame][0]:jo_sprite_get_width(i)-enemy_anchor[frame][0]),
                         y-enemy_anchor[frame][1]-MF_CORPORATE_PUNK,depth_key(y,0));
        jo_sprite_disable_horizontal_flip();
        if(e->burn && e->hp>0){
            jo_sprite_set_palette(fire_palette.id);
            jo_sprite_draw3D2(embers[(game.ticks/4)%2],x-13,y-58,depth_key(y,-1));
            jo_sprite_draw3D2(embers[(game.ticks/4+1)%2],x+7,y-42,depth_key(y,-1));
        }
    }
    for(j=0;j<MF_PLAYERS;j++) {
        mf_player *p=&game.players[j];int frame=mf_player_frame(&game,j);
        const short (*anchor)[2]=j?chuck_anchor:buck_anchor;
        if(!p->active)continue;
        x=p->x/256-game.camera;y=p->y/256;draw_shadow(x,y,p->height/256);
/* PLAYERHURT BEGIN */
#if MF_PLAYER_HURT
        int hurt_visible=p->health>0 && p->hurt>0;
#else
        int hurt_visible=0;
#endif
/* PLAYERHURT END */
        if(hurt_visible || !p->health || !p->invulnerable || p->invulnerable>=112 || (game.ticks&4)) {
            if(p->facing<0)jo_sprite_enable_horizontal_flip();
#if MF_PLAYABLE_ANIMATION
/* PLAYERHURT BEGIN */
#if MF_PLAYER_HURT
/* PLAYERDEATH BEGIN */
#if MF_PLAYER_DEATH
            if(mf_player_death_draw(&game,j,x,y,depth_key(y,0))) {
                /* Reuse the unmodified simulation defeat clock. */
            }else
#endif
/* PLAYERDEATH END */
            if(mf_player_hurt_draw(&game,j,x,y,depth_key(y,0))) {
                /* Existing hurt and invulnerability clock; no simulation changes. */
            }else
#endif
/* PLAYERHURT END */
#if MF_HQ_JUMP
            if(mf_hq_jump_draw(&game,j,x,y,depth_key(y,0))) {
                /* Pure phase selection; existing world root and shadow. */
            }else
#endif
#if MF_COMBAT_ANIMATION
            if(mf_combat_prototype_draw(&game,j,x,y,depth_key(y,0))) {
                /* Limited high-detail key-pose study; simulation is untouched. */
            }else
#endif
            if(mf_player_animation_draw(&game,j,x,y,depth_key(y,0))) {
                /* Complete high-detail idle/walk, same simulation root/depth. */
            }else
#endif
            if(p->torch && p->health && !p->hurt){
                int pose=p->torch==MF_TORCH_EQUIP?0:(p->torch==MF_TORCH_FIRE?1:2);
#if MF_HQ_TORCH
                mf_hq_torch_draw(&game,j,x,y,depth_key(y,0));
                (void)pose;
                if(p->facing<0)jo_sprite_enable_horizontal_flip();
#else
                int lower=buck_lower_for_frame[p->moving?2+(p->walk/5)%6:0];
                jo_sprite_set_palette(buck_palette.id);
                draw_anchored(normal_lower[lower],x,y,normal_lower_anchor[lower],p->facing,depth_key(y,0));
                jo_sprite_set_palette(j?chuck_palette.id:buck_palette.id);
                draw_anchored(torch_art[j][pose],x,y,j?chuck_torch_anchor[pose]:buck_torch_anchor[pose],p->facing,depth_key(y,-1));
                #endif
            }else if(p->bat && p->attack && p->health && !p->hurt) {
                frame=mf_bat_frame(p);
                jo_sprite_set_palette(buck_palette.id);
                if(p->attack_air && p->height){
                    int leg=air_lower_for_frame[frame];
                    draw_anchored(air_legs[leg],x,y-p->height/256,air_legs_anchor[leg],p->facing,depth_key(y,0));
                }else draw_anchored(bat_legs,x,y,bat_legs_anchor,p->facing,depth_key(y,0));
                jo_sprite_set_palette(j?chuck_palette.id:buck_palette.id);
                draw_anchored(bat[j][frame],x,y-p->height/256,j?chuck_bat_anchor[frame]:buck_bat_anchor[frame],p->facing,depth_key(y,-1));
#if MF_RUNNING_BAT_VISUALS
                if(game.running_bat[j].active)mf_running_bat_metal_draw(j,frame,x,y-p->height/256,p->facing,depth_key(y,-2));
#endif
            }else{
                int lower=j?chuck_lower_for_frame[frame]:buck_lower_for_frame[frame];
                jo_sprite_set_palette(buck_palette.id);
                draw_anchored(normal_lower[lower],x,y-p->height/256,normal_lower_anchor[lower],p->facing,depth_key(y,0));
                i=j?chuck[frame]:buck[frame];jo_sprite_set_palette(j?chuck_palette.id:buck_palette.id);
                draw_anchored(i,x,y-p->height/256,anchor[frame],p->facing,depth_key(y,0));
            }
            jo_sprite_disable_horizontal_flip();
        }
        /* Flame remains visible over the unchanged hurt pose and through
           invulnerability flicker, using exactly the collision eligibility. */
        if(mf_torch_active(p)) {
            int f=(game.ticks/3+j)%4;jo_sprite_set_palette(fire_palette.id);
            if(p->facing<0)jo_sprite_enable_horizontal_flip();
            draw_anchored(flame[f],x,y,flame_anchor[f],p->facing,depth_key(y,-2));
            jo_sprite_disable_horizontal_flip();
        }
    }
    for(j=0;j<MF_PLAYERS;j++)if(game.players[j].charge>=MF_TORCH_CUE_TICKS && (game.ticks&4)){
        mf_player *p=&game.players[j];jo_sprite_set_palette(fire_palette.id);
        jo_sprite_draw3D2(charge_cue,p->x/256-game.camera+p->facing*20-4,p->y/256-49,depth_key(p->y/256,-2));
    }
    mf_fx_draw_spark(&game,spark,explosion,spark_explosion,depth_key(game.spark_y,-1));
    health_bar(16,25,80,game.players[0].health,100);
    jo_print(2,1,"BUCK");jo_printf(14,1,"%06d",game.score);
    jo_printf(2,2,"HP %03d",game.players[0].health);
    if(game.players[1].active) {
        jo_print(27,1,"CHUCK       ");jo_printf(27,2,"HP %03d",game.players[1].health);
        health_bar(216,25,88,game.players[1].health,100);
    }else{jo_print(24,1,"P2 PRESS START");jo_print(27,2,"        ");}
    jo_clear_screen_line(5);
    for(j=0;j<MF_ENEMIES;j++) {
        mf_enemy *e=&game.enemies[j];
        engaged=e->state!=MF_ENEMY_ABSENT && e->x/256>game.camera-40 && e->x/256<game.camera+360;
        if(engaged) {
            health_bar(16+j*208,50,80,e->hp,MF_ENEMY_MAX_HP);
            jo_printf(2+j*26,5,"SUIT%d %d",j+1,e->hp);
            if(e->state==MF_ENEMY_WINDUP)jo_print(10+j*26,5,"!");
        }
    }
#if MF_LEVEL1_STAGE_CLEAR
#if MF_LEVEL1_WORLD_FLOW
    jo_printf(14,3,"KOs %04d",game.stage_kills);
    jo_print(14,4,game.camera==MF_WORLD_CAMERA_MAX?"TEST END   ":game.camera>320?"NEON STRIP ":"           ");
#else
    jo_printf(14,3,"KOs %02d/40",game.stage_kills);
#endif
#endif
    mode=!game.started?1:(game.paused?2:0);
#if MF_LEVEL1_STAGE_CLEAR
    if(!mode && game.stage>=MF_STAGE_CLEAR)mode=game.stage==MF_STAGE_CLEAR?3:4;
#endif
    if(mode) {
#if MF_HUD_PANEL_MEMORY
        /* Original SGL center-zoom uses size-1 and truncates the half-size:
           CMDCTRL=0xa01, A=(0,64), B=(255,39) -> x33..288, y165..204.
           Match those inclusive edges without the HV angle workaround. */
        static const jo_pos2D_fixed corners[4]={
            {-127*65536,45*65536},{128*65536,45*65536},
            {128*65536,84*65536},{-127*65536,84*65536}
        };
        jo_sprite_draw_4p_fixed(panel,corners,180*65536,true);
#else
        jo_sprite_draw3D2(panel,32,164,180);
#endif
    }
    if(mode!=overlay) {
        jo_clear_screen_line(21);jo_clear_screen_line(23);
        if(mode==1) {jo_print(10,21,"MULLET FORCE");jo_print(9,23,"PRESS START TO PLAY");}
        else if(mode==2) {jo_print(16,21,"PAUSED");jo_print(9,23,"START TO CONTINUE");}
#if MF_LEVEL1_STAGE_CLEAR
        else if(mode==3)jo_print(13,21,"STAGE CLEAR");
        else if(mode==4){jo_print(15,21,"LEVEL 2");jo_print(13,23,"COMING NEXT");}
#endif
        overlay=mode;
    }
    jo_print(2,28,"D-PAD MOVE A HIT B JUMP HOLD A1S TORCH");
    jo_print(2,29,"FWD FWD+A BAT  C DIAGNOSTICS");
    if(game.debug) {
        for(j=0;j<2;j++) {
            mf_input *in=&sampled_input[j];
            jo_printf(1,8+j*2,"P%d S%02d ID%02x T%d OK%d RAW%04x",j+1,in->sdk_slot,in->device_id,in->type,in->connected,in->raw);
            jo_printf(1,9+j*2,"PUSH%04x HELD%02x EDGE%02x      ",in->raw_pressed,in->held,in->pressed);
        }
        jo_printf(1,12,"S0-5 %02x %02x %02x %02x %02x %02x",jo_inputs[0].id,jo_inputs[1].id,jo_inputs[2].id,jo_inputs[3].id,jo_inputs[4].id,jo_inputs[5].id);
        jo_printf(1,13,"S6-B %02x %02x %02x %02x %02x %02x",jo_inputs[6].id,jo_inputs[7].id,jo_inputs[8].id,jo_inputs[9].id,jo_inputs[10].id,jo_inputs[11].id);
        jo_printf(1,14,"P2 ACTIVE%d X%03d Y%03d BAT%d   ",game.players[1].active,game.players[1].x/256,game.players[1].y/256,game.players[1].bat);
        jo_printf(1,15,"BUILD %.12s SRC %.8s",MF_BUILD_COMMIT,MF_BUILD_SOURCE);
        jo_printf(1,16,"NATIVE MUSIC READY %d",mf_music_ready());
#if MF_PLAYABLE_ANIMATION
        jo_printf(1,17,"HIGH DETAIL MOVEMENT B%02d C%02d",mf_player_animation_pose(&game,0),mf_player_animation_pose(&game,1));
        jo_printf(1,18,"VDP1 %u/458488",mf_animation_texture_bytes());
#endif
    }else {
        for(i=8;i<=16;i++)jo_clear_screen_line(i);
#if MF_PLAYABLE_ANIMATION
        jo_clear_screen_line(17);jo_clear_screen_line(18);
#endif
    }

}
static void update(void)
{
    unsigned now,steps,i,j,held[2],pressed[2];
    /* Jo polls peripherals during VBlank even before Chuck joins. Sample its
       active-low push fields only once per VBlank, not once per render callback. */
    now=vblanks;
    if(now!=last_input_vblank){
        for(j=0;j<2;j++){
            sampled_input[j]=mf_input_read_port(j);
            if(!sampled_input[j].connected)pending[j]=0;else pending[j]|=sampled_input[j].pressed;
        }
        last_input_vblank=now;
    }
#if MF_ENEMY_SPRITE_BANKS
    if(!asset_error && !mf_enemy_bank_ready() && !stage2_owned) {
        unsigned state=mf_enemy_bank_service(now);
        now=vblanks;last_vblank=now;pending[0]=pending[1]=0;
        mf_music_update(game.started,game.paused,0,now);
        if(state!=MF_BANK_READY) {
            if(state==MF_BANK_FAILED)jo_printf(3,12,"ENEMY BANK FAILED E%u",mf_enemy_bank_diagnostics()->error);
            return; /* No sprite submissions while draining/loading/failed. */
        }
    }
#endif
    #if MF_LEVEL2_WINGSUIT
    if(stage2_owned){mf_ws_runtime_frame(sampled_input,pending,now);return;}
    #endif
    if(asset_error) {draw_asset_diagnostics();return;}
#if MF_SPRITE_GALLERY
    if(mf_gallery_active() && ((pending[0]|pending[1])&MF_C)) {
        asset_diagnostic_view=!asset_diagnostic_view;
        pending[0]&=~MF_C;pending[1]&=~MF_C;jo_clear_screen();
    }
    if(asset_diagnostic_view) {
        pending[0]=pending[1]=0;last_vblank=now;draw_asset_diagnostics();return;
    }
#endif
#if MF_SPRITE_GALLERY
    if(mf_gallery_active()) {
        unsigned gallery_pressed=pending[0]|pending[1];
        pending[0]=pending[1]=0;
#if MF_ANIMATION_PREVIEW
        if(gallery_pressed&MF_DOWN) {
#if MF_PARALLAX_DEMO
            if(mf_parallax_active())mf_parallax_leave();
#endif
#if MF_SWAGGER_WALK || MF_ORIGINAL_THREE_WALK
            if(!mf_animation_active())jo_print(2,23,MF_RUN_BAT?"RESIDENT WALK / RUN REVIEW":"LOADING SIX-FRAME REVIEW BANK");
#endif
            if(!mf_animation_toggle()){asset_failure(710,"REVIEW BANK",0);return;}jo_clear_screen();
        }
        if(mf_animation_active()) {
            if(gallery_pressed&MF_START){mf_animation_leave();jo_clear_screen();}
            else {
                mf_animation_update(sampled_input[0].held|sampled_input[1].held,gallery_pressed,now-last_vblank);last_vblank=now;
                mf_animation_draw(street,street_palette.id);return;
            }
        }
#endif
#if MF_PARALLAX_DEMO
        if(gallery_pressed&MF_B) {
            if(mf_parallax_active())mf_parallax_leave();else mf_parallax_enter();
            jo_clear_screen();
        }
        if((gallery_pressed&MF_START) && mf_parallax_active())mf_parallax_leave();
        mf_parallax_update(sampled_input[0].held|sampled_input[1].held,now-last_vblank);
#endif
        last_vblank=now;
        if(mf_gallery_update(gallery_pressed)) {
            mf_gallery_draw(street,street_palette.id);
#if MF_PARALLAX_DEMO
            if(mf_parallax_active())mf_parallax_labels();
            else jo_printf(2,27,"B PARALLAX PREVIEW  ERROR %03d",mf_parallax_error());
#endif
#if MF_ANIMATION_PREVIEW
#if MF_ORIGINAL_THREE_WALK
            jo_print(1,25,"ORIGINAL THREE / DOWN SIX REVIEW");
#elif MF_SWAGGER_WALK
            jo_print(1,25,"SWAGGER GAME / DOWN LOAD SIX REVIEW");
#else
            jo_print(2,25,"DOWN ANIMATION POLISH REVIEW");
#endif
#endif
            return;
        }
        jo_clear_screen();overlay=-1;
        draw_game();return;
    }
#endif
    for(j=0;j<2;j++)held[j]=sampled_input[j].held;
    steps=now-last_vblank;last_vblank=now;
    /* Fixed NTSC VBlank clock, including simultaneous controller edges. */
    if(steps>6)steps=6;
    for(i=0;i<steps;i++) {
        for(j=0;j<2;j++){pressed[j]=pending[j];pending[j]=0;}
#if MF_PLAYABLE_ANIMATION || MF_CORPORATE_PUNK
        int before_tick=game.ticks;
#endif
#if MF_ARCADE_FX
        unsigned previous_hits[MF_PLAYERS];
        for(j=0;j<MF_PLAYERS;j++)previous_hits[j]=(unsigned)game.players[j].hit_mask;
#endif
#if MF_LEVEL2_WINGSUIT
        mf_dev_stage_skip(&game,pressed);
#endif
        mf_game_step_inputs(&game,held,pressed,(sampled_input[0].connected?1u:0u)|(sampled_input[1].connected?2u:0u));
#if MF_ARCADE_FX
        spark_explosion=mf_fx_spark_explosion(&game,previous_hits,spark_explosion);
#endif
#if MF_PLAYABLE_ANIMATION
        if(game.ticks!=before_tick)mf_player_animation_step(&game);
#endif
#if MF_CORPORATE_PUNK
        if(game.ticks!=before_tick)mf_corporate_step(&game);
#endif
        mf_music_update(game.started,game.paused,game.events,now);
#if MF_LEVEL2_WINGSUIT
        if(game.stage==MF_STAGE_LEVEL2_ENTRY){
#if MF_ENEMY_SPRITE_BANKS
            mf_enemy_bank_retire();
#endif
            stage2_owned=1;pending[0]=pending[1]=0;
            mf_ws_runtime_begin(game.players[1].active,&street_palette,now);return;
        }
#endif
    }
    draw_game();
}
void jo_main(void)
{
    jo_core_init(JO_COLOR_RGB(9,12,29));
    core_init_complete=1;
    jo_print(10,12,"LOADING NEON DISTRICT");
    load_assets();
    jo_clear_screen();
    mf_game_init(&game);
    jo_core_add_vblank_callback(clock_tick);
    last_vblank=vblanks;
#if MF_LEVEL2_WINGSUIT
    mf_ws_audio_trace_clock(&vblanks);
#endif
    jo_core_add_callback(update);
    jo_core_run();
}
