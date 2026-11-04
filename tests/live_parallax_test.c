#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/parallax.c"
unsigned char street_a0[131072],street_b0[131072];
static int allocations,reads,uploads,x1,y1,x2,y2,top,left,on;
void *jo_vdp2_malloc(int kind,unsigned size){assert(kind==JO_VDP2_RAM_MAP_NBG1);assert(size==(allocations?16384:32768));return street_b0+(allocations++?0xc000:0x4000);}
char *jo_fs_read_file(const char *n,int *bytes){char path[160];FILE *f;char *p;sprintf(path,"assets/city-gameplay-parallax/%s",n);f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);*bytes=ftell(f);rewind(f);p=malloc(*bytes);assert(fread(p,1,*bytes,f)==(size_t)*bytes);fclose(f);reads++;return p;}
void jo_free(void *p){free(p);}
void jo_dma_copy(const void *p,void *q,unsigned n){assert(!on);memcpy(q,p,n);uploads++;}
void slTVOff(void){on=0;} void slTVOn(void){on=1;}
void slCharNbg2(int a,int b){assert(a==COL_TYPE_256 && b==CHAR_SIZE_1x1);}
void slPageNbg2(void *a,void *b,int c){assert(a==street_b0+0x4000 && !b && c==(PNB_1WORD|CN_12BIT));}
void slPlaneNbg2(int p){assert(p==PL_SIZE_2x1);}
void slMapNbg2(void *a,void *b,void *c,void *d){assert(a==street_b0+0xc000 && b==a && c==a && d==a);}
void slPriorityNbg2(int p){assert(p==1);}void slPriorityNbg1(int p){assert(p==2);}
void slScrWindow1(unsigned short l,unsigned short t,unsigned short r,unsigned short b){assert(t==1 && r==319 && b==55);left=l;}
void slScrWindowModeNbg2(unsigned short p){assert(p==win1_IN);}
int slScrAutoDisp(unsigned p){assert(p==(NBG0ON|NBG1ON|NBG2ON));return 0;}
void slScrPosNbg1(int x,int y){x1=x;y1=y;}void slScrPosNbg2(int x,int y){x2=x;y2=y;}
void slScrWindow0(unsigned short l,unsigned short t,unsigned short r,unsigned short b){assert(r==319 && b==239);top=t;left=l;}
int main(void){int c;memset(street_b0,0xa5,sizeof(street_b0));assert(mf_parallax_load());for(c=0;c<=320;c++){mf_parallax_game_draw(c);assert(x1==(c-1)*65536 && x2==c*16384-65536 && y1==-65536 && y2==-65536 && top==56 && left==(c<4 || c%128==0));}assert(!mf_parallax_enter() && !mf_parallax_active());assert(reads==2 && uploads==2 && allocations==2);for(c=0;c<0x4000;c++)assert(street_b0[c]==0xa5);for(c=0x10000;c<131072;c++)assert(street_b0[c]==0xa5);puts("PASS live gameplay parallax: actual load/draw, aligned banks, all cameras, quarter speed, no streaming or preview activation");}
