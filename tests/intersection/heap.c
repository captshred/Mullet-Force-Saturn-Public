#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#define JO_MALLOC_TRY_REUSE_BLOCK 1
#include "parallax.c"
unsigned char street_a0[131072],street_b0[131072];
static void *owner;static int allocated,frees,bad_size,read_fail,alloc_fail,wrong_length,oversize;
static unsigned requested;
void *jo_malloc_with_behaviour(unsigned n,int behavior){assert(behavior==1 && !allocated);requested=n;if(alloc_fail)return 0;allocated=1;return oversize?(void*)0x060bff00:owner;}
void jo_free(void *p){assert(allocated && p==(oversize?(void*)0x060bff00:owner));allocated=0;frees++;}
int GFS_NameToId(Sint8 *p){assert(!strcmp((char*)p,"IXPACK.BIN"));return 1;}
GfsHn GFS_Open(int i){assert(i==1);return (void*)1;}
void GFS_Close(GfsHn h){assert(h==(void*)1);}
void GFS_GetFileSize(GfsHn h,Sint32 *s,Sint32 *c,Sint32 *last){assert(h==(void*)1);unsigned n=MF_INTERSECTION_PACK_BYTES+(bad_size?1:0);*s=2048;*c=(n+2047)/2048;*last=n-(*c-1)*2048;}
char *jo_fs_read_file_ptr(const char *name,void *p,int *len){assert(!strcmp(name,"IXPACK.BIN") && p==owner && allocated);if(read_fail)return 0;FILE *f=fopen("assets/level1-intersection/IXPACK.BIN","rb");assert(f && fread(p,1,MF_INTERSECTION_PACK_BYTES,f)==MF_INTERSECTION_PACK_BYTES);fclose(f);((unsigned char*)p)[MF_INTERSECTION_PACK_BYTES]=0;*len=MF_INTERSECTION_PACK_BYTES+(wrong_length?1:0);return p;}
int main(void){
 owner=mmap((void*)0x06030000,393216,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(owner==(void*)0x06030000);
 for(int i=0;i<8;i++){
  assert(world_pack_load());assert(world_packed==owner && world_block_cache==world_packed+MF_WORLD_PACK_STORAGE && requested==MF_WORLD_BACKGROUND_HEAP);
  world_blocks_reset();assert(world_block_index && world_prefetch_queue && world_prefetch_queued);
  world_release();assert(!world_packed && !world_block_cache && !world_block_index && !allocated);
 }
 int before=frees;
 bad_size=1;assert(!world_pack_load() && !allocated);bad_size=0;
 alloc_fail=1;assert(!world_pack_load() && !allocated);alloc_fail=0;
 read_fail=1;assert(!world_pack_load());world_release();read_fail=0;
 wrong_length=1;assert(!world_pack_load());world_release();wrong_length=0;
 oversize=1;assert(!world_pack_load());world_release();oversize=0;
 assert(!allocated && !world_packed && !world_block_cache && frees==before+3);
 assert(world_pack_load());live_ready=1;mf_parallax_leave();assert(!live_ready && !allocated && !world_packed && !world_block_cache);
 munmap(owner,393216);printf("PASS real combined heap ownership: %u bytes, eight reloads, exact-size check, allocation/read/length/SDK-bound failures, base-only free and Stage2 retirement\n",requested);
}
