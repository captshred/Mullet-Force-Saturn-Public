#include <assert.h>
#include <stdio.h>
#include <string.h>
#define JO_MALLOC_TRY_REUSE_BLOCK 1
void *jo_malloc_with_behaviour(unsigned,int);
#include "parallax.c"
unsigned char street_a0[131072],street_b0[131072];
static unsigned char panorama[1920*240];
static unsigned uploads,peak;
static unsigned char block_heap[MF_WORLD_DECODE_HEAP];
static unsigned char packed_heap[MF_INTERSECTION_PACK_BYTES+4];
static void file(const char *path,void *dst,unsigned bytes) {
 FILE *f=fopen(path,"rb");assert(f && fread(dst,1,bytes,f)==bytes && fgetc(f)==EOF);fclose(f);
}
static void load(void) {
 world_packed=packed_heap;
 file("assets/level1-intersection/IXPACK.BIN",world_packed,MF_INTERSECTION_PACK_BYTES);
 file("assets/level1-intersection/IXOFF.BIN",world_offsets,MF_INTERSECTION_OFFSET_BYTES);
 file("assets/level1-intersection/IXMAP.BIN",world_chunks,MF_INTERSECTION_MAP_BYTES);
 file("assets/level1-intersection/IXPIX.BIN",panorama,sizeof panorama);
 world_decoded_group=-1;
 assert(world_offset(0)==0 && world_offset(MF_INTERSECTION_BLOCKS)==MF_INTERSECTION_PACK_DATA_BYTES);
 for(unsigned i=0;i<MF_INTERSECTION_BLOCKS;i++)assert(world_decode(i));
 /* Every current map source decodes to its actual indexed panorama tile. */
 for(int col=0;col<240;col++)for(int y=0;y<30;y++) {
  unsigned source=world_pattern(col,y);assert(source<MF_INTERSECTION_TILES && world_decode(source/8));
  for(unsigned row=0;row<8;row++) {
   unsigned char blank[8]={0};
   assert(!memcmp(world_decoded+(source%8)*64+row*8,col<160 && y<7?blank:panorama+(y*8+row)*1920+col*8,8));
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
 for(int col=camera/8;col<=(camera+319)/8;col++)for(int y=0;y<30;y++) {
  unsigned physical=col%128,p=((unsigned short *)street_b0)[physical/64*4096+y*64+physical%64];
  assert((p&0xf000)==0x1000 && !(p&1));unsigned slot=(p&4095)/2;assert(slot<1664);
  unsigned source=world_render_pattern(col,y);assert(world_source[slot]==source && world_slot[source]==(int)slot);
  for(int row=0;row<8;row++)for(int pair=0;pair<4;pair++) {
   unsigned word=((unsigned short *)street_a0)[slot*32+row*4+pair];
   unsigned at=(y*8+row)*1920+col*8+pair*2;
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
 load();
 for(int direction=0;direction<2;direction++)for(int i=0;i<=1600;i++) {
  int camera=direction?1600-i:i;update(camera);visible(camera);
  if(i && i%8==0)visible(direction?camera+1:camera-1);
 }
 assert(peak<=30 && uploads>0);unsigned sequential_peak=peak;
 for(int round=0;round<3;round++){load();for(int c=0;c<=1600;c+=320){update(c);visible(c);}}
 /* Truncated offsets/streams and bad back-references never overrun scratch. */
 world_decoded_group=-1;unsigned char saved[4];memcpy(saved,world_offsets+4,4);
 memset(world_offsets+4,0,4);assert(!world_decode(0));memcpy(world_offsets+4,saved,4);
 for(unsigned value=0;value<256;value++) {
  unsigned char old=world_packed[0];world_packed[0]=(unsigned char)value;world_decoded_group=-1;
  (void)world_decode(0);world_packed[0]=old;
 }
 assert(!world_decode(MF_INTERSECTION_BLOCKS));
 printf("PASS 1920px lossless source/decoder/cache: 5328 tiles, every camera0..1600 both ways, prior scan-out pinned, ring wraps, all original tiles/pixels, transparent skyline mask, guarded VRAM tails, cold resets/jumps/corrupt streams; peak %u uploads <=1920B per update\n",sequential_peak);
}
