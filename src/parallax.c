#include "performance_audit.h"
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
static unsigned char *world_chunks;
static unsigned char *world_heap;
static unsigned char *world_packed;
/* The approved CD pack expands in place at stage load, descending by
   block. The range lies inside cartridge-independent Saturn low work RAM. */
#define MF_WORLD_PACK_LIMIT 0x00300000u
#define MF_WORLD_RAW_BYTES (MF_INTERSECTION_BLOCKS*512u)
#define MF_WORLD_PACK_ADDRESS (MF_WORLD_PACK_LIMIT-MF_WORLD_RAW_BYTES)
#if MF_WORLD_PACK_ADDRESS < 0x00200000u || MF_INTERSECTION_PACK_BYTES > MF_WORLD_RAW_BYTES
#error "Background tiles exceed low work RAM"
#endif
static unsigned char *world_offsets;
static unsigned short *world_refs;
static unsigned char world_decoded[512];
#define MF_WORLD_PACK_SECTOR 2048u
#define MF_WORLD_PACK_CHUNK 65536u
#define MF_WORLD_PACK_STORAGE ((MF_INTERSECTION_PACK_BYTES<MF_WORLD_PACK_CHUNK?MF_INTERSECTION_PACK_BYTES:MF_WORLD_PACK_CHUNK)+4u)
#define MF_WORLD_BACKGROUND_HEAP (MF_INTERSECTION_MAP_BYTES+4u+MF_INTERSECTION_OFFSET_BYTES+4u+MF_INTERSECTION_TILES*2u)
#define MF_WORLD_VIEW_ROWS 32
static void world_release(void) {
    if(world_heap)jo_free(world_heap);
    world_heap=world_packed=world_chunks=world_offsets=JO_NULL;
    world_refs=JO_NULL;
}
static int world_read(const char *name,void *dst,int expected) {
    int id=GFS_NameToId((Sint8 *)name),length=0;
    GfsHn file;
    Sint32 sector=0,count=0,last=0;
    if(id<0 || !(file=GFS_Open(id)))return 0;
    GFS_GetFileSize(file,&sector,&count,&last);
    GFS_Close(file);
    if(sector<=0 || count<=0 || last<=0 || last>sector ||
       count>expected/sector+1 || (count-1)*sector+last!=expected)return 0;
    return jo_fs_read_file_ptr(name,dst,&length)!=JO_NULL && length==expected;
}
/* Read only at stage load, with CD DMA still targeting high work RAM.
   The pack is one file; seek by sector before each read so a retry after
   a short transfer restarts at the same offset. */
static int world_pack_read(unsigned char *target) {
    int id=GFS_NameToId((Sint8 *)"IXPACK.BIN"),ok=0;
    GfsHn file;
    Sint32 sector=0,count=0,last=0;
    unsigned char *staging=JO_NULL;
    unsigned offset,bytes;
    if(id<0 || !(file=GFS_Open(id)))return 0;
    GFS_GetFileSize(file,&sector,&count,&last);
    if(sector!=MF_WORLD_PACK_SECTOR ||
       count!=(MF_INTERSECTION_PACK_BYTES+MF_WORLD_PACK_SECTOR-1)/MF_WORLD_PACK_SECTOR ||
       last!=(Sint32)(MF_INTERSECTION_PACK_BYTES-(count-1)*MF_WORLD_PACK_SECTOR))goto done;
    staging=jo_malloc_with_behaviour(MF_WORLD_PACK_STORAGE,JO_MALLOC_TRY_REUSE_BLOCK);
    if(!staging)goto done;
    for(offset=0;offset<MF_INTERSECTION_PACK_BYTES;offset+=bytes) {
        unsigned i,retry,sectors;
        bytes=MF_INTERSECTION_PACK_BYTES-offset;
        if(bytes>MF_WORLD_PACK_CHUNK)bytes=MF_WORLD_PACK_CHUNK;
        sectors=(bytes+MF_WORLD_PACK_SECTOR-1)/MF_WORLD_PACK_SECTOR;
        for(retry=0;retry<3;retry++)
            if(GFS_Seek(file,offset/MF_WORLD_PACK_SECTOR,GFS_SEEK_SET)>=0 &&
               GFS_Fread(file,sectors,staging,bytes)==(Sint32)bytes)break;
        if(retry==3)goto done;
        for(i=0;i<bytes;i++)target[offset+i]=staging[i];
    }
    ok=1;
done:
    if(staging)jo_free(staging);
    GFS_Close(file);
    return ok;
}
static int world_pack_load(void) {
    unsigned char *packed=(unsigned char *)MF_WORLD_PACK_ADDRESS;
    world_release();
    if(!world_pack_read(packed))return 0;
    world_packed=packed;
    world_heap=jo_malloc_with_behaviour(MF_WORLD_BACKGROUND_HEAP,JO_MALLOC_TRY_REUSE_BLOCK);
    if(!world_heap)return 0;
    if((unsigned long)world_heap+MF_WORLD_BACKGROUND_HEAP>0x060c0000u)return 0;
    world_chunks=world_heap;
    world_offsets=world_chunks+MF_INTERSECTION_MAP_BYTES+4u;
    world_refs=(unsigned short *)(world_offsets+MF_INTERSECTION_OFFSET_BYTES+4u);
    return 1;
}

/* Independently bounded 512-byte blocks (eight source tiles), used at load. */
static unsigned world_offset(unsigned group) {
    const unsigned char *p=world_offsets+group*4;
    return ((unsigned)p[0]<<24)|((unsigned)p[1]<<16)|((unsigned)p[2]<<8)|p[3];
}
static int world_decode(unsigned group) {
    unsigned at,end,bit=0,out=0;
    if(group>=MF_INTERSECTION_BLOCKS)return 0;
    at=world_offset(group);end=world_offset(group+1);
    if(at>=end || end>MF_INTERSECTION_PACK_DATA_BYTES)return 0;
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
    return 1;
}
static int world_expand(void)
{
    unsigned group,i;
    if(world_offset(0)!=0 || world_offset(MF_INTERSECTION_BLOCKS)!=MF_INTERSECTION_PACK_DATA_BYTES)return 0;
    for(group=MF_INTERSECTION_BLOCKS;group--;) {
        /* The output cannot overwrite bytes needed by an earlier block.
           Decode through scratch because this block's ranges may overlap. */
        if(world_offset(group)>group*512u || !world_decode(group))return 0;
        for(i=0;i<512;i++)world_packed[group*512u+i]=world_decoded[i];
    }
    return 1;
}

/* Counts cover the union of the current rectangle and the portion of the
   previous rectangle that could still be scanned out until the next callback. */
typedef struct { int left, right, top, bottom; } world_rect;
static world_rect world_ring, world_previous, world_ahead;
static short world_slot[MF_INTERSECTION_TILES];
static unsigned short world_source[MF_INTERSECTION_CACHE_TILES];
static unsigned world_victim, world_ahead_cursor;
static int world_last_camera,world_scroll_dir;
enum { WORLD_GUARD_COLUMNS=43, WORLD_PREFETCH_TILES=8, WORLD_PREFETCH_CELLS=48 };

static world_rect world_window(int camera)
{
    int scroll=mf_world_camera_y(camera);
    int top=scroll>0?(scroll-1)/8:0;
    int bottom=top+MF_WORLD_VIEW_ROWS;
    world_rect result={camera/8-1,camera/8-1+WORLD_GUARD_COLUMNS,top,
        bottom<MF_INTERSECTION_ROWS?bottom:MF_INTERSECTION_ROWS};
    return result;
}

static int world_same_window(world_rect a,world_rect b)
{
    return a.left==b.left && a.top==b.top && a.right==b.right && a.bottom==b.bottom;
}

static unsigned world_pattern(int column,int y)
{
    int at;
    if(column<0)column=0;
    if(column>=MF_INTERSECTION_WIDTH/8)column=MF_INTERSECTION_WIDTH/8-1;
    at=((column/16*MF_INTERSECTION_ROWS+y)*16+column%16)*2;
    return (unsigned)(world_chunks[at]<<8)|world_chunks[at+1];
}

static unsigned world_render_pattern(int column,int y)
{
    if(column<160 && y<7)return MF_INTERSECTION_BLANK;
    return world_pattern(column,y);
}

static void world_cache_reset(void)
{
    unsigned i;
    for(i=0;i<MF_INTERSECTION_TILES;i++){world_slot[i]=-1;world_refs[i]=0;}
    for(i=0;i<MF_INTERSECTION_CACHE_TILES;i++){world_source[i]=i;world_slot[i]=(short)i;}
    world_ring=world_previous=world_ahead=(world_rect){0,0,0,0};
    world_victim=world_ahead_cursor=0;
    world_last_camera=0;world_scroll_dir=1;
}

static void world_upload(unsigned slot,unsigned source)
{
    volatile unsigned short *cells=(volatile unsigned short *)VDP2_VRAM_A0+slot*32;
    const unsigned char *pixels=world_packed+source*64;
    unsigned i;
    MF_PERF_BEGIN(tile_start);
    for(i=0;i<32;i++)cells[i]=(unsigned short)((pixels[2*i]<<8)|pixels[2*i+1]);
    MF_PERF_END(MF_PERF_TILE_UPLOAD,tile_start);
    mf_perf_stream(64,0,0);
}

static unsigned world_resident(unsigned source)
{
    unsigned slot;
    MF_PERF_BEGIN(lookup_start);
    if(world_slot[source]>=0) {
        MF_PERF_END(MF_PERF_LOOKUP,lookup_start);
        return (unsigned)world_slot[source];
    }
    /* The largest adjacent union is below the slot capacity, so a victim
       always exists even when a speculative upload arrives at the guard. */
    while(world_refs[world_source[world_victim]]) {
        if(++world_victim==MF_INTERSECTION_CACHE_TILES)world_victim=0;
    }
    slot=world_victim;
    MF_PERF_END(MF_PERF_LOOKUP,lookup_start);
    MF_PERF_BEGIN(bind_start);
    world_slot[world_source[slot]]=-1;
    world_source[slot]=(unsigned short)source;
    world_slot[source]=(short)slot;
    if(++world_victim==MF_INTERSECTION_CACHE_TILES)world_victim=0;
    MF_PERF_END(MF_PERF_COPY,bind_start);
    world_upload(slot,source);
    return slot;
}

enum { WORLD_UNPIN=-1, WORLD_WRITE=0, WORLD_PIN=1 };

static void world_strip(int column,int first,int end,int op)
{
    int y;
    unsigned physical=(unsigned)column&127u;
    volatile unsigned short *map=(volatile unsigned short *)VDP2_VRAM_B0+
        (physical/64)*4096+physical%64;
    for(y=first;y<end;y++) {
        unsigned source=world_render_pattern(column,y);
        if(op)world_refs[source]=(unsigned short)(world_refs[source]+op);
        else {
            unsigned slot=world_resident(source);
            MF_PERF_BEGIN(name_start);
            map[y*64]=(unsigned short)(0x1000u|slot*2u);
            MF_PERF_END(MF_PERF_NAME_TABLE,name_start);
        }
    }
    if(!op)mf_perf_stream(0,(end-first)*2,0);
}

/* Visit only entering/leaving columns and rows. Half-open rectangles avoid
   double-counting the corner on a combined horizontal and vertical step. */
static void world_difference(world_rect a,world_rect b,int op)
{
    int col,top=a.top,bottom=a.bottom;
    if(b.top<bottom)bottom=b.top;
    if(b.bottom>top)top=b.bottom;
    for(col=a.left;col<a.right;col++) {
        if(col<b.left || col>=b.right || top<=bottom)
            world_strip(col,a.top,a.bottom,op);
        else {
            if(bottom>a.top)world_strip(col,a.top,bottom,op);
            if(top<a.bottom)world_strip(col,top,a.bottom,op);
        }
    }
}

static void world_prefetch(int camera)
{
    world_rect next;
    unsigned cells=0,uploads=0;
    int follow=camera+8*world_scroll_dir;
    if(follow<0)follow=0;
    if(follow>MF_WORLD_CAMERA_MAX)follow=MF_WORLD_CAMERA_MAX;
    next=world_window(follow);
    if(!world_same_window(next,world_ahead)) {
        world_ahead=next;
        world_ahead_cursor=0;
    }
    while(cells<WORLD_PREFETCH_CELLS && uploads<WORLD_PREFETCH_TILES &&
          world_ahead_cursor<MF_WORLD_VIEW_ROWS+WORLD_GUARD_COLUMNS) {
        unsigned index=world_ahead_cursor++,source;
        int col,y;
        MF_PERF_BEGIN(prefetch_start);
        if(index<MF_WORLD_VIEW_ROWS) {
            col=world_scroll_dir>0?next.right-1:next.left;
            y=next.top+(int)index;
            ++cells;
            if(y>=next.bottom || (col>=world_ring.left && col<world_ring.right &&
               y>=world_ring.top && y<world_ring.bottom)) {
                MF_PERF_END(MF_PERF_PREFETCH,prefetch_start);
                continue;
            }
        } else {
            col=next.left+(int)index-MF_WORLD_VIEW_ROWS;
            y=world_scroll_dir>0?next.bottom-1:next.top;
            ++cells;
            if(y>=world_ring.top && y<world_ring.bottom) {
                MF_PERF_END(MF_PERF_PREFETCH,prefetch_start);
                continue;
            }
        }
        source=world_render_pattern(col,y);
        MF_PERF_END(MF_PERF_PREFETCH,prefetch_start);
        if(world_slot[source]<0) {
            world_resident(source);
            ++uploads;
        }
    }
}

static void world_map_update(int camera)
{
    world_rect next=world_window(camera);
    if(camera!=world_last_camera) {
        int direction=camera>world_last_camera?1:-1;
        if(direction!=world_scroll_dir)world_ahead_cursor=0;
        world_scroll_dir=direction;
        world_last_camera=camera;
    }
    if(!world_same_window(world_previous,world_ring)) {
        MF_PERF_BEGIN(unpin_start);
        world_difference(world_previous,world_ring,WORLD_UNPIN);
        world_previous=world_ring;
        MF_PERF_END(MF_PERF_MARK,unpin_start);
    }
    if(!world_same_window(next,world_ring)) {
        MF_PERF_BEGIN(pin_start);
        /* Full discontinuities (such as exiting the gallery) already rebuild
           the ring. Retain overlap for all normal one-tile edge changes. */
        if(world_ring.right>world_ring.left &&
           (next.left-world_ring.left>1 || world_ring.left-next.left>1 ||
            next.top-world_ring.top>1 || world_ring.top-next.top>1)) {
            world_difference(world_ring,(world_rect){0,0,0,0},WORLD_UNPIN);
            world_ring=(world_rect){0,0,0,0};
        }
        world_difference(next,world_ring,WORLD_PIN);
        MF_PERF_END(MF_PERF_MARK,pin_start);
        world_difference(next,world_ring,WORLD_WRITE);
        world_previous=world_ring;
        world_ring=next;
        world_ahead_cursor=0;
    }
    world_prefetch(camera);
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
       !world_read("IXOFF.BIN",world_offsets,MF_INTERSECTION_OFFSET_BYTES) ||
       !world_read("IXMAP.BIN",world_chunks,MF_INTERSECTION_MAP_BYTES))goto failed;
    {
        unsigned i;
        for(i=0;i<MF_INTERSECTION_MAP_BYTES;i+=2)
            if(((unsigned)(world_chunks[i]<<8)|world_chunks[i+1])>=MF_INTERSECTION_TILES)goto failed;
        if(!world_expand())goto failed;
        for(i=0;i<MF_INTERSECTION_CACHE_TILES;i++)world_upload(i,i);
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
    MF_PERF_BEGIN(stream_start);
    world_map_update(camera);
    MF_PERF_END(MF_PERF_STREAM,stream_start);
#endif
    /* Same +1 raster registration and border culling as the approved street.
       Fractional quarter-speed fixed point avoids integer-camera stepping. */
#if MF_LEVEL1_WORLD_FLOW
    slScrPosNbg1((camera-1)*65536,(mf_world_camera_y(camera)-1)*65536);
    slScrWindow0(camera%128==0?1:0,mf_world_camera_y(camera)==0?1:0,319,239);
#else
    slScrPosNbg1((camera-1)*65536,-65536);
    slScrWindow0(camera%128==0?1:0,1,319,239);
#endif
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
