#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "parallax.c"
unsigned char street_a0[131072],street_b0[131072];
static unsigned char panorama[1280*240];
static unsigned uploads,peak;
static void load(void) {
 FILE *f=fopen("assets/level1-neon-strip/NSCELL.BIN","rb");assert(f && fread(world_cells,1,MF_NEON_STRIP_SOURCE_BYTES,f)==MF_NEON_STRIP_SOURCE_BYTES);fclose(f);
 f=fopen("assets/level1-neon-strip/NSMAP.BIN","rb");assert(f && fread(world_chunks,1,9600,f)==9600);fclose(f);
 f=fopen("assets/level1-neon-strip/NSPIX.BIN","rb");assert(f && fread(panorama,1,sizeof panorama,f)==sizeof panorama);fclose(f);
 for(unsigned i=0;i<131072/2;i++){((unsigned short *)street_a0)[i]=0xcafe;((unsigned short *)street_b0)[i]=0xbabe;}
 for(unsigned i=0;i<MF_NEON_STRIP_CACHE_TILES*32;i++)((unsigned short *)street_a0)[i]=(world_cells[2*i]<<8)|world_cells[2*i+1];
 world_cache_reset();
}
static void visible(int camera) {
 for(int col=camera/8;col<=(camera+319)/8;col++)for(int y=0;y<30;y++) {
  unsigned physical=col%128,p=((unsigned short *)street_b0)[physical/64*4096+y*64+physical%64];
  assert((p&0xf000)==0x1000 && !(p&1));unsigned slot=(p&4095)/2;assert(slot<1664);
  unsigned source=world_pattern(col,y);assert(world_source[slot]==source && world_slot[source]==(int)slot);
  for(int row=0;row<8;row++)for(int pair=0;pair<4;pair++) {
   unsigned word=((unsigned short *)street_a0)[slot*32+row*4+pair];
   unsigned at=(y*8+row)*1280+col*8+pair*2;
   assert((word>>8)==panorama[at] && (word&255)==panorama[at+1]);
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
 for(int direction=0;direction<2;direction++)for(int i=0;i<=960;i++) {
  int camera=direction?960-i:i;update(camera);visible(camera);
  if(i && i%8==0)visible(direction?camera+1:camera-1); /* Previous scan-out pinned. */
 }
 assert(peak<=30 && uploads>0);unsigned sequential_peak=peak;
 /* Cold reset restores initial tile tags and wraps. Large mock camera jumps
    are also safe (normal gameplay remains capped at two pixels/tick). */
 for(int round=0;round<4;round++){load();for(int c=0;c<=960;c+=320){update(c);visible(c);}}
 printf("PASS exact 1280px cache/ring decoded pixels at every camera both ways, old/new scan-out pinned, 1024 wrap/reloads, palette-1/even PNDs, A0 tail/B0 skyline/SDK guards; sequential peak uploads %u tiles (<=1920 bytes/update)\n",sequential_peak);
}
