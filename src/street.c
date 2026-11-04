#include "build-info.h"
#include <jo/jo.h>
#include "street.h"
#include "city_neon.h"
#if MF_PARALLAX_DEMO
#include "parallax.h"
#endif

#ifndef MF_STREET_LEGACY_CHECK
#define MF_STREET_LEGACY_CHECK 0
#endif
#if MF_CITY_NEON
static volatile unsigned short *city_palette;
static unsigned city_last_step=~0u;
#endif
/* Called from the existing VBlank callback. Only eight colors in the street's
   existing bank are touched; no textures, maps, heap, CD reads or game clocks. */
void mf_street_animate(unsigned vblank)
{
#if MF_CITY_NEON
    unsigned step=(vblank>>3)&127u,n,i;
    if(!city_palette || step==city_last_step)return;
    city_last_step=step;
    for(i=0;i<8;i++) {
        unsigned color=city_neon_base[i],gain,r,g,b;
        n=(step+(i>=5 && i<=6?11u:0u))&31u;
        gain=90u+(n<16u?n:31u-n)*10u/15u;
        /* A single letter group dips for eight VBlanks once per 1024.
           Readability stays intact; this is a soft fault, never a blackout. */
        if(i==7 && step==93u)gain=65u;
        r=(color&31u)*gain/100u;g=((color>>5)&31u)*gain/100u;
        b=((color>>10)&31u)*gain/100u;
        city_palette[239+i]=(unsigned short)(0x8000u|r|(g<<5)|(b<<10));
    }
#else
    (void)vblank;
#endif
}
static mf_street_diagnostic diagnostic={
    .palette_id=-99,.root_executable=-99,.root_street=-99,
    .file_id={-99,-99,-99},.length={-1,-1,-1},.auto_result=-99
};
const mf_street_diagnostic *mf_street_diagnostics(void) {return &diagnostic;}
static int street_failure(int code) {diagnostic.code=code;return 0;}
void mf_street_diagnostic_draw(int line)
{
    jo_printf(1,line,"STREET S%03d STEP%03d PAL%d",diagnostic.code,diagnostic.step,diagnostic.palette_id);
    jo_printf(1,line+1,"ROOT 0BIN%d ST0%d",diagnostic.root_executable,diagnostic.root_street);
    jo_printf(1,line+2,"BITMAP %08x",(unsigned)diagnostic.bitmap);
    jo_printf(1,line+3,"CELL %08x EXP25E00000",(unsigned)diagnostic.cells);
    jo_printf(1,line+4,"MAP  %08x EXP25E40000",(unsigned)diagnostic.map);
    jo_printf(1,line+5,"CELL ID%d %d/%u",diagnostic.file_id[0],diagnostic.length[0],MF_STREET_CELL_BYTES);
    jo_printf(1,line+6,"MAP  ID%d %d/16384",diagnostic.file_id[1],diagnostic.length[1]);
    jo_printf(1,line+7,"PAL  ID%d %d/510",diagnostic.file_id[2],diagnostic.length[2]);
    jo_printf(1,line+8,"READ MASK%x AUTO%d LEGACY%d",diagnostic.read_mask,diagnostic.auto_result,MF_STREET_LEGACY_CHECK);
}

#if MF_VDP2_STREET
/* Narrow adapter for the pinned SDK: relinquish its default NBG1 bitmap.
   This is the sole exported SDK storage pointer used; the SDK is not patched.
   NBG1 is owned exclusively here after initialization. Never call bitmap APIs. */
extern jo_color *nbg1_bitmap;
static int copy_file(const char *name,void *destination,int expected,int index)
{
    int length=-1;
    char *data;
    int code=120+10*index;
    diagnostic.step=code;
    diagnostic.file_id[index]=GFS_NameToId((Sint8 *)name);
    if(diagnostic.file_id[index]<0)return street_failure(code);
    data=jo_fs_read_file(name,&length);
    diagnostic.length[index]=length;
    if(!data)return street_failure(code+1);
    if(length!=expected) {jo_free(data);return street_failure(code+2);}
    if(expected==510)
        jo_palette_to_cram((unsigned short *)data,(unsigned short *)destination,255);
    else jo_dma_copy(data,destination,expected);
    jo_free(data);diagnostic.read_mask|=1<<index;return 1;
}
#endif

int mf_street_load(jo_palette *palette,int sprites[5])
{
    int n;
    diagnostic.code=0;diagnostic.step=100;diagnostic.palette_id=palette->id;
#if MF_CITY_NEON
    city_palette=JO_NULL;city_last_step=~0u;
#endif
    diagnostic.bitmap=diagnostic.cells=diagnostic.map=0;
    diagnostic.read_mask=0;diagnostic.auto_result=-99;
    for(n=0;n<3;n++){diagnostic.file_id[n]=-99;diagnostic.length[n]=-1;}
    diagnostic.root_executable=GFS_NameToId((Sint8 *)"0.BIN");
    diagnostic.root_street=GFS_NameToId((Sint8 *)"ST0.TGA");
    if(diagnostic.root_executable<0 || diagnostic.root_street<0)return street_failure(102);
#if MF_VDP2_STREET
    void *cells,*map;
    (void)sprites;
    if(palette->id!=1)return street_failure(101);
    slTVOff();
    diagnostic.bitmap=(unsigned long)nbg1_bitmap;
    if(nbg1_bitmap) {jo_vdp2_free(nbg1_bitmap);nbg1_bitmap=JO_NULL;}
    diagnostic.step=110;
    cells=jo_vdp2_malloc(JO_VDP2_RAM_CELL_NBG1,MF_STREET_CELL_BYTES);
    diagnostic.cells=(unsigned long)cells;
    if(!cells){street_failure(110);goto failed;}
    if(cells!=(void *)VDP2_VRAM_A0){street_failure(111);goto failed;}
    diagnostic.step=112;
    map=jo_vdp2_malloc(JO_VDP2_RAM_MAP_NBG1,16384);
    diagnostic.map=(unsigned long)map;
    /* Explicit bank bounds: never overwrite SDK text, back color or tables. */
    if(!map){street_failure(112);goto failed;}
    if(map!=(void *)VDP2_VRAM_B0){street_failure(113);goto failed;}
    if(!copy_file(MF_STREET_CELLS,cells,MF_STREET_CELL_BYTES,0)
       || !copy_file(MF_STREET_MAP,map,16384,1)
       || !copy_file(MF_STREET_PALETTE,palette->data,510,2))goto failed;
    diagnostic.step=150;
    slCharNbg1(COL_TYPE_256,CHAR_SIZE_1x1);
    slPageNbg1(cells,0,PNB_1WORD|CN_12BIT);
    slPlaneNbg1(PL_SIZE_2x1);
    slMapNbg1(map,map,map,map);
    slZoomNbg1(65536,65536);
    slScrPosNbg1(-65536,-65536);
    /* Match SGL's unit-scale VDP1 raster origin (+1,+1). The old
       x>-128 cull also leaves column zero uncovered at 128px boundaries.
       Window 0 belongs to this NBG1 owner only; sprites/text are unaffected. */
    slScrWindow0(1,1,319,239);
    slScrWindowModeNbg1(win0_IN);
    slPriorityNbg1(1);
    slPrioritySpr0(4);slPrioritySpr1(4);slPrioritySpr2(4);slPrioritySpr3(4);
    slPrioritySpr4(4);slPrioritySpr5(4);slPrioritySpr6(4);slPrioritySpr7(4);
    slPriorityNbg0(7);
    /* Recompute cell + pattern-name VRAM fetch cycles, not bitmap cycles. */
    diagnostic.auto_result=slScrAutoDisp(NBG0ON|NBG1ON);
    /* Pinned SGL returns 0 on success and -1 if no access schedule fits.
       LEGACY_CHECK exists only to reproduce dc962cd's inverted check. */
#if MF_STREET_LEGACY_CHECK
    if(!diagnostic.auto_result){street_failure(150);goto failed;}
#else
    if(diagnostic.auto_result<0){street_failure(150);goto failed;}
#endif
    diagnostic.step=199;
#if MF_CITY_NEON
    city_palette=palette->data;
#endif
    slTVOn();return 1;
failed:
    slTVOn();return 0;
#else
    int i;
    static const char *names[]={"ST0.TGA","ST1.TGA","ST2.TGA","ST3.TGA","ST4.TGA"};
    jo_set_tga_default_palette(palette);
    diagnostic.step=160;
    for(i=0;i<5;i++) {
        sprites[i]=jo_sprite_add_tga(JO_ROOT_DIR,names[i],1);
        if(sprites[i]<0)return street_failure(160+i);
    }
    diagnostic.step=199;
    return 1;
#endif
}
void mf_street_draw(const int sprites[5],int palette_id,int camera)
{
#if MF_VDP2_STREET
    (void)sprites;(void)palette_id;
#if MF_PARALLAX_DEMO
    if(mf_parallax_active()){mf_parallax_draw();return;}
#endif
    /* Signed multiplication avoids shifting a negative fixed-point value. */
    slScrPosNbg1((camera-1)*65536,-65536);
    slScrWindow0(camera%128==0?1:0,1,319,239);
#else
    int i;
    jo_sprite_set_palette(palette_id);
    for(i=0;i<5;i++) {
        int x=i*128-camera;
        if(x>-128 && x<320)jo_sprite_draw3D2(sprites[i],x,0,500);
    }
#endif
}
