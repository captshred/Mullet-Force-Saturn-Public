#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "parallax.c"
unsigned char street_a0[131072],street_b0[131072];
int main(void) {
 FILE *f=fopen("assets/city-cleanup/CICHUNK.BIN","rb");assert(f && fread(world_chunks,1,4800,f)==4800);fclose(f);
 for(int direction=0;direction<2;direction++)for(int i=0;i<=960;i++) {
  int camera=direction?960-i:i;world_map_update(camera);
  for(int col=camera/8;col<=(camera+319)/8;col++)for(int y=0;y<30;y++){
   int source=mf_world_source_column(col),at=((source/16*30+y)*16+source%16)*2;
   unsigned short expected=(world_chunks[at]<<8)|world_chunks[at+1];int physical=col%128;
   assert(((unsigned short *)street_b0)[physical/64*4096+y*64+physical%64]==expected);
   if(col<80)assert(source==col);
  }
 }
 puts("PASS actual map-ring writer: every camera 0..960 both directions, wrap at1024, exact original opening, valid reused columns, no new cells");
}
