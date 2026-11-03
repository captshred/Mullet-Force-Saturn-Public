#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/parallax.c"
unsigned char street_a0[131072],street_b0[131072];
static int allocation,reads,dmas,off,auto_result,sky_x,street_x,read_failure,size_failure,wrong_address;
static const char *names[]={"PCHUNK.BIN","PSKY.BIN","PSMAP.BIN"};
static int length(int id){return id==0?4800:8192;}
int GFS_NameToId(Sint8 *name){int i;for(i=0;i<3;i++)if(!strcmp((char *)name,names[i]))return i;return -1;}
GfsHn GFS_Open(int id){return (void *)(size_t)(id+1);}
void GFS_GetFileSize(GfsHn f,Sint32 *s,Sint32 *n,Sint32 *last)
{int bytes=length((int)(size_t)f-1)-size_failure;*s=2048;*n=(bytes+2047)/2048;*last=bytes-(*n-1)*2048;}
void GFS_Close(GfsHn f){(void)f;}
char *jo_fs_read_file_ptr(const char *name,void *p,int *len)
{
    char path[128];FILE *f;int id=GFS_NameToId((Sint8 *)name);
    if(read_failure)return NULL;
    snprintf(path,sizeof(path),"assets/parallax/%s",name);f=fopen(path,"rb");assert(f);
    *len=length(id);assert(fread(p,1,(size_t)*len,f)==(size_t)*len);fclose(f);
    ((char *)p)[*len]=0;reads++;return p;
}
void *jo_vdp2_malloc(int usage,unsigned bytes)
{assert(usage==JO_VDP2_RAM_MAP_NBG1 && bytes==8192);return street_b0+0x4000+8192*(allocation++)+wrong_address;}
void *jo_malloc_with_behaviour(unsigned n,int b){assert(n==8193 && b==JO_FAST_ALLOCATION);return malloc(n);}
void jo_free(void *p){free(p);}
void jo_dma_copy(const void *p,void *d,unsigned n){assert(off && n==8192);memcpy(d,p,n);dmas++;}
void slTVOff(void){off=1;}
void slTVOn(void){off=0;}
void slCharNbg2(int a,int b){assert(a==COL_TYPE_256 && b==CHAR_SIZE_1x1);}
void slPageNbg2(void *a,void *b,int f){assert(a==street_b0+0x4000 && !b && f==(PNB_1WORD|CN_12BIT));}
void slPlaneNbg2(int p){assert(p==PL_SIZE_1x1);}
void slMapNbg2(void *a,void *b,void *c,void *d){assert(a==street_b0+0x6000 && a==b && a==c && a==d);}
void slPriorityNbg2(int p){assert(p==1);}
void slPriorityNbg1(int p){assert(p==1 || p==2);}
void slScrWindow1(unsigned short x,unsigned short y,unsigned short r,unsigned short b){assert(!x && y==1 && r==319 && b==55);}
void slScrWindowModeNbg2(unsigned short m){assert(m==win1_IN);}
void slScrWindow0(unsigned short x,unsigned short y,unsigned short r,unsigned short b){assert(x<=1 && (y==1 || y==56) && r==319 && b==239);}
void slScrPosNbg1(int x,int y){assert(y==-65536);street_x=x;}
void slScrPosNbg2(int x,int y){assert(!y);sky_x=x;}
int slScrAutoDisp(unsigned flags){assert(off && (flags==3 || flags==7));return flags==7?auto_result:0;}
void slScrDisp(unsigned long flags){assert(flags==NBG2OFF);}
void jo_clear_screen_line(int y){(void)y;}
void jo_print(int x,int y,const char *p){(void)x;(void)y;(void)p;}
void jo_printf(int x,int y,const char *p,...){(void)x;(void)y;(void)p;}
static void visible(int camera)
{
    int x,row;
    for(x=camera?0:1;x<320;x+=1)for(row=0;row<30;row++) {
        int world=camera-1+x,column=world/8;
        int ring=column%128;
        unsigned actual=street_map()[(ring/64)*4096+row*64+ring%64];
        assert(actual==pattern((world/128)%5,row,column%16));
    }
}
int main(void)
{
    int camera,previous,initial_reads,i;unsigned char original[16384];FILE *f;
    memset(street_b0,0xa5,sizeof(street_b0));
    assert(mf_parallax_load() && !mf_parallax_error() && !mf_parallax_active());
    assert(reads==3 && dmas==2);
    for(i=0x8000;i<131072;i++)assert(street_b0[i]==0xa5);
    assert(mf_parallax_enter() && mf_parallax_active() && preview.uploads==8);
    initial_reads=reads;
    for(camera=1;camera<=7872;camera++) {
        previous=preview.camera;preview.camera=camera;ensure_cache();
        visible(previous);visible(camera);assert(preview.last_bytes<=960);
        mf_parallax_draw();assert(street_x==(camera-1)*65536 && sky_x==(camera/4)*65536);
    }
    for(camera=7871;camera>=0;camera--) {previous=preview.camera;preview.camera=camera;ensure_cache();visible(previous);visible(camera);assert(preview.last_bytes<=960);}
    mf_parallax_update(MF_LEFT|MF_UP,999);assert(preview.camera==0);
    mf_parallax_update(MF_RIGHT|MF_UP,999);assert(preview.camera==48 && preview.last_bytes<=960);
    mf_parallax_update(MF_RIGHT|MF_LEFT,6);assert(preview.camera==48);
    assert(reads==initial_reads);mf_parallax_leave();assert(!mf_parallax_active() && !off);
    f=fopen("assets/vdp2/STMAP.BIN","rb");assert(f);assert(fread(original,1,sizeof(original),f)==sizeof(original));fclose(f);
    for(i=0;i<8192;i++)assert(street_map()[i]==((unsigned)original[i*2]<<8|original[i*2+1]));
    assert(mf_parallax_enter());mf_parallax_leave();
    auto_result=-1;assert(!mf_parallax_enter() && preview.error==850 && !mf_parallax_active() && !off);
    preview.error=0;size_failure=1;assert(!mf_parallax_load() && preview.error==810);
    size_failure=0;read_failure=1;assert(!mf_parallax_load() && preview.error==811);
    read_failure=0;allocation=0;wrong_address=1;assert(!mf_parallax_load() && preview.error==820);
    puts("PASS parallax: actual loader/cache/restore; 7873 forward/backward offsets, wrap/reversal, old and next viewport safety, <=960-byte chunk refresh, quarter-speed skyline, clamps, no runtime CD/heap/texture/palette allocation, exact original map restore and failure guards.");
}
