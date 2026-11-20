#include <assert.h>
#include <stdio.h>
#include <string.h>
#define JO_MALLOC_TRY_REUSE_BLOCK 1
void *jo_malloc_with_behaviour(unsigned,int);
#include "parallax.c"
unsigned char street_a0[131072],street_b0[131072];
static unsigned char panorama[MF_INTERSECTION_WIDTH*MF_WORLD_HEIGHT];
static unsigned uploads,peak;
static unsigned char map_data[MF_INTERSECTION_MAP_BYTES],offset_data[MF_INTERSECTION_OFFSET_BYTES];
static unsigned char block_heap[MF_WORLD_DECODE_HEAP];
static unsigned char packed_heap[MF_INTERSECTION_PACK_BYTES+4];
static void file(const char *path,void *dst,unsigned bytes) {
 FILE *f=fopen(path,"rb");assert(f && fread(dst,1,bytes,f)==bytes && fgetc(f)==EOF);fclose(f);
}
/* Test the same sector-read path used at native boot, including a
   partial final sector and a short transfer that advances the cursor. */
static unsigned char staging[MF_WORLD_PACK_STORAGE], received[MF_INTERSECTION_PACK_BYTES];
static unsigned cd_offset, cd_seeks, cd_short_reads, cd_short_budget, cd_bad_size, cd_alloc_fail;
static int cd_open, cd_allocated;
int GFS_NameToId(Sint8 *name) { assert(!strcmp((const char *)name,"IXPACK.BIN"));return 1; }
GfsHn GFS_Open(int id) { assert(id==1 && !cd_open);cd_open=1;return &cd_open; }
void GFS_Close(GfsHn handle) { assert(handle==&cd_open && cd_open);cd_open=0; }
void GFS_GetFileSize(GfsHn handle,Sint32 *size,Sint32 *count,Sint32 *last) {
 unsigned length=MF_INTERSECTION_PACK_BYTES+cd_bad_size;
 assert(handle==&cd_open && cd_open);
 *size=MF_WORLD_PACK_SECTOR;*count=(length+*size-1)/ *size;*last=length-(*count-1)* *size;
}
Sint32 GFS_Seek(GfsHn handle,Sint32 offset,Sint32 mode) {
 assert(handle==&cd_open && cd_open && mode==GFS_SEEK_SET && offset>=0);
 cd_offset=(unsigned)offset*MF_WORLD_PACK_SECTOR;++cd_seeks;
 return offset;
}
Sint32 GFS_Fread(GfsHn handle,Sint32 sectors,void *dst,Sint32 length) {
 unsigned bytes=(unsigned)length;
 assert(handle==&cd_open && cd_open && cd_allocated && dst==staging);
 assert(bytes<=MF_WORLD_PACK_CHUNK && cd_offset+bytes<=MF_INTERSECTION_PACK_BYTES);
 assert((unsigned)sectors==(bytes+MF_WORLD_PACK_SECTOR-1)/MF_WORLD_PACK_SECTOR);
 if(cd_short_budget){--cd_short_budget;++cd_short_reads;--bytes;}
 memcpy(dst,packed_heap+cd_offset,bytes);
 cd_offset+=(unsigned)sectors*MF_WORLD_PACK_SECTOR;
 return (Sint32)bytes;
}
void *jo_malloc_with_behaviour(unsigned bytes,int behavior) {
 assert(bytes==sizeof staging && behavior==JO_MALLOC_TRY_REUSE_BLOCK && !cd_allocated);
 if(cd_alloc_fail)return NULL;
 cd_allocated=1;return staging;
}
void jo_free(void *ptr) { assert(ptr==staging && cd_allocated);cd_allocated=0; }
static void check_pack_read(void) {
 unsigned chunks=(MF_INTERSECTION_PACK_BYTES+MF_WORLD_PACK_CHUNK-1)/ MF_WORLD_PACK_CHUNK;
 file("assets/level1-intersection/IXPACK.BIN",packed_heap,MF_INTERSECTION_PACK_BYTES);
 cd_short_budget=1;
 assert(world_pack_read(received) && !cd_open && !cd_allocated);
 assert(cd_short_reads==1 && cd_seeks==chunks+1);
 assert(!memcmp(received,packed_heap,sizeof received));
 cd_bad_size=1;
 assert(!world_pack_read(received) && !cd_open && !cd_allocated);
 cd_bad_size=0;cd_alloc_fail=1;
 assert(!world_pack_read(received) && !cd_open && !cd_allocated);
 cd_alloc_fail=0;cd_short_budget=3;
 assert(!world_pack_read(received) && !cd_open && !cd_allocated);
 puts("PASS bounded CD staging, byte-exact pack, short-read retry, and cleanup");
}
static void load(void) {
 world_packed=packed_heap;world_chunks=map_data;world_offsets=offset_data;
 file("assets/level1-intersection/IXPACK.BIN",world_packed,MF_INTERSECTION_PACK_BYTES);
 file("assets/level1-intersection/IXOFF.BIN",world_offsets,MF_INTERSECTION_OFFSET_BYTES);
 file("assets/level1-intersection/IXMAP.BIN",world_chunks,MF_INTERSECTION_MAP_BYTES);
 file("assets/level1-intersection/IXPIX.BIN",panorama,sizeof panorama);
 world_decoded_group=-1;
 assert(world_offset(0)==0 && world_offset(MF_INTERSECTION_BLOCKS)==MF_INTERSECTION_PACK_DATA_BYTES);
 for(unsigned i=0;i<MF_INTERSECTION_BLOCKS;i++)assert(world_decode(i));
 /* Every current map source decodes to its actual indexed panorama tile. */
 for(int col=0;col<MF_INTERSECTION_WIDTH/8;col++)for(int y=0;y<MF_INTERSECTION_ROWS;y++) {
  unsigned source=world_pattern(col,y);assert(source<MF_INTERSECTION_TILES && world_decode(source/8));
  for(unsigned row=0;row<8;row++) {
   unsigned char blank[8]={0};
   assert(!memcmp(world_decoded+(source%8)*64+row*8,col<160 && y<7?blank:panorama+(y*8+row)*MF_INTERSECTION_WIDTH+col*8,8));
  }
 }
 for(unsigned i=0;i<131072/2;i++){((unsigned short *)street_a0)[i]=0xcafe;((unsigned short *)street_b0)[i]=0xbabe;}
 for(unsigned i=0;i<1664;i++) {
  assert(world_decode(i/8));
  for(unsigned j=0;j<32;j++)((unsigned short *)street_a0)[i*32+j]=(world_decoded[(i%8)*64+j*2]<<8)|world_decoded[(i%8)*64+j*2+1];
 }
 world_cache_reset();world_block_cache=block_heap;world_blocks_reset();
}
static void visible(int camera) {
 int scroll=mf_world_camera_y(camera);
 int first_row=scroll>0?(scroll-1)/8:0,last_row=(scroll+239)/8;
 for(int col=camera/8;col<=(camera+319)/8;col++)for(int y=first_row;y<=last_row;y++) {
  unsigned physical=col%128,p=((unsigned short *)street_b0)[physical/64*4096+y*64+physical%64];
  assert((p&0xf000)==0x1000 && !(p&1));unsigned slot=(p&4095)/2;assert(slot<1664);
  unsigned source=world_render_pattern(col,y);assert(world_source[slot]==source && world_slot[source]==(int)slot);
  for(int row=0;row<8;row++)for(int pair=0;pair<4;pair++) {
   unsigned word=((unsigned short *)street_a0)[slot*32+row*4+pair];
   unsigned at=(y*8+row)*MF_INTERSECTION_WIDTH+col*8+pair*2;
   unsigned expected=col<160 && y<7?0:(panorama[at]<<8)|panorama[at+1];
   assert(word==expected);
  }
 }
 for(unsigned i=106496/2;i<131072/2;i++)assert(((unsigned short *)street_a0)[i]==0xcafe);
 for(unsigned i=16384/2;i<131072/2;i++)assert(((unsigned short *)street_b0)[i]==0xbabe);
}
static void update(int camera) {
 unsigned short before[1664];memcpy(before,world_source,sizeof before);world_map_update(camera);
 unsigned count=0;for(unsigned i=0;i<1664;i++)count+=before[i]!=world_source[i];uploads+=count;if(count>peak)peak=count;
}
int main(void) {
 check_pack_read();
 load();
 for(int direction=0;direction<2;direction++)for(int i=0;i<=MF_WORLD_CAMERA_MAX;i++) {
  int camera=direction?MF_WORLD_CAMERA_MAX-i:i;update(camera);visible(camera);
  if(i)visible(direction?camera+1:camera-1);
 }
 assert(peak<=74 && uploads>0);unsigned sequential_peak=peak;
 for(int round=0;round<3;round++){load();for(int c=0;c<=MF_WORLD_CAMERA_MAX;c+=320){update(c);visible(c);}}
 /* Truncated offsets/streams and bad back-references never overrun scratch. */
 world_decoded_group=-1;unsigned char saved[4];memcpy(saved,world_offsets+4,4);
 memset(world_offsets+4,0,4);assert(!world_decode(0));memcpy(world_offsets+4,saved,4);
 for(unsigned value=0;value<256;value++) {
  unsigned char old=world_packed[0];world_packed[0]=(unsigned char)value;world_decoded_group=-1;
  (void)world_decode(0);world_packed[0]=old;
 }
 assert(!world_decode(MF_INTERSECTION_BLOCKS));
 printf("PASS diagonal tile codec, all cameras both ways, prior scan-out pinned, VRAM guards, cold resets and invalid streams. Peak %u tile uploads (%u bytes).\n",sequential_peak,sequential_peak*64);
}
