#include "build-info.h"
#if MF_LEVEL2_WINGSUIT
#include <jo/jo.h>
#include "wingsuit_runtime.h"
#include "wingsuit.h"
#include "wingsuit_audio.h"
#include <string.h>
static mf_wingsuit shooter;
static int ids[18]={-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1};
static int player_bank[2];
static const char restart_prompt[]="1P START TO RESTART";
static const char restart_clear[]="                   ";
typedef char restart_field_width_must_match[(sizeof(restart_prompt)==sizeof(restart_clear))?1:-1];
enum { WS_CENTER, WS_LEFT, WS_RIGHT };
static int phase,drain,title,error;
static unsigned previous;
static const char *failed_asset,*failed_reason;
static int failed_expected,failed_actual;
static int load_failure(const char *asset,const char *reason,int expected,int actual)
{
    failed_asset=asset;failed_reason=reason;
    failed_expected=expected;failed_actual=actual;return 0;
}
static char *read_asset(const char *name,int expected)
{
    int size=-1;char *data;
    if(GFS_NameToId((Sint8 *)name)<0){load_failure(name,"MISSING",expected,-1);return 0;}
    data=jo_fs_read_file(name,&size);
    if(!data){load_failure(name,"READ/ALLOC",expected,size);return 0;}
    if(size!=expected){load_failure(name,"LENGTH",expected,size);jo_free(data);return 0;}
    return data;
}
static jo_palette *background_palette;
/* These arenas are allocated once by the approved Level 1 profile. Ownership
   transfers here; no VDP2 allocator cursor or live pointer is invalidated. */
#ifndef MF_WS_SOUND_RAM
#define MF_WS_SOUND_RAM ((volatile unsigned short *)0x25a00000)
#endif
#define WS_CELLS ((void *)VDP2_VRAM_A0)
#define WS_MAP ((void *)VDP2_VRAM_B0)
#define WS_CELL_BYTES 2752
#define WS_MAP_BYTES 8192
#define WS_SPRITE_Z 100
#define WS_SCREEN_DISTANCE 160
#define WS_DEPTH_LEVEL 1
#define WS_FAR_Z 1024
/* Pinned SGL SpriteEntry rejects z <= screen_distance >> depth_level.
   These are render-sort parameters, not player/world coordinates. */
#if WS_SPRITE_Z <= (WS_SCREEN_DISTANCE >> WS_DEPTH_LEVEL) || WS_SPRITE_Z > WS_FAR_Z
#error Wingsuit sprite depth must be inside the configured SGL window
#endif
static int restore_sprite_state(void)
{
    /* These are the pinned SGL APIs; do not rebuild the engine or its texture
       table. SpriteEntry continues to reference Jo's existing definition array. */
    slSetSprTVMode(TV_320x240);
    slCurWindow(winFar);
    slFrameClipSize(320,240);
    if(!slWindow(0,0,319,239,WS_FAR_Z,160,120)){
        load_failure("VDP1","WINDOW",1,0);return 0;
    }
    slSetScreenDist(WS_SCREEN_DISTANCE*65536);
    slZdspLevel(WS_DEPTH_LEVEL);
    slSpriteColMode(SPR_PAL_RGB);
    slSpriteWinMode(OFF);
    slScrWindowModeSPR(0);
    slPrioritySpr0(4);slPrioritySpr1(4);slPrioritySpr2(4);slPrioritySpr3(4);
    slPrioritySpr4(4);slPrioritySpr5(4);slPrioritySpr6(4);slPrioritySpr7(4);
    slPriorityNbg1(1);slPriorityNbg0(7);
    /* slInitSprite in pinned LIBSGL.A installs PTMR=2 (automatic frame-change
       drawing). A sampled PTMR can be stopped/one-shot and is not a restart
       policy. SGL's normal core slSynch submits the fresh command list. */
    JO_VDP1_PTMR=2;
    return 1;
}
static int copy_file(const char *name,void *target,int expected)
{
    char *data=read_asset(name,expected);
    if(!data)return 0;
    jo_dma_copy(data,target,(unsigned)expected);jo_free(data);return 1;
}
static int texture(const char *name,int w,int h)
{
    int id;char *data=read_asset(name,w*h*2);jo_img image;
    if(!data)return -1;
    image.width=w;image.height=h;image.data=(jo_color *)data;
    id=jo_sprite_add(&image);jo_free(data);
    if(id<0)load_failure(name,"REGISTER",w*h*2,id);
    return id;
}
static void wipe(volatile unsigned short *p,unsigned bytes)
{unsigned i;for(i=0;i<bytes/2;i++)p[i]=0;}
static void audio_progress(const mf_ws_audio_diagnostic *d)
{
    /* Text VRAM updates identify a void SDK call even if it never returns. */
    jo_print(3,22,"                                   ");
    jo_printf(3,22,"AUDIO %02d %s",d->stage,d->operation);
}
static int load_resources(void)
{
    unsigned wait;
    int i;static const char *names[]={"WBUCK.BIN","WCHUCK.BIN","WDRONE.BIN","WSHOT.BIN","WHOST.BIN","WBOOM.BIN","WBUCKL.BIN","WBUCKR.BIN","WCHUCKL.BIN","WCHUCKR.BIN","WFL0.BIN","WFL1.BIN","WFL2.BIN","WFL3.BIN","WFO0.BIN","WFO1.BIN","WFO2.BIN","WFO3.BIN"};
    static const int widths[]={32,32,24,8,8,32,32,32,32,32,32,32,32,32,32,32,32,32};
    static const int heights[]={32,32,24,8,8,32,32,32,32,32,MF_WS_BEAM_SEGMENT_HEIGHT,MF_WS_BEAM_SEGMENT_HEIGHT,MF_WS_BEAM_SEGMENT_HEIGHT,MF_WS_BEAM_SEGMENT_HEIGHT,MF_WS_BEAM_ORIGIN_HEIGHT,MF_WS_BEAM_ORIGIN_HEIGHT,MF_WS_BEAM_ORIGIN_HEIGHT,MF_WS_BEAM_ORIGIN_HEIGHT};
    /* All prior commands have passed through three core slSynch barriers.
       No sprites were submitted during them; no slave rendering is enabled. */
    if(!background_palette || background_palette->id!=1 || !background_palette->data){load_failure("CRAM","PALETTE",1,-1);return 100;}
    /* Stop automatic VDP1 restarts, then require the current command list to
       finish. A timeout leaves VDP1 stopped and displays a text-only error. */
    JO_VDP1_PTMR=0;
    for(wait=0;wait<1000000u && !(JO_VDP1_EDSR&2u);++wait){}
    if(!(JO_VDP1_EDSR&2u)){load_failure("VDP1","BUSY",2,JO_VDP1_EDSR);return 105;}
    jo_sprite_free_all();
    if(jo_get_last_sprite_id()!=-1){load_failure("VDP1","RESET",-1,jo_get_last_sprite_id());return 101;}
    wipe((volatile unsigned short *)(JO_VDP1_VRAM+JO_VDP1_TEXTURE_DEF_BASE_ADDRESS),
         JO_VDP1_USER_AREA_END_ADDR-(JO_VDP1_VRAM+JO_VDP1_TEXTURE_DEF_BASE_ADDRESS));
    /* slSoundOffWait halts the 68000 before releasing its entire sample bank.
       A minimal stage-local barrel bank is initialized after the wipe. */
    slSoundOffWait();wipe(MF_WS_SOUND_RAM,0x80000);
    /* Keep SDK NBG0/text and back screen intact. Clear both stage-owned arenas,
       including the retired NBG2 skyline, before installing Level 2 tiles. */
    wipe((volatile unsigned short *)WS_CELLS,106496);
    wipe((volatile unsigned short *)WS_MAP,65536);
    wipe(background_palette->data,7*512);
    if(!copy_file("WCELL.BIN",WS_CELLS,WS_CELL_BYTES) ||
       !copy_file("WMAP.BIN",WS_MAP,WS_MAP_BYTES) ||
       !copy_file("WPAL.BIN",background_palette->data,32))return 102;
    for(i=0;i<18;i++){
        ids[i]=texture(names[i],widths[i],heights[i]);
        if(ids[i]!=i){if(!failed_asset)load_failure(names[i],"SPRITE ID",i,ids[i]);jo_sprite_free_all();for(i=0;i<18;i++)ids[i]=-1;return 103;}
    }
    if(!mf_ws_audio_load(read_asset,audio_progress)){
        const mf_ws_audio_diagnostic *d=mf_ws_audio_diagnostics();
        if(!failed_asset)load_failure("WDEATH BANK",d->operation,d->expected,d->actual);
        return 108;
    }
    slCharNbg1(COL_TYPE_256,CHAR_SIZE_1x1);
    slPageNbg1(WS_CELLS,0,PNB_1WORD|CN_12BIT);
    slPlaneNbg1(PL_SIZE_1x1);slMapNbg1(WS_MAP,WS_MAP,WS_MAP,WS_MAP);
    slZoomNbg1(65536,65536);slScrPosNbg1(0,0);
    slScrWindow0(48,0,271,239);slScrWindowModeNbg1(win0_IN);
    if(slScrAutoDisp(NBG0ON|NBG1ON|SPRON)<0){load_failure("VDP2","SCHEDULE",0,-1);return 104;}
    /* Establish sprite priority/RGB/window state after VDP2 scheduling, so it
       never depends on an inherited Level 1 configuration or an auto helper. */
    if(!restore_sprite_state())return 107;
    return 0;
}
static int load(void)
{
    int result;
    /* The pinned GFS table holds only 256 directory records. Resolve this
       early root entry once, then give all twenty-four reads a small private table. */
    if(GFS_NameToId((Sint8 *)"ALEVEL2")<0){
        load_failure("ALEVEL2","DIRECTORY",0,-1);return 106;
    }
    jo_fs_cd("ALEVEL2");
    result=load_resources();
    /* jo_fs_cd has no success return in the pinned SDK. Child file lookups
       diagnose a failed entry; always restore the parent after the attempt. */
    jo_fs_cd(JO_PARENT_DIR);
    return result;
}
void mf_ws_runtime_begin(int coop,jo_palette *background,unsigned now)
{
    mf_ws_init(&shooter,coop);background_palette=background;
    player_bank[0]=player_bank[1]=WS_CENTER;
    phase=1;drain=0;title=120;error=0;previous=now;
    failed_asset=failed_reason=0;failed_expected=failed_actual=-1;
    slScrDisp(NBG1OFF|NBG2OFF);jo_clear_screen();
}
static void draw(int id,int x,int y)
{jo_sprite_draw3D2(ids[id],x,y,WS_SPRITE_Z);}
static int bank_after_step(int old_x,const mf_ws_player *p,unsigned held,int was_game_over)
{
    int dx=!!(held&MF_RIGHT)-!!(held&MF_LEFT);
    if(was_game_over || shooter.game_over || shooter.paused || !p->active || !p->lives || p->respawn)return WS_CENTER;
    if(dx<0 && p->x<old_x)return WS_LEFT;
    if(dx>0 && p->x>old_x)return WS_RIGHT;
    return WS_CENTER;
}
static void render(void)
{
    int i;slScrPosNbg1(0,-shooter.scroll*65536);
    /* New bank uses raw RGB555, with a fresh default sprite attribute state. */
    jo_sprite_disable_horizontal_flip();jo_sprite_disable_vertical_flip();
    jo_sprite_disable_half_transparency();jo_sprite_disable_dark_filter();
    jo_sprite_disable_gouraud_shading();jo_sprite_restore_sprite_scale();jo_sprite_disable_clipping();
    for(i=0;i<2;i++)if(mf_ws_beam_active(&shooter,i)){
        int bottom=shooter.players[i].y/256-MF_WS_BEAM_EMITTER-MF_WS_BEAM_ORIGIN_HEIGHT;
        int frame=(shooter.ticks/3+i)&3;
        draw(14+frame,shooter.players[i].x/256-16,bottom);
        /* Tile one periodic body frame without gaps or a terminal tip. All
           segments share phase so the wrap remains seamless during animation.
           System clipping trims the uppermost segment at the playfield edge. */
        for(;bottom>MF_WS_BEAM_TOP;bottom-=MF_WS_BEAM_SEGMENT_HEIGHT)
            draw(10+frame,shooter.players[i].x/256-16,bottom-MF_WS_BEAM_SEGMENT_HEIGHT);
    }
    for(i=0;i<MF_WS_ENEMIES;i++){
        mf_ws_enemy *e=&shooter.enemies[i];
        if(e->active)draw(2,e->x/256-12,e->y/256-12);
        else if(e->explosion)draw(5,e->x/256-16,e->y/256-16);
    }
    for(i=0;i<MF_WS_SHOTS;i++)if(shooter.shots[i].active)draw(3,shooter.shots[i].x/256-4,shooter.shots[i].y/256-4);
    for(i=0;i<MF_WS_HOSTILE;i++)if(shooter.hostile[i].active)draw(4,shooter.hostile[i].x/256-4,shooter.hostile[i].y/256-4);
    for(i=0;i<2;i++){
        mf_ws_player *p=&shooter.players[i];int col=i?34:0;
        if(p->active && p->lives && !p->respawn && (!p->invulnerable || !(shooter.ticks&4))){
            static const int pose[2][3]={{0,6,7},{1,8,9}};
            draw(pose[i][player_bank[i]],p->x/256-16,p->y/256-16);
        }
        jo_print(col,2,i?"CHUCK":"BUCK");jo_print(col,3,i?"2P":"1P");
        jo_printf(col,6,"%05d",p->score%100000);jo_print(col,8,"LIVES");jo_printf(col,9,"%d",p->lives);
        jo_print(col,12,"WPN 1");
        if(i && !p->active){jo_print(col,16,"START");jo_print(col,17,"JOIN");}
        else {jo_print(col,16,"     ");jo_print(col,17,"    ");}
    }
    jo_print(12,14,shooter.game_over?"GAME OVER       ":(shooter.paused?"PAUSED          ":"                "));
    jo_print(10,16,shooter.game_over?restart_prompt:restart_clear);
}
void mf_ws_runtime_frame(const mf_input input[2],unsigned pressed[2],unsigned now)
{
    unsigned elapsed=now-previous,held[2]={input[0].held,input[1].held};unsigned conn=(input[0].connected?1u:0u)|(input[1].connected?2u:0u),i;
    previous=now;
    if(phase==1){
        pressed[0]=pressed[1]=0;
        /* A callback count alone is insufficient: count only real VBlanks. */
        if(elapsed && ++drain>=3){error=load();phase=error?4:2;jo_clear_screen();}
        return;
    }
    if(phase==4){
        jo_printf(3,10,"LEVEL 2 LOAD FAILED E%d",error);
        jo_printf(3,12,"ASSET %s",failed_asset?failed_asset:"UNKNOWN");
        jo_printf(3,13,"CAUSE %s",failed_reason?failed_reason:"UNKNOWN");
        jo_printf(3,15,"EXPECT %d GOT %d",failed_expected,failed_actual);
        jo_print(3,17,"DISC /ALEVEL2");return;
    }
    if(phase==2){
        mf_ws_audio_step(now,0); /* Preconfigure persistent flame controls during title. */
        jo_print(15,11,"LEVEL 2");jo_print(11,13,"WINGSUIT ASSAULT");
        pressed[0]=pressed[1]=0;
        title-=elapsed>6?6:(int)elapsed;
        if(title<=0){phase=3;jo_clear_screen();}return;
    }
    if(elapsed>6)elapsed=6;
    for(i=0;i<elapsed;i++){
        int j,was_game_over=shooter.game_over,old_x[2]={shooter.players[0].x,shooter.players[1].x};
        mf_ws_step(&shooter,held,pressed,conn);mf_ws_audio_events(shooter.deaths,shooter.shots_fired);pressed[0]=pressed[1]=0;
        for(j=0;j<2;j++)player_bank[j]=bank_after_step(old_x[j],&shooter.players[j],(conn&(1u<<j))?held[j]:0,was_game_over);
    }
    {
        unsigned focus=0;
        if(!shooter.paused)for(i=0;i<2;i++)if(mf_ws_beam_active(&shooter,i))focus|=1u<<i;
        mf_ws_audio_step(now,focus);
    }
    render();
    if(mf_ws_audio_fault())jo_printf(3,21,"AUDIO P%d STATUS %02X",mf_ws_audio_fault()>>8,mf_ws_audio_fault()&255);
}
#endif
