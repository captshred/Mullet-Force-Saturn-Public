/* Actual stage loader/dispatcher with SDK commands and SCSP RAM mocked. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned char ram[524288];
#define MF_WS_SOUND_BASE ram
#include "../src/wingsuit_audio.c"
char sddrvstsk[MF_SOUND_DRIVER_BYTES];
static int stopped=1,inflight,reads,frees,starts,accept=1,initializations;
static const char *fail_name;
char *jo_fs_read_file(const char *n,int *size){(void)n;(void)size;assert(0);return NULL;}
static char *read_exact(const char *name,int expected)
{
    char path[128],*b;FILE *f;int n;
    reads++;if(fail_name && !strcmp(fail_name,name))return NULL;
    snprintf(path,sizeof(path),"assets/wingsuit/%s",name);f=fopen(path,"rb");assert(f);
    fseek(f,0,SEEK_END);n=(int)ftell(f);rewind(f);assert(n==expected);
    b=malloc(n);assert(b && fread(b,1,n,f)==(size_t)n);fclose(f);return b;
}
void jo_free(void *p){assert(!inflight);frees++;free(p);}
void slSoundOffWait(void){stopped=1;}
void slSoundOnWait(void){assert(stopped && !ram[0x4e1]);stopped=0;}
void slDMACopy(void *s,void *d,unsigned n){assert(stopped && !inflight && (unsigned char *)d>=ram && (unsigned char *)d+n<=ram+sizeof(ram));memcpy(d,s,n);inflight=1;}
void slDMAWait(void){inflight=0;}
void slSndFlush(void){}
void slInitSound(Uint8 *p,unsigned s,Uint8 *m,unsigned n){assert(stopped && p==(Uint8 *)sddrvstsk && s==MF_SOUND_DRIVER_BYTES && m && n==MF_WS_MAP_BYTES);inflight=1;}
void SND_Init(SndIniDt *p){assert(stopped && p->program==(Uint16 *)sddrvstsk && p->program_size==MF_SOUND_DRIVER_BYTES && p->map_size==MF_WS_MAP_BYTES);initializations++;}
int SND_ChgMap(int n){assert(!n);return 0;}
int SND_StopDsp(void){return 0;}
int SND_SetCdDaLev(int l,int r){assert(!l && !r);return 0;}
int SND_SetTlVl(int v){assert(v==15);return 0;}
int SND_SetSeqVl(int p,int v,int f){assert(!stopped && p>=1 && p<=4 && v==MF_SFX_VOLUME && !f);return !accept;}
int SND_StartSeq(int p,int b,int song,int pr){assert(!stopped && p>=1 && p<=4 && !b && !song && pr==MF_SFX_PRIORITY);if(!accept)return 1;starts++;return 0;}
int main(void)
{
    int i,n;const char *names[]={"WDEATH.MAP","WDEATH.SEQ","WDEATH.TON"};
    memset(ram,0x55,sizeof(ram));assert(mf_ws_audio_load(read_exact));assert(reads==3 && frees==3 && initializations==1 && !stopped);
    assert(ram[MF_WS_TON_ADDR+MF_WS_TON_BYTES]==0x55); /* strict high-water */
    for(i=0;i<2;i++){
        const char *name=i?"WDEATH.TON":"WDEATH.SEQ";int size=i?MF_WS_TON_BYTES:MF_WS_SEQ_BYTES;
        char *b=read_exact(name,size);assert(!memcmp(b,ram+(i?MF_WS_TON_ADDR:MF_WS_SEQ_ADDR),size));jo_free(b);
    }
    mf_ws_audio_events(10);mf_ws_audio_step(100);assert(starts==4 && pending==6);
    for(i=0;i<6;i++){mf_ws_audio_step(100);}assert(starts==4);
    mf_ws_audio_step(148);assert(starts==4);mf_ws_audio_step(149);assert(starts==8);
    mf_ws_audio_step(198);assert(starts==10 && !pending);
    for(i=0;i<100;i++){mf_ws_audio_step(200+i);}assert(starts==10);
    accept=0;mf_ws_audio_events(1);mf_ws_audio_step(400);assert(starts==10 && pending==1);
    accept=1;mf_ws_audio_step(401);assert(starts==11 && !pending);
    for(i=0;i<3;i++){
        fail_name=names[i];assert(!mf_ws_audio_load(read_exact));assert(!ready);
        n=starts;mf_ws_audio_events(1);mf_ws_audio_step(500);assert(starts==n);
        if(i)assert(stopped);
    }
    fail_name=NULL;assert(mf_ws_audio_load(read_exact));
    mf_ws_audio_events(1);mf_ws_audio_step(~0u-20);assert(starts==12);
    mf_ws_audio_events(4);mf_ws_audio_step(~0u-20);assert(starts==15 && pending==1);
    mf_ws_audio_step(27);assert(starts==15);mf_ws_audio_step(28);assert(starts==16 && !pending);
    puts("PASS death audio: exact stage bank, stopped CPU uploads, DMA source lifetime, four ports, ten-event burst once each, rejection retry, VBlank/release guard and clock wrap, failed loads disabled");
}
