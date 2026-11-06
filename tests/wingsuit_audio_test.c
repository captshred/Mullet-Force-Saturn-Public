/* Actual simulation/transport with SDK commands and SCSP RAM mocked. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
static unsigned char ram[524288];
#define MF_WS_SOUND_BASE ram
#include "../src/wingsuit_audio.c"
#include "../src/wingsuit.c"
char sddrvstsk[MF_SOUND_DRIVER_BYTES];
static int stopped=1,inflight,reads,frees,accept=1,initializations,commands;
static unsigned clock_now;
static int starts[8],stops[8],notes[2],offs[2],bank[2],program[2],live[8],status_error;
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
void slSoundOnWait(void){assert(stopped && ram[0x4e1]==0x80);stopped=0;}
void slDMACopy(void *s,void *d,unsigned n){assert(stopped && !inflight && (unsigned char *)d>=ram && (unsigned char *)d+n<=ram+sizeof(ram));memcpy(d,s,n);inflight=1;}
void slDMAWait(void){inflight=0;}
void slSndFlush(void){}
void slInitSound(Uint8 *p,unsigned s,Uint8 *m,unsigned n){assert(stopped && p==(Uint8 *)sddrvstsk && s==MF_SOUND_DRIVER_BYTES && m && n==MF_WS_MAP_BYTES);inflight=1;ram[0x4e1]=0x80;commands=0;memset(live,0,sizeof(live));memset(bank,0,sizeof(bank));memset(program,0,sizeof(program));}
void SND_Init(SndIniDt *p){assert(stopped && p->program==(Uint16 *)sddrvstsk && p->program_size==MF_SOUND_DRIVER_BYTES && p->map_size==MF_WS_MAP_BYTES/2);initializations++;}
int SND_ChgMap(int n){assert(!n);return 0;}
int SND_StopDsp(void){return 0;}
int SND_SetCdDaLev(int l,int r){assert(!l && !r);return 0;}
int SND_SetTlVl(int v){assert(v==15);return 0;}
static int accepted(void){if(!accept)return 0;assert(++commands<=8);return 1;}
static int check_volume(int p,int v,int f){assert(!stopped && p>=0 && p<8 && v==(p<2?MF_WS_FLAME_VOLUME:p<4?MF_WS_SHOT_VOLUME:MF_SFX_VOLUME) && !f);return accepted()?0:1;}
static int check_start(int p,int b,int song,int pr){assert(!stopped && p>=2 && p<8 && !b && song==(p<4?1:0) && !pr);if(!accepted())return 1;starts[p]++;live[p]=1;return 0;}
static int check_stop(int p){assert(p==2 || p==3);if(!accepted())return 1;stops[p]++;live[p]=0;return 0;}
static int check_midi(int p,int pr,int cmd,int channel,int a,int b)
{
    assert(p>=0 && p<2 && !pr && channel==p);
    if(!accepted())return 1;
    if(cmd==3){assert(a==32 && !b);bank[p]=1;}
    else if(cmd==4){assert(a==2 && !b && bank[p]);program[p]=1;}
    else if(cmd==1){assert(a==60 && b==110 && bank[p] && program[p] && !live[p]);live[p]=1;notes[p]++;}
    else {assert(cmd==0 && a==60 && !b && live[p]);live[p]=0;offs[p]++;}
    return 0;
}
int slSoundRequest(const char *format,...)
{
    va_list ap;int cmd,a=0,b=0,c=0,d=0,result=0;
    assert(ram[0x4e1]==0x80);va_start(ap,format);cmd=va_arg(ap,int);
    if(strlen(format)>0)a=va_arg(ap,int);
    if(strlen(format)>1)b=va_arg(ap,int);
    if(strlen(format)>2)c=va_arg(ap,int);
    if(strlen(format)>3)d=va_arg(ap,int);
    va_end(ap);
    if(cmd==SND_SEQ_VOL){assert(!strcmp(format,"bbb"));result=check_volume(a,b,c);}
    else if(cmd==SND_SEQ_START){assert(!strcmp(format,"bbbb"));result=check_start(a,b,c,d);}
    else if(cmd==SND_SEQ_STOP){assert(!strcmp(format,"b"));result=check_stop(a);}
    else if(cmd==SND_MIDI_CTRL_DIR){assert(!strcmp(format,"bbbb"));result=check_midi(b>>5,0,a,b&31,c,d);}
    else {
        assert(cmd==SND_MAP_CHG || cmd==SND_DSP_STOP || cmd==SND_CDDA_LEV || cmd==SND_TTL_VOL);
        if(cmd==SND_TTL_VOL)assert(a==15);
        else assert(!a && !b);
    }
    return result?-1:0;
}
void SND_GetSeqStat(SndSeqStat *s,int p){assert(p>=2 && p<8);s->mode=live[p];s->stat=p==4?status_error:0;}
static void pump(unsigned now,unsigned focus){clock_now=now;commands=0;mf_ws_audio_step(now,focus);}
static void load(unsigned now)
{
    fail_name=NULL;accept=1;status_error=0;assert(mf_ws_audio_load(read_exact));
    pump(now,0);pump(now+1,0);pump(now+2,0);assert(flame[0].prep==3 && flame[1].prep==3);
}
static void reset_counts(void){memset(starts,0,sizeof(starts));memset(stops,0,sizeof(stops));memset(notes,0,sizeof(notes));memset(offs,0,sizeof(offs));}
static void sim(mf_wingsuit *g,unsigned a,unsigned b,unsigned press)
{
    unsigned held[2]={a,b},edge[2]={press,0},focus=0;int i;
    mf_ws_step(g,held,edge,3);mf_ws_audio_events(g->deaths,g->shots_fired);
    if(!g->paused)for(i=0;i<2;i++)if(mf_ws_beam_active(g,i))focus|=1u<<i;
    pump(clock_now+1,focus);
}
int main(void)
{
    int i,n,r;mf_wingsuit g;const char *names[]={"WDEATH.MAP","WDEATH.SEQ","WDEATH.TON"};
    memset(ram,0x55,sizeof(ram));load(0);assert(reads==3 && frees==3 && initializations==1 && !stopped);
    assert(ram[MF_WS_TON_ADDR+MF_WS_TON_BYTES]==0x55);
    for(i=0;i<2;i++){
        const char *name=i?"WDEATH.TON":"WDEATH.SEQ";int size=i?MF_WS_TON_BYTES:MF_WS_SEQ_BYTES;
        char *b=read_exact(name,size);assert(!memcmp(b,ram+(i?MF_WS_TON_ADDR:MF_WS_SEQ_ADDR),size));jo_free(b);
    }
    r=reads;reset_counts();mf_ws_init(&g,1);g.spawn=10000;
    sim(&g,MF_A,0,0);assert(g.shots_fired==1 && starts[2]==1 && !notes[0]);
    for(i=2;i<=19;i++){sim(&g,MF_A,0,0);assert(!notes[0]);}
    sim(&g,MF_A,0,0);assert(g.players[0].shot_hold==20 && notes[0]==1 && live[0]);
    for(i=0;i<1000;i++)sim(&g,MF_A,0,0);
    assert(notes[0]==1 && live[0]);
    for(i=0;i<20;i++){sim(&g,MF_A,MF_A,0);if(i<19)assert(!notes[1]);}
    assert(notes[0]==1 && notes[1]==1 && live[0] && live[1]);
    sim(&g,0,MF_A,0);assert(!live[0] && live[1] && offs[0]==1 && !offs[1]);
    sim(&g,0,MF_A,MF_START);assert(g.paused && !live[1] && offs[1]==1);
    for(i=0;i<10;i++)sim(&g,0,MF_A,0);
    sim(&g,0,MF_A,MF_START);assert(!g.paused && notes[1]==2 && live[1]);
    g.players[1].invulnerable=0;g.hostile[0]=(mf_ws_hostile_shot){1,g.players[1].x,g.players[1].y-768,0,60,0,768};
    sim(&g,0,MF_A,0);assert(g.players[1].respawn && !live[1] && offs[1]==2);
    n=starts[4]+starts[5]+starts[6]+starts[7];assert(n==1);
    for(i=0;i<20;i++)sim(&g,0,MF_A,0);
    assert(starts[4]+starts[5]+starts[6]+starts[7]==n && !live[1]);assert(reads==r);
    load(1700);reset_counts();mf_ws_init(&g,1);g.spawn=10000;
    g.players[0].shot_hold=19;g.enemies[0]=(mf_ws_enemy){1,130*256,100*256,0,0};
    sim(&g,MF_A,0,0);assert(g.deaths==1 && starts[4]==1);
    for(i=0;i<20;i++)sim(&g,MF_A,0,0);
    assert(starts[4]+starts[5]+starts[6]+starts[7]==1 && notes[0]==1);
    load(1800);reset_counts();mf_ws_init(&g,1);g.spawn=10000;
    for(i=0;i<32;i++)g.shots[i]=(mf_ws_shot){1,160*256,100*256,1,90,0};
    sim(&g,MF_A,0,0);assert(!g.shots_fired && !starts[2] && !starts[3]);
    g.shots[5].active=0;g.players[0].shot_hold=0;
    sim(&g,MF_A,0,0);assert(g.shots_fired==1 && starts[2]==1);
    assert(g.shots[5].x==g.players[0].x && !g.shots[5].vx);
    load(2000);reset_counts();mf_ws_audio_events(1,2);pump(2003,1);
    assert(live[0] && live[2] && live[4] && notes[0]==1);
    mf_ws_audio_events(1,0);pump(2004,3);assert(live[0] && live[1] && live[4] && live[5] && notes[0]==1 && notes[1]==1);
    load(2100);reset_counts();mf_ws_audio_events(1,3);pump(2103,0);
    assert(live[2] && live[3] && live[4] && starts[2]==1 && starts[3]==1);
    mf_ws_audio_events(0,1);pump(2104,0);assert(stops[2]==1 && !stops[3] && live[4]);
    pump(2104,0);assert(starts[2]==1);pump(2105,0);assert(starts[2]==2 && live[3] && live[4]);
    load(2200);reset_counts();mf_ws_audio_events(10,0);pump(2203,3);
    /* Two flame NOTE ON commands leave room for three explosion starts. */
    for(i=2204;i<=2303;i++)pump((unsigned)i,3);
    assert(starts[4]+starts[5]+starts[6]+starts[7]==10 && !pending_explosions);
    assert(notes[0]==1 && notes[1]==1 && !offs[0] && !offs[1]);
    load(3000);reset_counts();accept=0;mf_ws_audio_events(1,1);pump(3003,1);
    assert(!notes[0] && !starts[4] && !starts[2]);accept=1;pump(3004,1);assert(notes[0]==1 && starts[4]==1 && starts[2]==1);
    accept=0;pump(3005,0);assert(live[0]);accept=1;pump(3006,1);assert(!live[0] && offs[0]==1);
    pump(3007,1);assert(notes[0]==2);status_error=0x81;pump(3008,1);assert(mf_ws_audio_fault()==0x481);
    for(i=0;i<3;i++){
        fail_name=names[i];assert(!mf_ws_audio_load(read_exact));assert(!ready);
        n=starts[4];mf_ws_audio_events(1,3);pump(3100,3);assert(starts[4]==n);
    }
    load(~0u-3);reset_counts();mf_ws_audio_events(1,0);pump(~0u,1);
    pump(0,1);assert(notes[0]==1 && starts[4]==1);pump(48,1);assert(notes[0]==1);
    mf_ws_audio_events(1,0);pump(49,1);assert(starts[4]==2);
    puts("PASS Level 2 audio: real single-shot events; 19/20-tick ignition, indefinite sustain/no retrigger, release/pause/death and independent flames; three required polyphony mixes; explosion burst, shot-only oldest stealing, SDK rejection/release guard/clock wrap, DMA bank once and runtime status diagnostics");
}
