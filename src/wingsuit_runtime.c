#include "build-info.h"
#if MF_LEVEL2_WINGSUIT
#include <jo/jo.h>
#include "wingsuit_runtime.h"
#include "wingsuit.h"
#include <string.h>
static mf_wingsuit shooter;
static int ids[6]={-1,-1,-1,-1,-1,-1};
static int phase,drain,title,error;
static unsigned previous;
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
static int copy_file(const char *name,void *target,int expected)
{
    int size=0;char *data=jo_fs_read_file(name,&size);
    if(!data)return 0;
    if(size!=expected){jo_free(data);return 0;}
    jo_dma_copy(data,target,(unsigned)size);jo_free(data);return 1;
}
static int texture(const char *name,int w,int h)
{
    int size=0,id;char *data=jo_fs_read_file(name,&size);jo_img image;
    if(!data)return -1;
    if(size!=w*h*2){jo_free(data);return -1;}
    image.width=w;image.height=h;image.data=(jo_color *)data;
    id=jo_sprite_add(&image);jo_free(data);return id;
}
static void wipe(volatile unsigned short *p,unsigned bytes)
{unsigned i;for(i=0;i<bytes/2;i++)p[i]=0;}
static int load(void)
{
    unsigned trigger,wait;
    int i;static const char *names[]={"WBUCK.BIN","WCHUCK.BIN","WDRONE.BIN","WSHOT.BIN","WHOST.BIN","WBOOM.BIN"};
    static const int widths[]={32,32,24,8,8,32};
    /* All prior commands have passed through three core slSynch barriers.
       No sprites were submitted during them; no slave rendering is enabled. */
    if(!background_palette || background_palette->id!=1 || !background_palette->data)return 100;
    /* Stop automatic VDP1 restarts, then require the current command list to
       finish. A timeout leaves VDP1 stopped and displays a text-only error. */
    trigger=JO_VDP1_PTMR;JO_VDP1_PTMR=0;
    for(wait=0;wait<1000000u && !(JO_VDP1_EDSR&2u);++wait){}
    if(!(JO_VDP1_EDSR&2u))return 105;
    jo_sprite_free_all();
    if(jo_get_last_sprite_id()!=-1)return 101;
    wipe((volatile unsigned short *)(JO_VDP1_VRAM+JO_VDP1_TEXTURE_DEF_BASE_ADDRESS),
         JO_VDP1_USER_AREA_END_ADDR-(JO_VDP1_VRAM+JO_VDP1_TEXTURE_DEF_BASE_ADDRESS));
    /* slSoundOffWait halts the 68000 before releasing its entire sample bank.
       This prototype deliberately uses silent Level 2 audio. */
    slSoundOffWait();wipe(MF_WS_SOUND_RAM,0x80000);
    /* Keep SDK NBG0/text and back screen intact. Clear both stage-owned arenas,
       including the retired NBG2 skyline, before installing Level 2 tiles. */
    wipe((volatile unsigned short *)WS_CELLS,106496);
    wipe((volatile unsigned short *)WS_MAP,65536);
    wipe(background_palette->data,7*512);
    if(!copy_file("WCELL.BIN",WS_CELLS,WS_CELL_BYTES) ||
       !copy_file("WMAP.BIN",WS_MAP,WS_MAP_BYTES) ||
       !copy_file("WPAL.BIN",background_palette->data,32))return 102;
    for(i=0;i<6;i++){
        ids[i]=texture(names[i],widths[i],widths[i]);
        if(ids[i]!=i){jo_sprite_free_all();for(i=0;i<6;i++)ids[i]=-1;return 103;}
    }
    slCharNbg1(COL_TYPE_256,CHAR_SIZE_1x1);
    slPageNbg1(WS_CELLS,0,PNB_1WORD|CN_12BIT);
    slPlaneNbg1(PL_SIZE_1x1);slMapNbg1(WS_MAP,WS_MAP,WS_MAP,WS_MAP);
    slZoomNbg1(65536,65536);slScrPosNbg1(0,0);
    slScrWindow0(48,0,271,239);slScrWindowModeNbg1(win0_IN);
    slPriorityNbg1(1);slPriorityNbg0(7);
    if(slScrAutoDisp(NBG0ON|NBG1ON)<0)return 104;
    JO_VDP1_PTMR=trigger;return 0;
}
void mf_ws_runtime_begin(int coop,jo_palette *background,unsigned now)
{
    mf_ws_init(&shooter,coop);background_palette=background;
    phase=1;drain=0;title=120;error=0;previous=now;
    slScrDisp(NBG1OFF|NBG2OFF);jo_clear_screen();
}
static void draw(int id,int x,int y)
{jo_sprite_draw3D2(ids[id],x,y,100);}
static void render(void)
{
    int i;slScrPosNbg1(0,-shooter.scroll*65536);
    /* New bank uses raw RGB555, with a fresh default sprite attribute state. */
    jo_sprite_disable_horizontal_flip();jo_sprite_disable_vertical_flip();
    jo_sprite_disable_half_transparency();jo_sprite_disable_dark_filter();
    jo_sprite_disable_gouraud_shading();jo_sprite_restore_sprite_scale();jo_sprite_disable_clipping();
    for(i=0;i<MF_WS_ENEMIES;i++){
        mf_ws_enemy *e=&shooter.enemies[i];
        if(e->active)draw(2,e->x/256-12,e->y/256-12);
        else if(e->explosion)draw(5,e->x/256-16,e->y/256-16);
    }
    for(i=0;i<MF_WS_SHOTS;i++)if(shooter.shots[i].active)draw(3,shooter.shots[i].x/256-4,shooter.shots[i].y/256-4);
    for(i=0;i<MF_WS_HOSTILE;i++)if(shooter.hostile[i].active)draw(4,shooter.hostile[i].x/256-4,shooter.hostile[i].y/256-4);
    for(i=0;i<2;i++){
        mf_ws_player *p=&shooter.players[i];int col=i?34:0;
        if(p->active && p->lives && !p->respawn && (!p->invulnerable || !(shooter.ticks&4)))draw(i,p->x/256-16,p->y/256-16);
        jo_print(col,2,i?"CHUCK":"BUCK");jo_print(col,3,i?"2P":"1P");
        jo_printf(col,6,"%05d",p->score%100000);jo_print(col,8,"LIVES");jo_printf(col,9,"%d",p->lives);
        jo_print(col,12,"WPN 1");
        if(i && !p->active){jo_print(col,16,"START");jo_print(col,17,"JOIN");}
        else {jo_print(col,16,"     ");jo_print(col,17,"    ");}
    }
    jo_print(12,14,shooter.game_over?"GAME OVER       ":(shooter.paused?"PAUSED          ":"                "));
    jo_print(10,16,shooter.game_over?"1P START TO RESTART":"                  ");
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
    if(phase==4){jo_printf(7,12,"LEVEL 2 LOAD FAILED E%d",error);return;}
    if(phase==2){
        jo_print(15,11,"LEVEL 2");jo_print(11,13,"WINGSUIT ASSAULT");
        pressed[0]=pressed[1]=0;
        title-=elapsed>6?6:(int)elapsed;
        if(title<=0){phase=3;jo_clear_screen();}return;
    }
    if(elapsed>6)elapsed=6;
    for(i=0;i<elapsed;i++){
        mf_ws_step(&shooter,held,pressed,conn);pressed[0]=pressed[1]=0;
    }
    render();
}
#endif
