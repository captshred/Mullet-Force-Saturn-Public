/* Investigation only: production C included unchanged; SDK/68000/SCSP mocked. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
static unsigned char ram[0x80000];
static unsigned short regs[512];
#define MF_WS_SOUND_BASE ram
#define MF_WS_SLOT_REGS regs
#include "../src/wingsuit_audio.c"
char sddrvstsk[MF_SOUND_DRIVER_BYTES];
static int eager,gated,failflag,skipmap,injectfull;static unsigned ticks,ack_delay,due[8],rejections;
static void putword(unsigned a,unsigned v){ram[a]=v>>8;ram[a+1]=v;}
static void consume(int i){unsigned c=ram[0x700+i*16];if(c==8 && !skipmap)memcpy(ram+0x500,ram+0xa000,MF_WS_FIRE_MAP_BYTES);putword(0x41a,(sound_word(0x41a)&0x7f0)+16);ram[0x700+i*16]=0;}
static int submit(unsigned c){int i;for(i=0;i<8;i++)if(!ram[0x700+i*16]){ram[0x700+i*16]=c;due[i]=ticks+ack_delay;if(eager)consume(i);return 0;}rejections++;return 1;}
void slSoundOffWait(void){}
void slSoundOnWait(void){}
void slInitSound(Uint8 *p,unsigned n,Uint8 *m,unsigned s){(void)p;(void)n;memset(ram+0x700,0,128);putword(0x41a,0);memcpy(ram+0xa000,m,s);ram[0x4e1]=0x80;}
void slSndFlush(void){}
void slDMAWait(void){}
void slDMACopy(void *s,void *d,unsigned n){memcpy(d,s,n);}
void jo_free(void *p){free(p);}
void SND_Init(SndIniDt *p){assert(p->map_size==MF_WS_MUSIC_MAP_BYTES/2);memset(ram+0x700,0,128);}
int SND_ChgMap(int a){(void)a;return submit(8);}
int SND_StopDsp(void){return submit(12);}
int SND_SetCdDaLev(int a,int b){(void)a;(void)b;return submit(128);}
int SND_SetTlVl(int a){(void)a;return submit(130);}
int SND_SetSeqVl(int a,int b,int c){(void)a;(void)b;(void)c;return submit(5);}
int SND_CtrlDirMidi(int a,int b,int c,int d,int e,int f){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;return submit(9);}
int SND_StartSeq(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;return submit(1);}
int SND_StopSeq(int a){(void)a;return submit(2);}
char *jo_fs_read_file(const char *n,int *s){(void)n;(void)s;return NULL;}
static char *reader(const char *n,int size){char path[256];char *b=calloc(1,size);FILE *f;snprintf(path,sizeof(path),"assets/wingsuit/%s",n);f=fopen(path,"rb");assert(f);assert(fread(b,1,size,f)==(unsigned)size);fclose(f);return b;}
static unsigned rng=0xE008;static unsigned randn(void){rng=rng*1664525u+1013904223u;return rng;}
static int run(unsigned start_delay,unsigned gap,unsigned stride,unsigned seed,int warm){unsigned n,i;int r; rng=seed;ticks=0;rejections=0;if(!warm)memset(ram,0,sizeof(ram));assert(mf_ws_audio_load(reader,NULL));if(injectfull)for(i=3;i<8;i++){ram[0x700+i*16]=9;due[i]=0;}for(n=0;n<=300 && !mf_ws_audio_ready();n+=stride){ticks=n;if(n>=start_delay && (!gap || randn()%gap==0) && !failflag && !gated){for(i=0;i<8;i++)if(ram[0x700+i*16] && n>=due[i])consume(i);}mf_ws_audio_step(n,0);mf_ws_audio_step(n,0);}r=mf_ws_audio_ready();assert(mf_ws_startup_capture.frozen);{unsigned n=mf_ws_startup_capture.count;trace_sample(4);assert(n==mf_ws_startup_capture.count);if(r<0 && diagnostic.actual==12){mf_ws_startup_sample *p=&mf_ws_startup_capture.samples[(n-1)&127];assert(p->event==5 && p->queue[0]==12 && mf_ws_startup_capture.failure_queue[0]==12);}}return r;}
static void batch(const char *name,unsigned count,unsigned delay,unsigned gap,unsigned stride,int warm){unsigned i,ok=0,fail=0,exact=0;for(i=0;i<count;i++){int r=run(delay,gap,stride,i+1,warm);ok+=r==1;fail+=r==-1;exact+=r==-1 && !strcmp(diagnostic.operation,"DRIVER READY") && diagnostic.expected==0 && diagnostic.actual==12;}printf("%s trials=%u ready=%u timeout=%u exact_driver_ready_12=%u last=%s:%d/%d\n",name,count,ok,fail,exact,diagnostic.operation,diagnostic.expected,diagnostic.actual);}
int main(void){
 batch("cold_regular",1000,0,0,1,0);batch("warm_audio_reload_only",1000,0,0,1,1);
 eager=1;batch("synchronous_consumption",1000,0,0,1,0);eager=0;
 batch("initial_delay_60",1000,60,0,1,0);
 batch("initial_delay_119",1000,119,0,1,0);
 batch("initial_delay_120",1000,120,0,1,0);
 batch("initial_delay_121",1000,121,0,1,0);
 failflag=1;batch("missing_all_ack",1000,0,0,1,0);failflag=0;
 gated=1;batch("request_flag_gate_closed",1000,0,0,1,0);gated=0;
 injectfull=1;batch("full_queue_after_load",1000,0,0,1,0);injectfull=0;
 ack_delay=3;batch("each_ack_delayed_3",1000,0,0,1,0);ack_delay=0;
 batch("seeded_sparse_consumer_1_in_8",1000,0,8,1,0);
 batch("poll_every_4_vblanks",1000,0,0,4,0);
 batch("poll_every_8_vblanks",1000,0,0,8,0);
 batch("seeded_sparse_consumer_1_in_2",1000,0,2,1,0);
 batch("seeded_sparse_consumer_1_in_4",1000,0,4,1,0);
 skipmap=1;batch("missing_map_ack",1000,0,0,1,0);skipmap=0;
 {unsigned d,ok=0,fail=0,firstfail=999;for(d=0;d<=140;d++){int r=run(d,0,1,d+1,0);ok+=r==1;fail+=r==-1;if(r==-1 && firstfail==999)firstfail=d;}printf("initial_delay_sweep trials=141 ready=%u timeout=%u first_failure_delay=%u\n",ok,fail,firstfail);}
 {unsigned clock=777,n;mf_ws_audio_trace_clock(&clock);mf_ws_startup_capture.frozen=0;for(n=0;n<300;n++)trace_sample(4);assert(mf_ws_startup_capture.samples[(mf_ws_startup_capture.count-1)&127].tick==777);mf_ws_startup_capture.frozen=1;}
 return 0;
}
