#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/street.c"

unsigned char street_a0[131072],street_b0[131072];
jo_color *nbg1_bitmap;
static unsigned short colors[256];
static int tv_on=1,released,uploads,reads,scroll_x,scroll_y,bad_bank,short_file;
static int configured,priorities[8],cycles,sprite_uploads,sprite_draws;
static int auto_result;
static int window_left,window_mode;
static int allocation_failure,wrong_map;
static const char *missing_name,*null_read,*short_name;
static jo_palette *loading;
int GFS_NameToId(Sint8 *name)
{
    if(missing_name && !strcmp((char *)name,missing_name))return -1;
    if(!strcmp((char *)name,"0.BIN"))return 0;
    if(!strcmp((char *)name,"ST0.TGA"))return 1;
    if(!strcmp((char *)name,"STCELLS.BIN"))return 11;
    if(!strcmp((char *)name,"STMAP.BIN"))return 12;
    if(!strcmp((char *)name,"STPAL.BIN"))return 13;
    return -1;
}
void jo_printf(int x,int y,const char *format,...){(void)x;(void)y;(void)format;}
char *jo_fs_read_file(const char *name,int *length)
{
    char path[128],*data;FILE *f;long n;
    if(null_read && !strcmp(name,null_read))return NULL;
    snprintf(path,sizeof(path),"assets/vdp2/%s",name);f=fopen(path,"rb");assert(f);
    assert(!fseek(f,0,SEEK_END));n=ftell(f);rewind(f);assert(n>0);
    data=malloc((size_t)n);assert(data);assert(fread(data,1,(size_t)n,f)==(size_t)n);fclose(f);
    *length=(int)n-(short_file || (short_name && !strcmp(name,short_name)));reads++;return data;
}
void jo_free(void *p) {free(p);}
void jo_dma_copy(const void *src,void *dst,unsigned n)
{
    assert(!tv_on);
    assert((dst==street_a0 && n==90240)||(dst==street_b0 && n==16384));
    memcpy(dst,src,n);uploads++;
}
void jo_palette_to_cram(unsigned short *src,unsigned short *dst,unsigned n)
{
    assert(!tv_on && dst==colors && n==255);memcpy(dst,src,n*2);uploads++;
}
void jo_vdp2_free(const void *p) {assert(!tv_on && p==street_a0);released++;}
void *jo_vdp2_malloc(int usage,unsigned n)
{
    assert(!tv_on && released);
    if(usage==allocation_failure)return NULL;
    if(usage==JO_VDP2_RAM_CELL_NBG1){assert(n==90240);return street_a0+bad_bank;}
    assert(usage==JO_VDP2_RAM_MAP_NBG1 && n==16384);return street_b0+wrong_map;
}
void slTVOff(void){tv_on=0;}
void slTVOn(void){tv_on=1;}
void slCharNbg1(int c,int s){assert(c==COL_TYPE_256 && s==CHAR_SIZE_1x1);configured++;}
void slPageNbg1(void *c,void *p,int f){assert(c==street_a0 && !p && f==(PNB_1WORD|CN_12BIT));configured++;}
void slPlaneNbg1(int n){assert(n==PL_SIZE_2x1);configured++;}
void slMapNbg1(void *a,void *b,void *c,void *d){assert(a==street_b0 && b==a && c==a && d==a);configured++;}
void slZoomNbg1(int x,int y){assert(x==65536 && y==65536);configured++;}
void slScrPosNbg1(int x,int y){scroll_x=x;scroll_y=y;}
void slScrWindow0(unsigned short x,unsigned short y,unsigned short r,unsigned short b)
{assert(x<=1 && y==1 && r==319 && b==239);window_left=x;}
void slScrWindowModeNbg1(unsigned short mode){assert(mode==win0_IN);window_mode=mode;}
void slPriorityNbg1(int n){assert(n==1);}
void slPriorityNbg0(int n){assert(n==7);}
void test_priority(int i,int n){assert(n==4);priorities[i]=n;}
int slScrAutoDisp(unsigned flags)
{
    int i;assert(!tv_on && flags==(NBG0ON|NBG1ON) && configured==5);
    for(i=0;i<8;i++)assert(priorities[i]==4);
    cycles++;return auto_result; /* Pinned SGL: zero is SUCCESS, negative is failure. */
}
void jo_set_tga_default_palette(jo_palette *p){loading=p;}
int jo_sprite_add_tga(void *dir,const char *name,int transparent)
{
    char expected[12];(void)dir;
    snprintf(expected,sizeof(expected),"ST%d.TGA",sprite_uploads);
    assert(loading && loading->id==1 && transparent==1 && !strcmp(name,expected));
    return 100+sprite_uploads++;
}
void jo_sprite_set_palette(int p){assert(p==1);}
void jo_sprite_draw3D2(int id,int x,int y,int z)
{assert(id>=100 && id<=104 && x>-128 && x<320 && y==0 && z==500);sprite_draws++;}

int main(void)
{
    int sprites[5]={0},camera;jo_palette pal={1,colors};
    assert(diagnostic.root_executable==-99 && diagnostic.root_street==-99);
    memset(street_a0,0xa5,sizeof(street_a0));memset(street_b0,0xa5,sizeof(street_b0));
    colors[255]=0xbeef;nbg1_bitmap=(jo_color *)street_a0;
#if MF_VDP2_STREET && MF_STREET_LEGACY_CHECK
    assert(!mf_street_load(&pal,sprites));
    assert(diagnostic.code==150 && diagnostic.auto_result==0 && diagnostic.read_mask==7);
    puts("PASS: dc962cd legacy condition reproduces S150 despite successful SGL setup and all three reads.");
    return 0;
#endif
    assert(mf_street_load(&pal,sprites));
#if MF_VDP2_STREET
    assert(diagnostic.code==0 && diagnostic.step==199 && diagnostic.read_mask==7 && diagnostic.auto_result==0);
    assert(released==1 && !nbg1_bitmap && uploads==3 && reads==3 && cycles==1 && tv_on);
    assert(!sprite_uploads && colors[255]==0xbeef);
    for(camera=90240;camera<131072;camera++)assert(street_a0[camera]==0xa5);
    for(camera=16384;camera<131072;camera++)assert(street_b0[camera]==0xa5);
    for(camera=0;camera<=320;camera++) {
        mf_street_draw(sprites,pal.id,camera);
        assert(scroll_x==(camera-1)*65536 && scroll_y==-65536);
        assert(window_mode==win0_IN && window_left==(camera%128==0));
    }
    assert(!sprite_draws);
    auto_result=-1;configured=0;nbg1_bitmap=(jo_color *)street_a0;
    assert(!mf_street_load(&pal,sprites) && diagnostic.code==150 && diagnostic.auto_result==-1 && tv_on);
    auto_result=0;
    bad_bank=1;nbg1_bitmap=(jo_color *)street_a0;
    assert(!mf_street_load(&pal,sprites) && diagnostic.code==111 && tv_on && reads==6);
    bad_bank=0;short_file=1;nbg1_bitmap=(jo_color *)street_a0;
    assert(!mf_street_load(&pal,sprites) && diagnostic.code==122 && tv_on && uploads==6);
    short_file=0;
    {
        const char *names[]={"STCELLS.BIN","STMAP.BIN","STPAL.BIN"};
        int index;
        for(index=0;index<3;index++) {
            missing_name=names[index];nbg1_bitmap=(jo_color *)street_a0;
            assert(!mf_street_load(&pal,sprites) && diagnostic.code==120+10*index && tv_on);
            missing_name=NULL;null_read=names[index];nbg1_bitmap=(jo_color *)street_a0;
            assert(!mf_street_load(&pal,sprites) && diagnostic.code==121+10*index && tv_on);
            null_read=NULL;short_name=names[index];nbg1_bitmap=(jo_color *)street_a0;
            assert(!mf_street_load(&pal,sprites) && diagnostic.code==122+10*index && tv_on);
            short_name=NULL;
        }
    }
    allocation_failure=JO_VDP2_RAM_CELL_NBG1;nbg1_bitmap=(jo_color *)street_a0;
    assert(!mf_street_load(&pal,sprites) && diagnostic.code==110 && tv_on);
    allocation_failure=JO_VDP2_RAM_MAP_NBG1;nbg1_bitmap=(jo_color *)street_a0;
    assert(!mf_street_load(&pal,sprites) && diagnostic.code==112 && tv_on);
    allocation_failure=0;wrong_map=1;nbg1_bitmap=(jo_color *)street_a0;
    assert(!mf_street_load(&pal,sprites) && diagnostic.code==113 && tv_on);
    wrong_map=0;pal.id=2;
    assert(!mf_street_load(&pal,sprites) && diagnostic.code==101);
    pal.id=1;missing_name="0.BIN";
    assert(!mf_street_load(&pal,sprites) && diagnostic.code==102);
    missing_name=NULL;
    puts("PASS VDP2: actual loader, zero street sprite uploads/draws, exact allocations, untouched bank tails, palette guard, two-page config, priorities, cycle setup, all camera offsets and failure guards.");
#else
    assert(sprite_uploads==5 && !uploads && !released && !reads);
    for(camera=0;camera<=320;camera++)mf_street_draw(sprites,pal.id,camera);
    assert(sprite_draws>0);
    puts("PASS VDP1 fallback: five original TGAs and original scrolling sprite path; no VDP2 allocation or uploads.");
#endif
    return 0;
}
