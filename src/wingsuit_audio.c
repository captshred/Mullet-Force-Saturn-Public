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
static int upload(mf_ws_audio_reader read,const char *name,int expected,unsigned addr)
{
    char *p=read(name,expected);if(!p)return 0;
    if(addr+(unsigned)expected>0x80000){jo_free(p);return 0;}
    slDMACopy(p,MF_WS_SOUND_BASE+addr,expected);slDMAWait();jo_free(p);return 1;
}
int mf_ws_audio_load(mf_ws_audio_reader read)
{
    int ok;char *map;SndIniDt init;
    ready=clock_set=0;pending_shots=pending_explosions=fault=0;
    memset(shot,0,sizeof(shot));memset(explosion,0,sizeof(explosion));memset(flame,0,sizeof(flame));
    map=read("WDEATH.MAP",MF_WS_MAP_BYTES);if(!map)return 0;
    slSoundOffWait();
    SND_INI_PRG_ADR(init)=(Uint16 *)sddrvstsk;SND_INI_PRG_SZ(init)=MF_SOUND_DRIVER_BYTES;
    SND_INI_ARA_ADR(init)=(Uint16 *)map;SND_INI_ARA_SZ(init)=MF_WS_MAP_BYTES/2; /* SDK uses words. */
    SND_Init(&init); /* Initialize read-only status pointers before SGL owns transport. */
    slInitSound((Uint8 *)sddrvstsk,MF_SOUND_DRIVER_BYTES,(Uint8 *)map,MF_WS_MAP_BYTES);slDMAWait();jo_free(map);
    ok=upload(read,"WDEATH.SEQ",MF_WS_SEQ_BYTES,MF_WS_SEQ_ADDR);
    ok=upload(read,"WDEATH.TON",MF_WS_TON_BYTES,MF_WS_TON_ADDR)&&ok;
    if(!ok)return 0;
    /* slInitSound enables the driver's latched timing handshake. Leave it
       intact and use SGL's queue exclusively, including initialization. */
    slSoundOnWait();
    if(slSoundRequest("b",SND_MAP_CHG,0) || slSoundRequest("",SND_DSP_STOP) ||
       slSoundRequest("bb",SND_CDDA_LEV,0,0) || slSoundRequest("b",SND_TTL_VOL,15))return 0;
    slSndFlush();slDMAWait();
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
    if(slSoundRequest("bbbb",SND_MIDI_CTRL_DIR,command,(port<<5)|port,data1,data2)!=0)return 0;
    --budget;return 1;
}
static void advance(one_shot *pool,int n,unsigned *pending,int first_port,int song,int volume,unsigned duration,unsigned now)
{
    int i;for(i=0;i<n;i++){
        one_shot *p=&pool[i];int port=first_port+i;
        if(p->state==PLAYING && (int)(now-p->until)>=0)p->state=FREE;
        if(p->state==RELEASE && now!=p->stopped)p->state=FREE;
        if(p->state==FREE && *pending){--*pending;p->state=VOLUME;}
        if(p->state==VOLUME && budget && slSoundRequest("bbb",SND_SEQ_VOL,port,volume,0)==0){--budget;p->state=START;}
        if(p->state==START && budget && slSoundRequest("bbbb",SND_SEQ_START,port,0,song,0)==0){
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
            if(!f->prep && budget && slSoundRequest("bbb",SND_SEQ_VOL,i,MF_WS_FLAME_VOLUME,0)==0){--budget;result=1;}
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
        if(!waiting && oldest>=0 && budget && slSoundRequest("b",SND_SEQ_STOP,oldest+2)==0){
            --budget;shot[oldest].state=RELEASE;shot[oldest].stopped=now;
        }
    }
    if(budget<8)slSndFlush(); /* SDK owns the timing handshake and command DMA. */
}
unsigned mf_ws_audio_fault(void){return fault;}
