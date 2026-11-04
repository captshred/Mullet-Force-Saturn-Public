#include "build-info.h"
#include "city_neon.h"
#if MF_LIVE_CITY_PARALLAX
#include <jo/jo.h>
#include "parallax.h"
#include "live_city_data.h"
static int live_ready,live_error;
static int live_copy(const char *name,void *dst,int bytes)
{
    int length=0;char *data=jo_fs_read_file(name,&length);
    if(!data)return 0;
    if(length!=bytes){jo_free(data);return 0;}
    jo_dma_copy(data,dst,bytes);jo_free(data);return 1;
}
int mf_parallax_load(void)
{
    void *cells,*map;live_ready=live_error=0;slTVOff();
    cells=jo_vdp2_malloc(JO_VDP2_RAM_MAP_NBG1,MF_LIVE_SKY_BYTES);
    map=jo_vdp2_malloc(JO_VDP2_RAM_MAP_NBG1,16384);
    if(cells!=(void *)(VDP2_VRAM_B0+0x4000) || map!=(void *)(VDP2_VRAM_B0+0x4000+MF_LIVE_SKY_BYTES))goto failed;
    if(!live_copy("LCSKY.BIN",cells,MF_LIVE_SKY_BYTES) || !live_copy("LCMAP.BIN",map,16384))goto failed;
    slCharNbg2(COL_TYPE_256,CHAR_SIZE_1x1);slPageNbg2(cells,0,PNB_1WORD|CN_12BIT);
    slPlaneNbg2(PL_SIZE_2x1);slMapNbg2(map,map,map,map);
    slPriorityNbg2(1);slPriorityNbg1(2);
    slScrWindow1(1,1,319,55);slScrWindowModeNbg2(win1_IN);
    if(slScrAutoDisp(NBG0ON|NBG1ON|NBG2ON)<0)goto failed;
    live_ready=1;slTVOn();return 1;
failed:
    live_error=860;slTVOn();return 0;
}
void mf_parallax_game_draw(int camera)
{
    if(!live_ready)return;
    /* Same +1 raster registration and border culling as the approved street.
       Fractional quarter-speed fixed point avoids integer-camera stepping. */
    slScrPosNbg1((camera-1)*65536,-65536);
    slScrWindow0(camera%128==0?1:0,56,319,239);
    slScrWindow1(camera%128==0?1:0,1,319,55);
    slScrPosNbg2(camera*16384-65536,-65536);
}
int mf_parallax_error(void){return live_error;}
int mf_parallax_active(void){return 0;}
int mf_parallax_enter(void){return 0;}
void mf_parallax_leave(void){}
void mf_parallax_update(unsigned h,unsigned t){(void)h;(void)t;}
void mf_parallax_draw(void){}
void mf_parallax_labels(void){}

#elif MF_PARALLAX_DEMO
#include <jo/jo.h>
#include "input.h"
#include "parallax.h"

/* B0 ownership: existing street ring [0,0x4000), skyline cells
   [0x4000,0x6000), skyline map [0x6000,0x8000). A1/B1 stay SDK-owned. */
static struct {
    void *cells,*map;
    int active,camera,base,error,uploads,last_bytes,tags[8];
} preview;
/* Includes space for Jo's read_file_ptr trailing NUL and word alignment. */
static unsigned char chunks[4804];
static volatile unsigned short *street_map(void)
{return (volatile unsigned short *)VDP2_VRAM_B0;}
static unsigned short pattern(int source,int row,int x)
{
    int i=((source*30+row)*16+x)*2;
    return (unsigned short)((chunks[i]<<8)|chunks[i+1]);
}
static int size_matches(int id,int expected)
{
    GfsHn file=GFS_Open(id);
    Sint32 sector=0,count=0,last=0;
    if(!file)return 0;
    GFS_GetFileSize(file,&sector,&count,&last);GFS_Close(file);
    if(sector<=0 || count<=0 || count>expected/sector+1)return 0;
    return (count-1)*sector+last==expected;
}
static int read_exact(const char *name,void *dst,int size,int code)
{
    int id=GFS_NameToId((Sint8 *)name),length=-1;
    if(id<0 || !size_matches(id,size)){preview.error=code;return 0;}
    if(!jo_fs_read_file_ptr(name,dst,&length) || length!=size){preview.error=code+1;return 0;}
    return 1;
}
int mf_parallax_error(void){return preview.error;}
int mf_parallax_active(void){return preview.active;}
int mf_parallax_load(void)
{
    void *buffer;
    int i;
    preview.error=0;
    if(!read_exact("PCHUNK.BIN",chunks,4800,810))return 0;
    for(i=0;i<2400;i++) {
        unsigned p=(unsigned)(chunks[i*2]<<8)|chunks[i*2+1];
        if((p>>12)!=1 || (p&1) || (p&4095)>=MF_STREET_CELL_BYTES/32u){preview.error=812;return 0;}
    }
    preview.cells=jo_vdp2_malloc(JO_VDP2_RAM_MAP_NBG1,8192);
    preview.map=jo_vdp2_malloc(JO_VDP2_RAM_MAP_NBG1,8192);
    if(preview.cells!=(void *)(VDP2_VRAM_B0+0x4000)
       || preview.map!=(void *)(VDP2_VRAM_B0+0x6000)){preview.error=820;return 0;}
    /* FAST allocation makes the temporary block size exact (not a larger
       previously freed TGA block). No retained heap allocation. */
    buffer=jo_malloc_with_behaviour(8193,JO_FAST_ALLOCATION);
    if(!buffer){preview.error=821;return 0;}
    slTVOff();
    if(!read_exact("PSKY.BIN",buffer,8192,830))goto failed;
    jo_dma_copy(buffer,preview.cells,8192);
    if(!read_exact("PSMAP.BIN",buffer,8192,840))goto failed;
    jo_dma_copy(buffer,preview.map,8192);
    jo_free(buffer);slTVOn();return 1;
failed:
    jo_free(buffer);slTVOn();return 0;
}
static void fill_chunk(int world)
{
    int row,x,slot=world%8;
    volatile unsigned short *map=street_map();
    for(row=0;row<30;row++)for(x=0;x<16;x++) {
        int column=slot*16+x;
        map[(column/64)*4096+row*64+column%64]=pattern(world%5,row,x);
    }
    preview.tags[slot]=world;preview.uploads++;preview.last_bytes+=960;
}
static void ensure_cache(void)
{
    int world,base=preview.camera/128-2;
    if(base<0)base=0;
    if(base>56)base=56;
    preview.base=base;preview.last_bytes=0;
    /* Moving <=48px/update means at most one newly needed 128px chunk.
       Its physical slot is outside both old and next visible viewports.
       These 16-bit writes never alter an actively displayed tile column. */
    for(world=base;world<base+8;world++)
        if(preview.tags[world%8]!=world)fill_chunk(world);
}
int mf_parallax_enter(void)
{
    int i;
    if(preview.error || !preview.map)return 0;
    slTVOff();
    preview.camera=preview.uploads=0;
    for(i=0;i<8;i++)preview.tags[i]=-1;
    for(i=0;i<8192;i++)street_map()[i]=0x1000;
    ensure_cache();
    slCharNbg2(COL_TYPE_256,CHAR_SIZE_1x1);
    slPageNbg2(preview.cells,0,PNB_1WORD|CN_12BIT);
    slPlaneNbg2(PL_SIZE_1x1);
    slMapNbg2(preview.map,preview.map,preview.map,preview.map);
    slPriorityNbg2(1);slPriorityNbg1(2);
    slScrWindow1(0,1,319,55);
    slScrWindowModeNbg2(win1_IN);
    if(slScrAutoDisp(NBG0ON|NBG1ON|NBG2ON)<0) {
        preview.error=850;mf_parallax_leave();return 0;
    }
    preview.active=1;mf_parallax_draw();slTVOn();return 1;
}
void mf_parallax_leave(void)
{
    int page,row,x;
    slTVOff();preview.active=0;
    /* Restore every original map word, including padding, without a CD read. */
    for(page=0;page<2;page++)for(row=0;row<64;row++)for(x=0;x<64;x++) {
        int column=page*64+x;
        street_map()[page*4096+row*64+x]=row<30 && column<80
            ?pattern(column/16,row,column%16):0x1000;
    }
    slScrDisp(NBG2OFF);
    slPriorityNbg1(1);slScrWindow0(1,1,319,239);
    slScrPosNbg1(-65536,-65536);
    if(slScrAutoDisp(NBG0ON|NBG1ON)<0)preview.error=851;
    slTVOn();
}
void mf_parallax_update(unsigned held,unsigned ticks)
{
    int step;
    if(!preview.active)return;
    if(ticks>6)ticks=6;
    step=(held&MF_UP)?8:2;
    if((held&MF_RIGHT) && !(held&MF_LEFT))preview.camera+=step*(int)ticks;
    if((held&MF_LEFT) && !(held&MF_RIGHT))preview.camera-=step*(int)ticks;
    if(preview.camera<0)preview.camera=0;
    if(preview.camera>7872)preview.camera=7872;
    ensure_cache();
}
void mf_parallax_draw(void)
{
    /* Street maintains the validated +1,+1 screen registration. Skyline is
       behind it; the demo opens only the upper 55px of the old opaque sky. */
    slScrPosNbg1((preview.camera-1)*65536,-65536);
    slScrWindow0(preview.camera==0?1:0,56,319,239);
    slScrPosNbg2((preview.camera/4)*65536,0);
}
void mf_parallax_labels(void)
{
    jo_clear_screen_line(2);jo_clear_screen_line(4);jo_clear_screen_line(6);
    jo_print(5,2,"PARALLAX STREAMING TEST       ");
    jo_printf(5,4,"CAM %04d/7872 SKY %04d   ",preview.camera,preview.camera/4);
    jo_printf(5,6,"CACHE %02d..%02d LOADS %03d ",preview.base,preview.base+7,preview.uploads);
    jo_print(2,27,"LEFT RIGHT MOVE  UP FAST  B GALLERY");
}
#endif
