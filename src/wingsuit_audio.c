#include <jo/jo.h>
#include <SEGA_SND.H>
#include <string.h>
#include "music_data.h"
#include "wingsuit_audio_data.h"
#include "wingsuit_audio.h"
#ifndef MF_WS_SOUND_BASE
#define MF_WS_SOUND_BASE ((unsigned char *)0x25a00000)
#endif
extern char sddrvstsk[];
/* Pinned driver 2.10: eight control numbers 0..7, 32 physical SCSP slots.
   Two persistent flames, two shot controls, four explosion controls. */
enum { FREE,VOLUME,START,PLAYING,RELEASE };
typedef struct { unsigned started,until,stopped;int state; } one_shot;
typedef struct { unsigned stopped;int prep,on,guard,stop; } flame_state;
static one_shot shot[2],explosion[4];
static flame_state flame[2];
static unsigned pending_shots,pending_explosions,last_now,fault;
static int ready,clock_set,budget;
static mf_ws_audio_diagnostic diagnostic;
static mf_ws_audio_progress progress;
static const char *const operation[]={"IDLE","MAP READ","SOUND OFF","SND INIT",
    "MAP CHANGE","SGL INIT","SEQ UPLOAD","TON UPLOAD","CPU RESTART",
    "FLUSH/HANDSHAKE","DSP STOP","CDDA LEVEL","TOTAL VOLUME"};
static void stage(unsigned n)
{
    diagnostic.stage=n;diagnostic.operation=operation[n];
    diagnostic.has_status=0;diagnostic.expected=diagnostic.actual=0;
    if(progress)progress(&diagnostic);
}
static void completed(void){diagnostic.completed|=1u<<(diagnostic.stage-1);}
static int result(int status)
{
    diagnostic.has_status=1;diagnostic.expected=SND_RET_SET;diagnostic.actual=status;
    if(status!=SND_RET_SET)return 0;
    completed();return 1;
}
const mf_ws_audio_diagnostic *mf_ws_audio_diagnostics(void){return &diagnostic;}
static int upload(mf_ws_audio_reader read,const char *name,int expected,unsigned addr)
{
    char *p=read(name,expected);
    if(!p){diagnostic.has_status=1;diagnostic.expected=expected;diagnostic.actual=-1;return 0;}
    if(addr+(unsigned)expected>0x80000){
        diagnostic.has_status=1;diagnostic.expected=0x80000;diagnostic.actual=addr+expected;
        jo_free(p);return 0;
    }
    slDMACopy(p,MF_WS_SOUND_BASE+addr,expected);slDMAWait();jo_free(p);completed();return 1;
}
int mf_ws_audio_load(mf_ws_audio_reader read,mf_ws_audio_progress notify)
{
    char *map;SndIniDt init;
    /* Pinned SND_Init takes words and copies floor(bytes/4)*4+4. Supply its
       four-byte lookahead explicitly rather than reading past the MAP file. */
    unsigned int map_storage[(MF_WS_MAP_BYTES+4)/4]={0};
    ready=clock_set=0;pending_shots=pending_explosions=fault=0;
    memset(shot,0,sizeof(shot));memset(explosion,0,sizeof(explosion));memset(flame,0,sizeof(flame));
    memset(&diagnostic,0,sizeof(diagnostic));progress=notify;
    stage(MF_WS_AUDIO_MAP_READ);map=read("WDEATH.MAP",MF_WS_MAP_BYTES);
    if(!map){diagnostic.has_status=1;diagnostic.expected=MF_WS_MAP_BYTES;diagnostic.actual=-1;return 0;}
    memcpy(map_storage,map,MF_WS_MAP_BYTES);completed();
    stage(MF_WS_AUDIO_SOUND_OFF);slSoundOffWait();completed();
    SND_INI_PRG_ADR(init)=(Uint16 *)sddrvstsk;SND_INI_PRG_SZ(init)=MF_SOUND_DRIVER_BYTES;
    SND_INI_ARA_ADR(init)=(Uint16 *)map_storage;
    SND_INI_ARA_SZ(init)=MF_WS_MAP_BYTES/sizeof(Uint16); /* Binary-verified word count. */
    stage(MF_WS_AUDIO_SND_INIT);SND_Init(&init);completed();
    stage(MF_WS_AUDIO_MAP_CHANGE);
    if(!result(SND_ChgMap(0))){jo_free(map);return 0;}
    stage(MF_WS_AUDIO_SGL_INIT);
    slInitSound((Uint8 *)sddrvstsk,MF_SOUND_DRIVER_BYTES,(Uint8 *)map_storage,MF_WS_MAP_BYTES);
    slDMAWait();
    /* Same dry/silent DSP arena as the proven Level 1 initializer. */
    memset(MF_WS_SOUND_BASE+0xc000,0,0x1c580-0xc000);
    jo_free(map);completed();
    stage(MF_WS_AUDIO_SEQ_UPLOAD);if(!upload(read,"WDEATH.SEQ",MF_WS_SEQ_BYTES,MF_WS_SEQ_ADDR))return 0;
    stage(MF_WS_AUDIO_TON_UPLOAD);if(!upload(read,"WDEATH.TON",MF_WS_TON_BYTES,MF_WS_TON_ADDR))return 0;
    /* Follow src/music.c's working SND/SGL initialization pairing, restart,
       flush and SND-only command submission. No slSoundRequest return checks. */
    MF_WS_SOUND_BASE[0x4e1]=0;
    stage(MF_WS_AUDIO_CPU_RESTART);slSoundOnWait();completed();
    stage(MF_WS_AUDIO_FLUSH);slSndFlush();slDMAWait();completed();
    stage(MF_WS_AUDIO_DSP_STOP);if(!result(SND_StopDsp()))return 0;
    stage(MF_WS_AUDIO_CDDA_LEVEL);if(!result(SND_SetCdDaLev(0,0)))return 0;
    stage(MF_WS_AUDIO_TOTAL_VOLUME);if(!result(SND_SetTlVl(15)))return 0;
    ready=1;return 1;
}
void mf_ws_audio_events(int count,unsigned shots)
{
    if(!ready)return;
    if(count>0)pending_explosions+=(unsigned)count;
    pending_shots+=!!(shots&1u)+!!(shots&2u);
}
static int midi(int port,int command,int data1,int data2)
{
    if(!budget)return 0;
    if(SND_CtrlDirMidi(port,0,command,port,data1,data2)!=SND_RET_SET)return 0;
    --budget;return 1;
}
static void advance(one_shot *pool,int n,unsigned *pending,int first_port,int song,int volume,unsigned duration,unsigned now)
{
    int i;for(i=0;i<n;i++){
        one_shot *p=&pool[i];int port=first_port+i;
        if(p->state==PLAYING && (int)(now-p->until)>=0)p->state=FREE;
        if(p->state==RELEASE && now!=p->stopped)p->state=FREE;
        if(p->state==FREE && *pending){--*pending;p->state=VOLUME;}
        if(p->state==VOLUME && budget && SND_SetSeqVl(port,volume,0)==SND_RET_SET){--budget;p->state=START;}
        if(p->state==START && budget && SND_StartSeq(port,0,song,0)==SND_RET_SET){
            --budget;p->state=PLAYING;p->started=now;p->until=now+duration;
        }
        if(p->state==PLAYING){
            SndSeqStat status;SND_GetSeqStat(&status,port);
            if(status.stat && !fault)fault=((unsigned)port<<8)|status.stat;
        }
    }
}
void mf_ws_audio_step(unsigned now,unsigned focused)
{
    int i,oldest=-1;
    if(!ready || (clock_set && now==last_now))return;
    last_now=now;clock_set=1;budget=8;
    /* Stops take precedence and never affect a different player's control. */
    for(i=0;i<2;i++){
        flame_state *f=&flame[i];if(f->on && !(focused&(1u<<i)))f->stop=1;
        if(f->stop && midi(i,0,60,0)){
            f->on=f->stop=0;f->guard=1;f->stopped=now;
        }
    }
    for(i=0;i<2;i++){
        flame_state *f=&flame[i];int result=0;
        /* Configure over distinct title VBlanks: volume, bank, program. A
           focus edge then needs only NOTE ON; no finite gate or re-ignition. */
        if(f->prep<3){
            if(!f->prep && budget && SND_SetSeqVl(i,MF_WS_FLAME_VOLUME,0)==SND_RET_SET){--budget;result=1;}
            else if(f->prep==1)result=midi(i,3,32,0);
            else if(f->prep==2)result=midi(i,4,2,0);
            if(result)++f->prep;
            continue;
        }
        if(f->guard && now!=f->stopped)f->guard=0;
        if((focused&(1u<<i)) && !f->on && !f->guard && !f->stop && midi(i,1,60,110))f->on=1;
    }
    advance(explosion,4,&pending_explosions,4,0,MF_SFX_VOLUME,MF_WS_EXP_TICKS,now);
    advance(shot,2,&pending_shots,2,1,MF_WS_SHOT_VOLUME,MF_WS_SHOT_TICKS,now);
    /* Steal the oldest SHOT only. The requested new event stays queued until
       stop acknowledgement and a real VBlank release guard have elapsed. */
    if(pending_shots){
        int waiting=0;
        for(i=0;i<2;i++){
            if(shot[i].state!=PLAYING)waiting=1;
            else if(oldest<0 || (unsigned)(now-shot[i].started)>(unsigned)(now-shot[oldest].started))oldest=i;
        }
        if(!waiting && oldest>=0 && budget && SND_StopSeq(oldest+2)==SND_RET_SET){
            --budget;shot[oldest].state=RELEASE;shot[oldest].stopped=now;
        }
    }
}
unsigned mf_ws_audio_fault(void){return fault;}
