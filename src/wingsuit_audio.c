#include <jo/jo.h>
#include <SEGA_SND.H>
#include <string.h>
#include "music_data.h"
#include "wingsuit_audio_data.h"
#include "wingsuit_audio.h"
#ifndef MF_WS_SOUND_BASE
#define MF_WS_SOUND_BASE ((unsigned char *)0x25a00000)
#endif
#ifndef MF_WS_SLOT_REGS
#define MF_WS_SLOT_REGS ((volatile unsigned short *)0x25b00000)
#endif
extern char sddrvstsk[];
/* Pinned driver 2.10: eight control numbers 0..7, 32 physical SCSP slots.
   Two persistent flames, two shot controls, four explosion controls. */
enum { FREE,VOLUME,START,PLAYING,RELEASE };
typedef struct { unsigned started,until,stopped;int state; } one_shot;
typedef struct { unsigned stopped,started,loop_started,missing_since;int prep,attack,loop,program,guard,stop,missing; } flame_state;
static one_shot shot[2],explosion[4];
static flame_state flame[2];
static mf_ws_flame_diagnostic flame_diagnostic[2];
static unsigned pending_shots,pending_explosions,last_now,fault;
static int ready,clock_set,budget,startup_done,startup_failed,boot_clock;
static unsigned boot,boot_since,boot_counter;
enum { BOOT_CPU=1,BOOT_MAP,BOOT_MAP_ACK,BOOT_DSP,BOOT_DSP_ACK,
       BOOT_CDDA,BOOT_CDDA_ACK,BOOT_VOLUME,BOOT_VOLUME_ACK };
static mf_ws_audio_diagnostic diagnostic;
static mf_ws_audio_progress progress;
static const char *const operation[]={"IDLE","MAP READ","SOUND OFF","SND INIT",
    "MAP CHANGE","SGL INIT","SEQ UPLOAD","TON UPLOAD","CPU RESTART",
    "FLUSH/HANDSHAKE","DSP STOP","CDDA LEVEL","TOTAL VOLUME",
    "DRIVER READY","MAP READY","FLAME READY"};
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
static unsigned sound_word(unsigned addr)
{
    volatile unsigned char *p=MF_WS_SOUND_BASE+addr;
    return ((unsigned)p[0]<<8)|p[1];
}
static unsigned sound_pointer(unsigned addr)
{return (sound_word(addr)<<16)|sound_word(addr+2);}
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
    ready=clock_set=startup_done=startup_failed=boot_clock=0;boot=0;pending_shots=pending_explosions=fault=0;
    memset(shot,0,sizeof(shot));memset(explosion,0,sizeof(explosion));memset(flame,0,sizeof(flame));
    memset(flame_diagnostic,0,sizeof(flame_diagnostic));
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
    /* Submission success is not driver consumption. Finish a bounded, live
       readiness handshake during existing title VBlanks before accepting play. */
    boot_counter=sound_word(0x8838);boot=BOOT_CPU;return 1;
}
void mf_ws_audio_events(int count,unsigned shots)
{
    if(!startup_done)return;
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
/* Read-only diagnostics for pinned driver 2.10. Its timer caches SCSP EG
   activity in slot work at 0x8000 + 0x40*slot, word 0x3a (mask 6).
   Do not select/read the shared SCSP monitor: that would race its 68K owner. */
static void observe_flame(unsigned player,unsigned now,unsigned focused)
{
    flame_state *f=&flame[player];mf_ws_flame_diagnostic *d=&flame_diagnostic[player];
    unsigned slot,found=0,active=0,looping=!!f->loop;
    unsigned layer=looping?MF_WS_FLAME_LOOP_LAYER_ADDR:MF_WS_FLAME_ATTACK_LAYER_ADDR;
    unsigned pcm=looping?MF_WS_FLAME_LOOP_PCM_ADDR:MF_WS_FLAME_ATTACK_PCM_ADDR;
    unsigned frames=looping?MF_WS_FLAME_LOOP_FRAMES:MF_WS_FLAME_ATTACK_FRAMES;
    unsigned note=looping?MF_WS_FLAME_LOOP_NOTE:MF_WS_FLAME_ATTACK_NOTE;
    unsigned age=now-(looping?f->loop_started:f->started);
    memset(d,0,sizeof(*d));d->requested=!!(focused&(1u<<player));
    if(!f->attack && !f->loop){d->state=d->requested?MF_WS_FLAME_REQUESTED:MF_WS_FLAME_OFF;return;}
    d->age=now-f->started;
    for(slot=0;slot<32;slot++){
        unsigned addr=0x8000+slot*0x40,owner=sound_word(addr+6),eg=sound_word(addr+0x3a);
        volatile unsigned short *reg=MF_WS_SLOT_REGS+slot*16;
        unsigned control,sa,lsa,lea;
        if(owner!=(player<<9) || sound_word(addr+2)!=((player<<8)|note) || sound_pointer(addr+8)!=layer)continue;
        control=reg[0];sa=((control&15)<<16)|reg[1];lsa=reg[2];lea=reg[3];
        if(owner!=sound_word(addr+6) || eg!=sound_word(addr+0x3a))continue;
        found|=1u<<slot;if(eg&6)active|=1u<<slot;
        if(!d->slots || (eg&6)){
            d->control=control;d->sa=sa;d->lsa=lsa;d->lea=lea;d->eg=eg;
            d->state=(sa!=pcm || (control&0x790) || ((control>>5)&3)!=looping || lsa || lea!=frames)?MF_WS_FLAME_MISMATCH:0;
        }
        d->slots=found;
    }
    d->active_slots=active;
    if(!d->requested){d->state=MF_WS_FLAME_RELEASING;return;}
    if(active){
        f->missing=0;
        if(age<12)d->state=MF_WS_FLAME_REQUESTED;
        else if(d->state!=MF_WS_FLAME_MISMATCH)d->state=looping?MF_WS_FLAME_SUSTAIN:MF_WS_FLAME_ATTACK;
    }else{
        if(!f->missing){f->missing=1;f->missing_since=now;}
        if(now-f->missing_since>=12 && age>=12)d->state=MF_WS_FLAME_STOPPED;
        else if(d->state!=MF_WS_FLAME_MISMATCH)d->state=MF_WS_FLAME_REQUESTED;
    }
}
const mf_ws_flame_diagnostic *mf_ws_audio_flame_diagnostics(unsigned player)
{return player<2?&flame_diagnostic[player]:0;}
/* Pinned 2.10 timer increments word 0x8838; its eight 16-byte request
   blocks at 0x700 are cleared by the command consumer, not by SND submission. */
static int commands_empty(void)
{
    unsigned i;volatile unsigned char *sound_ram=MF_WS_SOUND_BASE;
    for(i=0;i<8;i++)if(sound_ram[0x700+i*16])return 0;
    return 1;
}
static int map_ready(void)
{
    unsigned i;volatile unsigned char *sound_ram=MF_WS_SOUND_BASE;
    for(i=16;i<32;i++)if(sound_ram[0x500+i]!=sound_ram[0xa000+i])return 0;
    return 1;
}
static void pending(const char *name)
{
    diagnostic.operation=name;diagnostic.has_status=0;diagnostic.expected=0;diagnostic.actual=0;
}
static void startup_timeout(void)
{
    unsigned i,queued=0;volatile unsigned char *sound_ram=MF_WS_SOUND_BASE;
    if(diagnostic.has_status && diagnostic.actual!=SND_RET_SET){startup_failed=1;return;}
    diagnostic.has_status=1;diagnostic.expected=1;diagnostic.actual=0;
    for(i=0;boot!=BOOT_CPU && i<8;i++)if(sound_ram[0x700+i*16]){
        queued=sound_ram[0x700+i*16];diagnostic.expected=0;diagnostic.actual=queued;break;
    }
    if((boot==BOOT_MAP_ACK || boot==BOOT_VOLUME_ACK) && commands_empty() && !map_ready()){
        for(i=16;i<32;i++)if(sound_ram[0x500+i]!=sound_ram[0xa000+i]){
            diagnostic.operation="MAP BYTE";diagnostic.expected=sound_ram[0xa000+i];diagnostic.actual=sound_ram[0x500+i];break;
        }
    }
    if(!boot){
        if(queued)diagnostic.operation="FLAME ACK";
        else {diagnostic.operation="FLAME READY";diagnostic.expected=3;diagnostic.actual=flame[0].prep<flame[1].prep?flame[0].prep:flame[1].prep;}
    }
    startup_failed=1;
}
static void startup(unsigned now)
{
    if(!boot_clock){boot_clock=1;boot_since=now;stage(MF_WS_AUDIO_DRIVER_READY);}
    if(now-boot_since>=120){
        startup_timeout();return;
    }
    switch(boot){
    case BOOT_CPU:
        if(sound_word(0x8838)==boot_counter || !commands_empty())return;
        completed();stage(MF_WS_AUDIO_MAP_READY);boot=BOOT_MAP;break;
    case BOOT_MAP:{
        int status=SND_ChgMap(0);
        diagnostic.has_status=1;diagnostic.expected=SND_RET_SET;diagnostic.actual=status;
        if(status==SND_RET_SET){pending("MAP ACK");boot=BOOT_MAP_ACK;}break;
    }
    case BOOT_MAP_ACK:
        if(!commands_empty() || !map_ready())return;
        completed();stage(MF_WS_AUDIO_DSP_STOP);boot=BOOT_DSP;break;
    case BOOT_DSP:
        if(result(SND_StopDsp())){pending("DSP ACK");boot=BOOT_DSP_ACK;}break;
    case BOOT_DSP_ACK:
        if(!commands_empty())return;
        stage(MF_WS_AUDIO_CDDA_LEVEL);boot=BOOT_CDDA;break;
    case BOOT_CDDA:
        if(result(SND_SetCdDaLev(0,0))){pending("CDDA ACK");boot=BOOT_CDDA_ACK;}break;
    case BOOT_CDDA_ACK:
        if(!commands_empty())return;
        stage(MF_WS_AUDIO_TOTAL_VOLUME);boot=BOOT_VOLUME;break;
    case BOOT_VOLUME:
        if(result(SND_SetTlVl(15))){pending("VOLUME ACK");boot=BOOT_VOLUME_ACK;}break;
    case BOOT_VOLUME_ACK:
        if(!commands_empty() || !map_ready())return;
        ready=1;boot=0;stage(MF_WS_AUDIO_FLAME_READY);break;
    default:break;
    }
}
int mf_ws_audio_ready(void){return startup_failed?-1:startup_done;}
void mf_ws_audio_step(unsigned now,unsigned focused)
{
    int i,oldest=-1;
    if((!ready && !boot) || startup_failed || (clock_set && now==last_now))return;
    last_now=now;clock_set=1;budget=8;
    if(boot){startup(now);return;}
    if(!startup_done && boot_clock && now-boot_since>=120){startup_timeout();return;}
    /* Release is latched across SDK rejection; stop only this player's keys.
       Loop Note Off takes priority over the already finite Attack tone. */
    for(i=0;i<2;i++){
        flame_state *f=&flame[i];
        if((f->attack || f->loop) && !(focused&(1u<<i)))f->stop=1;
        if(f->stop){
            if(f->loop && midi(i,0,MF_WS_FLAME_LOOP_NOTE,0))f->loop=0;
            if(f->attack && midi(i,0,MF_WS_FLAME_ATTACK_NOTE,0))f->attack=0;
            if(!f->attack && !f->loop){f->stop=0;f->guard=1;f->stopped=now;f->prep=2;f->program=0;}
        }
    }
    for(i=0;i<2;i++){
        flame_state *f=&flame[i];int accepted=0;
        if(f->prep<3){
            /* During startup every setup batch must actually drain. */
            if(!startup_done && !commands_empty())continue;
            if(!f->prep && budget && SND_SetSeqVl(i,MF_WS_FLAME_VOLUME,0)==SND_RET_SET){--budget;accepted=1;}
            else if(f->prep==1)accepted=midi(i,3,32,0);
            else if(f->prep==2)accepted=midi(i,4,MF_WS_FLAME_ATTACK_PROGRAM,0);
            if(accepted)++f->prep;
            continue;
        }
        if(f->guard && now!=f->stopped)f->guard=0;
        if(f->stop)continue;
        if((focused&(1u<<i)) && !f->attack && !f->loop && !f->guard &&
           midi(i,1,MF_WS_FLAME_ATTACK_NOTE,110)){
            f->attack=1;f->started=now;f->program=0;f->missing=0;
        }
        /* Program Change does not retune/replace the already sounding note. */
        if(f->attack && !f->program && now!=f->started && midi(i,4,MF_WS_FLAME_LOOP_PROGRAM,0))f->program=1;
        if(f->attack && f->program && !f->loop && now-f->started>=MF_WS_FLAME_HANDOFF_TICKS &&
           midi(i,1,MF_WS_FLAME_LOOP_NOTE,110)){
            f->loop=1;f->loop_started=now;f->missing=0;
        }
        /* The attack ends naturally ~1.02ms after the 38-tick Loop start.
           Retire its held key on the next real VBlank, preserving the overlap. */
        if(f->attack && f->loop && now!=f->loop_started && midi(i,0,MF_WS_FLAME_ATTACK_NOTE,0))f->attack=0;
    }
    if(!startup_done && flame[0].prep==3 && flame[1].prep==3 && commands_empty()){
        startup_done=1;completed();
    }
    advance(explosion,4,&pending_explosions,4,0,MF_SFX_VOLUME,MF_WS_EXP_TICKS,now);
    advance(shot,2,&pending_shots,2,1,MF_WS_SHOT_VOLUME,MF_WS_SHOT_TICKS,now);
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
    for(i=0;i<2;i++)observe_flame((unsigned)i,now,focused);
}
unsigned mf_ws_audio_fault(void){return fault;}
