#include "build-info.h"
#include "city_neon.h"
#include "world_config.h"
#if MF_LIVE_CITY_PARALLAX
#include <jo/jo.h>
#include "parallax.h"
#include "live_city_data.h"
static int live_ready,live_error;
#if MF_LEVEL1_WORLD_FLOW
#include "intersection_data.h"
/* Load-time CPU source, fixed 1664-tile A0 residency. Neither SDK-owned bank
   nor the existing NBG2 skyline allocation is borrowed for facade graphics. */
static unsigned char world_chunks[MF_INTERSECTION_MAP_BYTES+4];
static unsigned char *world_packed; /* Owned heap base; compressed bytes stay resident. */
static unsigned char world_offsets[MF_INTERSECTION_OFFSET_BYTES+4] __attribute__((aligned(4)));
static unsigned char world_decoded[512];
#define MF_WORLD_DECODE_CACHE 128
#define MF_WORLD_PACK_STORAGE ((MF_INTERSECTION_PACK_BYTES+4u+3u)&~3u)
#define MF_WORLD_BACKGROUND_HEAP (MF_WORLD_PACK_STORAGE+MF_WORLD_DECODE_HEAP)
#define MF_WORLD_DECODE_HEAP (MF_WORLD_DECODE_CACHE*512+MF_INTERSECTION_BLOCKS*4+(MF_INTERSECTION_BLOCKS+7)/8)
static unsigned char *world_block_cache;
static short world_block_tag[MF_WORLD_DECODE_CACHE];
static unsigned world_block_age[MF_WORLD_DECODE_CACHE],world_block_clock;
static short *world_block_index;
static unsigned short *world_prefetch_queue;
static unsigned char *world_prefetch_queued;
static unsigned world_prefetch_count,world_prefetch_at;
static int world_decoded_group=-1;
static void world_release(void) {
    if(world_packed)jo_free(world_packed);
    world_packed=world_block_cache=JO_NULL;
    world_block_index=JO_NULL;world_prefetch_queue=JO_NULL;world_prefetch_queued=JO_NULL;
    world_decoded_group=-1;
}
static int world_pack_load(void) {
    int id=GFS_NameToId((Sint8 *)"IXPACK.BIN"),length=-1;
    GfsHn file;Sint32 sector=0,count=0,last=0;
    if(id<0 || !(file=GFS_Open(id)))return 0;
    GFS_GetFileSize(file,&sector,&count,&last);GFS_Close(file);
    if(sector<=0 || count<=0 || last<=0 || last>sector || count>MF_INTERSECTION_PACK_BYTES/(unsigned)sector+1 ||
       (unsigned)((count-1)*sector+last)!=MF_INTERSECTION_PACK_BYTES)return 0;
    world_release();
    world_packed=jo_malloc_with_behaviour(MF_WORLD_BACKGROUND_HEAP,JO_MALLOC_TRY_REUSE_BLOCK);
    if(!world_packed)return 0;
    /* Existing fixed heap only. The whole owner block, not just the decode
       suffix, must fit below the pinned SDK sort/work boundary. */
    if((unsigned long)world_packed+MF_WORLD_BACKGROUND_HEAP>0x060c0000u)return 0;
    world_block_cache=world_packed+MF_WORLD_PACK_STORAGE;
    if(!jo_fs_read_file_ptr("IXPACK.BIN",world_packed,&length) ||
       length!=(int)MF_INTERSECTION_PACK_BYTES)return 0;
    return 1;
}

/* Independently bounded 512-byte blocks (eight source tiles). No gameplay
   filesystem calls, heap work, or framebuffer-dependent decompression. */
static unsigned world_offset(unsigned group) {
    const unsigned char *p=world_offsets+group*4;
    return ((unsigned)p[0]<<24)|((unsigned)p[1]<<16)|((unsigned)p[2]<<8)|p[3];
}
static int world_decode(unsigned group) {
    unsigned at,end,bit=0,out=0;
    if(group>=MF_INTERSECTION_BLOCKS)return 0;
    if(world_decoded_group==(int)group)return 1;
    at=world_offset(group);end=world_offset(group+1);
    if(at>=end || end>MF_INTERSECTION_PACK_DATA_BYTES)return 0;
    world_decoded_group=-1;
    while(out<512) {
        int node=0;unsigned n,d=0,i;
        while(node>=0) {
            if((unsigned)node>=MF_INTERSECTION_HUFF_NODES || at>=end)return 0;
            node=mf_intersection_huffman[node][(world_packed[at]>>(7-bit))&1];
            if(++bit==8){bit=0;++at;}
        }
        n=(unsigned)(-node-1);
        if(n<256){world_decoded[out++]=(unsigned char)n;continue;}
        n=n-256+3;if(out+n>512)return 0;
        for(i=0;i<9;i++) {
            if(at>=end)return 0;
            d=(d<<1)|((world_packed[at]>>(7-bit))&1);
            if(++bit==8){bit=0;++at;}
        }
        ++d;if(d>out)return 0;
        for(i=0;i<n;i++){world_decoded[out]=world_decoded[out-d];++out;}
    }
    if(at+(bit!=0)!=end)return 0;
    world_decoded_group=(int)group;return 1;
}
static short world_slot[MF_INTERSECTION_TILES];
static unsigned short world_source[MF_INTERSECTION_CACHE_TILES];
static unsigned char world_needed[(MF_INTERSECTION_TILES+7)/8];
static unsigned world_victim;
static int world_ring_left=-9999,world_scroll_dir=1;
/* Source blocks span neighboring tiles. Retain the 128 most recently used
   blocks in the existing Jo CPU heap so column updates do not repeatedly
   decode the same rows. This adds no video allocation or gameplay I/O. */
static void world_blocks_reset(void) {
    unsigned i;
    world_block_index=(short *)(world_block_cache+MF_WORLD_DECODE_CACHE*512);
    world_prefetch_queue=(unsigned short *)(world_block_index+MF_INTERSECTION_BLOCKS);
    world_prefetch_queued=(unsigned char *)(world_prefetch_queue+MF_INTERSECTION_BLOCKS);
    for(i=0;i<MF_WORLD_DECODE_CACHE;i++){world_block_tag[i]=-1;world_block_age[i]=0;}
    for(i=0;i<MF_INTERSECTION_BLOCKS;i++)world_block_index[i]=-1;
    world_prefetch_count=world_prefetch_at=0;
    world_block_clock=0;world_decoded_group=-1;
}
static int world_decode_cached(unsigned group) {
    unsigned i,victim=0,j;int cached;
    if(group>=MF_INTERSECTION_BLOCKS)return 0;
    if(!world_block_cache)return world_decode(group);
    cached=world_block_index[group];
    if(cached>=0) {
        if(world_decoded_group!=(int)group)
            for(j=0;j<512;j++)world_decoded[j]=world_block_cache[cached*512+j];
        world_decoded_group=(int)group;world_block_age[cached]=++world_block_clock;return 1;
    }
    for(i=1;i<MF_WORLD_DECODE_CACHE;i++)
        if(world_block_age[i]<world_block_age[victim])victim=i;
    if(!world_decode(group))return 0;
    for(j=0;j<512;j++)world_block_cache[victim*512+j]=world_decoded[j];
    if(world_block_tag[victim]>=0)world_block_index[world_block_tag[victim]]=-1;
    world_block_tag[victim]=(short)group;world_block_index[group]=(short)victim;
    world_block_age[victim]=++world_block_clock;return 1;
}
static unsigned world_pattern(int column,int y) {
    int at;
    if(column<0)column=0;
    if(column>=MF_INTERSECTION_WIDTH/8)column=MF_INTERSECTION_WIDTH/8-1;
    at=((column/16*30+y)*16+column%16)*2;
    return (unsigned)(world_chunks[at]<<8)|world_chunks[at+1];
}
/* The old top 56 pixels were always hidden behind the independent skyline.
   Keep their source bytes intact; transparent ring cells expose that same
   skyline while allowing the new tall buildings to rise in front of it. */
static unsigned world_render_pattern(int column,int y) {
    if(column<160 && y<7)return MF_INTERSECTION_BLANK;
    return world_pattern(column,y);
}
static void world_cache_reset(void) {
    unsigned i;
    for(i=0;i<MF_INTERSECTION_TILES;i++)world_slot[i]=-1;
    for(i=0;i<MF_INTERSECTION_CACHE_TILES;i++){world_source[i]=i;world_slot[i]=(short)i;}
    world_victim=0;world_ring_left=-9999;world_scroll_dir=1;
}
static void world_mark(int first) {
    int column,y;
    for(column=first;column<=first+42;column++)for(y=0;y<30;y++)
        {
        unsigned source=world_render_pattern(column,y);
        world_needed[source>>3]|=(unsigned char)(1u<<(source&7));
    }
}
static unsigned world_resident(unsigned source) {
    unsigned slot,i,at;
    volatile unsigned short *cells=(volatile unsigned short *)VDP2_VRAM_A0;
    if(world_slot[source]>=0)return (unsigned)world_slot[source];
    /* Current and previous visible/guard tiles are pinned before any upload.
       At most 44*30 source tiles can be needed during a normal 2px step. */
    while(world_needed[world_source[world_victim]>>3]&(1u<<(world_source[world_victim]&7)))
        world_victim=(world_victim+1)%MF_INTERSECTION_CACHE_TILES;
    if(!world_decode_cached(source/8)){live_error=861;return 0;}
    slot=world_victim;world_slot[world_source[slot]]=-1;
    world_source[slot]=(unsigned short)source;world_slot[source]=(short)slot;
    at=(source%8)*64;
    for(i=0;i<32;i++)cells[slot*32+i]=(unsigned short)((world_decoded[at+2*i]<<8)|world_decoded[at+2*i+1]);
    world_victim=(slot+1)%MF_INTERSECTION_CACHE_TILES;
    return slot;
}
/* Queue the next 128px beyond the ring guard, nearest column first. Two
   missing blocks are prepared per callback; no decode burst is needed when
   those tiles enter scan-out. Direct group lookup avoids per-hit LRU scans. */
static void world_prefetch_build(int first) {
    int n,y;unsigned i;
    for(i=0;i<(MF_INTERSECTION_BLOCKS+7)/8;i++)world_prefetch_queued[i]=0;
    world_prefetch_count=world_prefetch_at=0;
    for(n=0;n<16;n++) {
        int column=world_scroll_dir>0?first+43+n:first-1-n;
        if(column<0 || column>=MF_INTERSECTION_WIDTH/8)continue;
        for(y=0;y<30;y++) {
            unsigned source=world_render_pattern(column,y),group=source/8;
            if(world_slot[source]<0 && world_block_index[group]<0 &&
               !(world_prefetch_queued[group>>3]&(1u<<(group&7)))) {
                world_prefetch_queued[group>>3]|=(unsigned char)(1u<<(group&7));
                world_prefetch_queue[world_prefetch_count++]=(unsigned short)group;
            }
        }
    }
}
static void world_prefetch(void) {
    unsigned decoded=0;
    while(world_prefetch_at<world_prefetch_count && decoded<2) {
        unsigned group=world_prefetch_queue[world_prefetch_at++];
        if(world_block_index[group]>=0)continue;
        if(!world_decode_cached(group)){live_error=861;return;}
        ++decoded;
    }
}
static void world_map_update(int camera) {
    int first=camera/8-1,col,y;unsigned i;
    volatile unsigned short *map=(volatile unsigned short *)VDP2_VRAM_B0;
    if(first==world_ring_left){world_prefetch();return;}
    if(world_ring_left!=-9999)world_scroll_dir=first>world_ring_left?1:-1;
    for(i=0;i<sizeof(world_needed);i++)world_needed[i]=0;
    world_mark(first);
    if(world_ring_left>=-1 && first-world_ring_left>=-1 && first-world_ring_left<=1)
        world_mark(world_ring_left);
    for(col=first;col<=first+42;col++) {
        int physical=(col%128+128)%128;
        for(y=0;y<30;y++)
            map[physical/64*4096+y*64+physical%64]=(unsigned short)(0x1000u|world_resident(world_render_pattern(col,y))*2u);
    }
    world_ring_left=first;world_prefetch_build(first);world_prefetch();
}
#endif
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
#if MF_LEVEL1_WORLD_FLOW
    if(!world_pack_load() ||
       !live_copy("IXOFF.BIN",world_offsets,MF_INTERSECTION_OFFSET_BYTES) ||
       !live_copy("IXMAP.BIN",world_chunks,MF_INTERSECTION_MAP_BYTES))goto failed;
    {unsigned i,j;
     world_decoded_group=-1;
     if(world_offset(0)!=0 || world_offset(MF_INTERSECTION_BLOCKS)!=MF_INTERSECTION_PACK_DATA_BYTES)goto failed;
     for(i=0;i<MF_INTERSECTION_BLOCKS;i++)if(!world_decode(i))goto failed;
     for(i=0;i<MF_INTERSECTION_MAP_BYTES;i+=2)
        if(((unsigned)(world_chunks[i]<<8)|world_chunks[i+1])>=MF_INTERSECTION_TILES)goto failed;
     if(!world_block_cache)goto failed;
     /* The pinned SGL sort area starts at 0x060c0000; never place this new
        retained heap allocation inside any SDK command/work reservation. */
     if((unsigned long)world_block_cache+MF_WORLD_DECODE_HEAP>0x060c0000u)goto failed;
     world_blocks_reset();
     for(i=0;i<MF_INTERSECTION_CACHE_TILES;i++) {
        volatile unsigned short *dst=(volatile unsigned short *)VDP2_VRAM_A0;
        if(!world_decode(i/8))goto failed;
        for(j=0;j<32;j++)dst[i*32+j]=(unsigned short)((world_decoded[(i%8)*64+j*2]<<8)|world_decoded[(i%8)*64+j*2+1]);
     }
    }
    world_cache_reset();
#endif
    live_ready=1;slTVOn();return 1;
failed:
#if MF_LEVEL1_WORLD_FLOW
    world_release();
#endif
    live_error=860;slTVOn();return 0;
}
void mf_parallax_game_draw(int camera)
{
    if(!live_ready)return;
#if MF_LEVEL1_WORLD_FLOW
    world_map_update(camera);
#endif
    /* Same +1 raster registration and border culling as the approved street.
       Fractional quarter-speed fixed point avoids integer-camera stepping. */
    slScrPosNbg1((camera-1)*65536,-65536);
    slScrWindow0(camera%128==0?1:0,1,319,239);
    slScrWindow1(camera<4 || camera%128==0?1:0,1,319,55);
    slScrPosNbg2(camera*16384-65536,-65536);
}
int mf_parallax_error(void){return live_error;}
int mf_parallax_active(void){return 0;}
int mf_parallax_enter(void){return 0;}
void mf_parallax_leave(void){
#if MF_LEVEL1_WORLD_FLOW
    world_release();
    live_ready=0;
#endif
}
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
    if(sector<=0 || count<=0 || last<=0 || last>sector || count>expected/sector+1)return 0;
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
