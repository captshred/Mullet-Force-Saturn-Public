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
enum { FREE,PLAYING,RESTARTING };
typedef struct { unsigned started,until;int state; } one_shot;
typedef struct { unsigned stopped,started,loop_started,missing_since;int prep,attack,loop,program,guard,stop,missing; } flame_state;
static one_shot shot[2],explosion[4];
static unsigned shot_next,explosion_next;
static one_shot hit;
static unsigned hit_prep,pending_hits;
static flame_state flame[2];
static mf_ws_flame_diagnostic flame_diagnostic[2];
static unsigned pending_shots,pending_explosions,last_now,fault,note_on_mask;
static unsigned one_prep[6],note_baseline[8];
static mf_ws_mixer_diagnostic mixer;
typedef struct { unsigned owner,key,stamp,started,missing_since,other_on,free;int seen,missing; } slot_watch;
static slot_watch watch[32];
static int ready,clock_set,budget,startup_done,startup_failed,boot_clock;
static unsigned boot,boot_since,boot_counter,music_prep,music_requested,map_ack_bytes;
static mf_ws_audio_reader bank_reader;
enum { BOOT_CPU=1,BOOT_MAP,BOOT_MAP_ACK,BOOT_DSP,BOOT_DSP_ACK,
       BOOT_CDDA,BOOT_CDDA_ACK,BOOT_VOLUME,BOOT_VOLUME_ACK,
       BOOT_FIRE_UPLOAD,BOOT_FIRE_MAP,BOOT_FIRE_ACK };
static mf_ws_audio_diagnostic diagnostic;
static mf_ws_audio_progress progress;
static const char *const operation[]={"IDLE","MAP READ","SOUND OFF","SND INIT",
    "MAP CHANGE","SGL INIT","SEQ UPLOAD","TON UPLOAD","CPU RESTART",
    "FLUSH/HANDSHAKE","DSP STOP","CDDA LEVEL","TOTAL VOLUME",
    "DRIVER READY","MAP READY","SFX READY"};
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
    unsigned int map_storage[(MF_WS_MUSIC_MAP_BYTES+4)/4]={0};
    bank_reader=read;map_ack_bytes=MF_WS_MUSIC_MAP_BYTES;
    memset(&hit,0,sizeof(hit));hit_prep=pending_hits=0;music_prep=music_requested=0;ready=clock_set=startup_done=startup_failed=boot_clock=0;boot=0;pending_shots=pending_explosions=fault=0;
    memset(shot,0,sizeof(shot));memset(explosion,0,sizeof(explosion));memset(flame,0,sizeof(flame));
    memset(flame_diagnostic,0,sizeof(flame_diagnostic));
    memset(note_baseline,0,sizeof(note_baseline));memset(one_prep,0,sizeof(one_prep));memset(&mixer,0,sizeof(mixer));memset(watch,0,sizeof(watch));
    memset(&diagnostic,0,sizeof(diagnostic));progress=notify;
    stage(MF_WS_AUDIO_MAP_READ);map=read("WMUSIC.MAP",MF_WS_MUSIC_MAP_BYTES);
    if(!map){diagnostic.has_status=1;diagnostic.expected=MF_WS_MUSIC_MAP_BYTES;diagnostic.actual=-1;return 0;}
    memcpy(map_storage,map,MF_WS_MUSIC_MAP_BYTES);completed();
    stage(MF_WS_AUDIO_SOUND_OFF);slSoundOffWait();completed();
    SND_INI_PRG_ADR(init)=(Uint16 *)sddrvstsk;SND_INI_PRG_SZ(init)=MF_SOUND_DRIVER_BYTES;
    SND_INI_ARA_ADR(init)=(Uint16 *)map_storage;
    SND_INI_ARA_SZ(init)=MF_WS_MUSIC_MAP_BYTES/sizeof(Uint16); /* Binary-verified word count. */
    stage(MF_WS_AUDIO_SND_INIT);SND_Init(&init);completed();
    stage(MF_WS_AUDIO_MAP_CHANGE);
    if(!result(SND_ChgMap(0))){jo_free(map);return 0;}
    stage(MF_WS_AUDIO_SGL_INIT);
    slInitSound((Uint8 *)sddrvstsk,MF_SOUND_DRIVER_BYTES,(Uint8 *)map_storage,MF_WS_MUSIC_MAP_BYTES);
    slDMAWait();
    /* Same dry/silent DSP arena as the proven Level 1 initializer. */
    memset(MF_WS_SOUND_BASE+0xc000,0,0x1c580-0xc000);
    jo_free(map);completed();
    stage(MF_WS_AUDIO_SEQ_UPLOAD);if(!upload(read,"WDEATH.SEQ",MF_WS_SEQ_BYTES,MF_WS_SEQ_ADDR))return 0;
    stage(MF_WS_AUDIO_TON_UPLOAD);if(!upload(read,"WDEATH.TON",MF_WS_TON_BYTES,MF_WS_TON_ADDR))return 0;
    if(!upload(read,"WMUSIC.SEQ",MF_WS_MUSIC_SEQ_BYTES,MF_WS_MUSIC_SEQ_ADDR))return 0;
    if(!upload(read,"WMUSIC.TON",MF_WS_MUSIC_TON_BYTES,MF_WS_MUSIC_TON_ADDR))return 0;
    /* Follow src/music.c's working SND/SGL initialization pairing, restart,
       flush and SND-only command submission. No slSoundRequest return checks. */
    MF_WS_SOUND_BASE[0x4e1]=0;
    stage(MF_WS_AUDIO_CPU_RESTART);slSoundOnWait();completed();
    stage(MF_WS_AUDIO_FLUSH);slSndFlush();slDMAWait();completed();
    /* Pinned 2.10 dispatch at 0x1bd4..0x1be4 advances history cursor
       (exported word 0x041a) and RESETS interval timer 0x8838 per command.
       Capture before submission: commands may finish before load returns. */
    boot_counter=sound_word(0x41a);
    stage(MF_WS_AUDIO_DSP_STOP);if(!result(SND_StopDsp()))return 0;
    stage(MF_WS_AUDIO_CDDA_LEVEL);if(!result(SND_SetCdDaLev(0,0)))return 0;
    stage(MF_WS_AUDIO_TOTAL_VOLUME);if(!result(SND_SetTlVl(15)))return 0;
    /* Submission success is not driver consumption. Finish a bounded, live
       readiness handshake during existing title VBlanks before accepting play. */
    boot=BOOT_CPU;return 1;
}
/* Fixed capacities avoid room underflow as pending attacks occupy controls.
   Identical Explosion events need only a FIFO count; newest excess is dropped. */
static void enqueue(unsigned *pending,unsigned add,unsigned limit,unsigned *dropped)
{
    unsigned room=limit-*pending;
    if(add>room){*dropped+=add-room;*pending=limit;}
    else *pending+=add;
}
void mf_ws_audio_events(int count,unsigned shots)
{
    if(!startup_done)return;
    music_requested=1;
    if(count>0)enqueue(&pending_explosions,(unsigned)count,MF_WS_EXPLOSION_PENDING_MAX,&mixer.dropped_explosions);
    enqueue(&pending_shots,!!(shots&1u)+!!(shots&2u),4,&mixer.dropped_shots);
}
static int midi(int port,int command,int data1,int data2)
{
    unsigned counter=sound_word(0x67ec);
    if(!budget)return 0;
    /* Driver context = (control<<9)+(channel<<5). Music owns control 0;
       Flames use control 1/channel 0 or 1, one-shots controls/channels 2..7.
       Priority bits are discarded by the pinned direct-MIDI dispatcher. */
    if(SND_CtrlDirMidi(port<2?1:port,0,command,port,data1,data2)!=SND_RET_SET)return 0;
    if(command==1){note_on_mask|=1u<<port;note_baseline[port]=counter;}
    --budget;return 1;
}
/* All driver controls are assigned. Hit shares gain96 on control2 but has
   its own channel8 bank/program/key context; no control-wide stop is used. */
void mf_ws_audio_hits(unsigned count)
{
    if(startup_done){unsigned room=8-pending_hits;pending_hits+=count>room?room:count;}
}
static int hit_midi(int cmd,int a,int b)
{
    if(!budget || SND_CtrlDirMidi(2,0,cmd,8,a,b)!=SND_RET_SET)return 0;
    --budget;return 1;
}
static void advance_hit(unsigned now)
{
    if(hit.state==PLAYING && (int)(now-hit.until)>=0 && hit_midi(0,60,0))hit.state=FREE;
    /* At most one Hit attack per VBlank bounds release overlap; queued
       simultaneous impacts drain deterministically on following VBlanks. */
    if(pending_hits && budget){
        if(hit.state==PLAYING){if(!hit_midi(0,60,0))return;hit.state=RESTARTING;}
        if(!hit_midi(1,60,110))return;
        --pending_hits;hit.state=PLAYING;hit.started=now;hit.until=now+MF_WS_HIT_TICKS;
    }
}
static void advance_explosions(unsigned now)
{
    unsigned i;
    for(i=0;i<4;i++){
        one_shot *p=&explosion[i];
        /* Retire only after natural PCM completion, with the existing lease.
           Rejected retirement retains ownership and retries. */
        if(p->state==PLAYING && (int)(now-p->until)>=0 && midi(4+i,0,60,0))p->state=FREE;
        if(p->state==FREE && pending_explosions && (int)(now-explosion_next)>=0 && midi(4+i,1,60,110)){
            --pending_explosions;p->state=PLAYING;p->started=now;p->until=now+MF_WS_EXP_TICKS;
            explosion_next=now+MF_WS_EXPLOSION_MIN_SPACING;
        }
    }
}
static void advance_shots(unsigned now)
{
    unsigned i;
    for(i=0;i<2;i++)if(shot[i].state==PLAYING && (int)(now-shot[i].until)>=0 && midi(2+i,0,60,0))shot[i].state=FREE;
    while(pending_shots && budget){
        unsigned selected=shot_next;one_shot *p;
        /* Finish a previously accepted stop before selecting another voice. */
        for(i=0;i<2;i++)if(shot[i].state==RESTARTING){selected=i;break;}
        if(i==2){
            for(i=0;i<2;i++)if(shot[(shot_next+i)%2].state==FREE){selected=(shot_next+i)%2;break;}
            if(i==2 && now-shot[1-selected].started>now-shot[selected].started)selected=1-selected;
        }
        p=&shot[selected];
        if(p->state==PLAYING){
            if(!midi(2+selected,0,60,0))break;
            p->state=RESTARTING;
        }
        if(!midi(2+selected,1,60,110))break;
        --pending_shots;p->state=PLAYING;p->started=now;p->until=now+MF_WS_SHOT_TICKS;
        shot_next=1-selected;
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
        if(owner!=(1u<<9) || sound_word(addr+2)!=((player<<8)|note) || sound_pointer(addr+8)!=layer)continue;
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
/* Read only the driver's cached EG and ownership records, never its shared
   hardware monitor or private allocator flags. EG is sampled over ~9 VBlanks:
   these are observed cached-live slots, not a waveform/audibility measurement. */
static int expected_voice(unsigned owner,unsigned key,unsigned now,unsigned *started,unsigned *kind)
{
    unsigned p=owner>>9,note=key&255,age;
    if(owner!=(p<<9) || p>=8)return 0;
    if(p==1 && (key>>8)<2){
        p=key>>8;
        flame_state *f=&flame[p];*kind=MF_WS_SFX_FLAME;
        if(note==MF_WS_FLAME_LOOP_NOTE && f->loop){*started=f->loop_started;return 1;}
        if(note!=MF_WS_FLAME_ATTACK_NOTE || !f->attack)return 0;
        *started=f->started;return now-*started<37;
    }
    if(p<2 || (key>>8)!=p || note!=60)return 0;
    {one_shot *v=p<4?&shot[p-2]:&explosion[p-4];
     *kind=p<4?MF_WS_SFX_SHOT:MF_WS_SFX_EXPLOSION;*started=v->started;
     age=now-*started;
     /* Exclude the natural LEA boundary, independent of the longer reuse lease. */
     return v->state==PLAYING && age<(p<4?30u:43u);}
}
static void lost_voice(slot_watch *w,unsigned now,unsigned kind,int replaced)
{
    if(!mixer.losses){
        mixer.lost_kind=kind;mixer.lost_control=w->owner>>9;
        mixer.lost_age=(replaced?now:w->missing_since)-w->started;
        mixer.other_note_on=replaced?(note_on_mask&~(1u<<mixer.lost_control)):w->other_on;
        mixer.free_at_loss=replaced?mixer.free_slots:w->free;
        fault=(kind<<8)|mixer.lost_control;
    }
    ++mixer.losses;if(replaced)++mixer.replacements;
}
static void observe_mixer(unsigned now)
{
    unsigned s;
    mixer.flame=mixer.shot=mixer.explosion=mixer.total=mixer.free_slots=0;
    for(s=0;s<32;s++){
        unsigned a=0x8000+s*64,eg=sound_word(a+0x3a),owner=sound_word(a+6),key=sound_word(a+2);
        unsigned p=owner>>9,stamp=sound_word(a+0x3e),start=0,kind=0;
        slot_watch *w=&watch[s];
        mixer.owner[s]=255;
        if(!eg || !(eg&0xffcc))++mixer.free_slots;
        if(eg&6){
            ++mixer.total;
            if(p<8 && owner==(p<<9) && ((p==1 && (key>>8)<2) || (p>=2 && (key>>8)==p))){
                mixer.owner[s]=p;
                if(p==1)++mixer.flame;else if(p<4)++mixer.shot;else ++mixer.explosion;
            }
        }
        /* A concurrent 68K update is not evidence of voice loss. */
        if(eg!=sound_word(a+0x3a) || owner!=sound_word(a+6) || key!=sound_word(a+2) || stamp!=sound_word(a+0x3e))continue;
        if(w->seen){
            if(!expected_voice(w->owner,w->key,now,&start,&kind) || start!=w->started)w->seen=0;
            else if(owner!=w->owner || key!=w->key || stamp!=w->stamp){
                lost_voice(w,now,kind,1);w->seen=0;
            }else if(!(eg&6)){
                if(!w->missing){w->missing=1;w->missing_since=now;w->other_on=note_on_mask&~(1u<<(w->owner>>9));}
                if(now-w->missing_since>=12){lost_voice(w,now,kind,0);w->seen=0;}
            }else w->missing=0;
        }
        /* Submission precedes 68K consumption. An old cached-live ended key
           must not be attributed to a newly leased control. Native Note On
           increments 0x67ec before assigning its timestamp at slot+0x3e. */
        if(!w->seen && (eg&6) && p<8 && (short)(stamp-note_baseline[p==1 && (key>>8)<2?(key>>8):p])>0 &&
           expected_voice(owner,key,now,&start,&kind)){
            w->owner=owner;w->key=key;w->stamp=stamp;w->started=start;w->seen=1;w->missing=0;
        }
    }
    /* Loss snapshots use a complete count, independent of slot scan order. */
    if(mixer.losses && !mixer.snapshot){
        if(mixer.replacements)mixer.free_at_loss=mixer.free_slots;
        mixer.snapshot=1;
    }
    for(s=0;s<32;s++)if(watch[s].missing && watch[s].missing_since==now)watch[s].free=mixer.free_slots;
}
const mf_ws_mixer_diagnostic *mf_ws_audio_mixer_diagnostics(void){return &mixer;}
/* Pinned 2.10 exports consumed-command cursor at 0x041a; its eight 16-byte request
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
    for(i=16;i<map_ack_bytes-8;i++)if(sound_ram[0x500+i]!=sound_ram[0xa000+i])return 0;
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
    /* Include BOOT_CPU: report the first blocked command ID, not a
       misleading generic zero when requests remain unconsumed. */
    for(i=0;i<8;i++)if(sound_ram[0x700+i*16]){
        queued=sound_ram[0x700+i*16];diagnostic.expected=0;diagnostic.actual=queued;break;
    }
    if((boot==BOOT_MAP_ACK || boot==BOOT_VOLUME_ACK || boot==BOOT_FIRE_ACK) && commands_empty() && !map_ready()){
        for(i=16;i<map_ack_bytes-8;i++)if(sound_ram[0x500+i]!=sound_ram[0xa000+i]){
            diagnostic.operation="MAP BYTE";diagnostic.expected=sound_ram[0xa000+i];diagnostic.actual=sound_ram[0x500+i];break;
        }
    }
    if(!boot){
        if(queued)diagnostic.operation="SFX ACK";
        else {unsigned prep=flame[0].prep<flame[1].prep?flame[0].prep:flame[1].prep;
            for(i=0;i<6;i++)if(one_prep[i]<prep)prep=one_prep[i];
            diagnostic.operation="SFX READY";diagnostic.expected=3;diagnostic.actual=prep;}
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
        if(sound_word(0x41a)==boot_counter || !commands_empty())return;
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
        /* The owner-tested parent is fully acknowledged before any new
           bank is exposed to the running driver. */
        boot=BOOT_FIRE_UPLOAD;pending("FIRE UPLOAD");break;
    case BOOT_FIRE_UPLOAD:{
        char *map;
        if(!commands_empty())return;
        /* Upload tone FIRST. slInitSound internally starts the 68K and marks
           mapped areas transferred, so no uninitialized Fire mapping at boot. */
        if(!upload(bank_reader,"WFIRE.TON",MF_WS_FIRE_TON_BYTES,MF_WS_FIRE_TON_ADDR)){startup_failed=1;return;}
        map=bank_reader("WFIRE.MAP",MF_WS_FIRE_MAP_BYTES);
        if(!map){diagnostic.has_status=1;diagnostic.expected=MF_WS_FIRE_MAP_BYTES;diagnostic.actual=-1;startup_failed=1;return;}
        slDMACopy(map,MF_WS_SOUND_BASE+0xa000,MF_WS_FIRE_MAP_BYTES);slDMAWait();jo_free(map);
        map_ack_bytes=MF_WS_FIRE_MAP_BYTES;boot=BOOT_FIRE_MAP;pending("FIRE MAP");break;
    }
    case BOOT_FIRE_MAP:{
        int status;
        if(!commands_empty())return;
        boot_counter=sound_word(0x41a); /* Capture BEFORE synchronous consumption. */
        status=SND_ChgMap(0);
        diagnostic.has_status=1;diagnostic.expected=SND_RET_SET;diagnostic.actual=status;
        if(status==SND_RET_SET){boot=BOOT_FIRE_ACK;pending("FIRE MAP ACK");}break;
    }
    case BOOT_FIRE_ACK:
        if(sound_word(0x41a)==boot_counter || !commands_empty() || !map_ready())return;
        ready=1;boot=0;stage(MF_WS_AUDIO_FLAME_READY);break;
    default:break;
    }
}
int mf_ws_audio_ready(void){return startup_failed?-1:startup_done;}
void mf_ws_audio_step(unsigned now,unsigned focused)
{
    int i,all_prepared=1;
    if((!ready && !boot) || startup_failed || (clock_set && now==last_now))return;
    if(!clock_set){shot_next=0;explosion_next=now;}
    last_now=now;clock_set=1;budget=8;note_on_mask=0;
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
            if(!f->prep && budget && SND_SetSeqVl(1,MF_WS_FLAME_VOLUME,0)==SND_RET_SET){--budget;accepted=1;}
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
    /* SND_SetSeqVl is the driver's shared per-control gain command (also used
       by direct MIDI), configured ONCE before gameplay, never per one-shot. */
    if(!startup_done && commands_empty())for(i=0;i<6;i++){
        unsigned p=(unsigned)i+2;int accepted=0;
        if(!one_prep[i] && budget && SND_SetSeqVl(p,p<4?MF_WS_SHOT_VOLUME:100,0)==SND_RET_SET){--budget;accepted=1;}
        else if(one_prep[i]==1)accepted=midi(p,3,32,p<4?2:0);
        else if(one_prep[i]==2)accepted=midi(p,4,0,0);
        if(accepted)++one_prep[i];
    }
    if(!startup_done && commands_empty()){
        if(hit_prep==0 && hit_midi(3,32,0))hit_prep=1;
        else if(hit_prep==1 && hit_midi(4,1,0))hit_prep=2;
    }
    for(i=0;i<6;i++)if(one_prep[i]!=3)all_prepared=0;
    if(!startup_done && hit_prep==2 && all_prepared && flame[0].prep==3 && flame[1].prep==3 && commands_empty()){
        /* Preserve native score on control 0. SFX preparation must never
           attenuate its gain; Flames share control 1, separate MIDI channels. */
        if(music_prep==0 && budget && SND_SetSeqVl(0,127,0)==SND_RET_SET){--budget;music_prep=1;}
        else if(music_prep==1){startup_done=1;completed();}
    }
    if(startup_done){
        if(music_requested && music_prep==1 && budget && SND_StartSeq(0,1,0,0)==SND_RET_SET){--budget;music_prep=2;}
        advance_explosions(now);
        advance_shots(now);
        advance_hit(now);
    }
    observe_mixer(now);
    for(i=0;i<2;i++)observe_flame((unsigned)i,now,focused);
}
unsigned mf_ws_audio_fault(void){return fault;}
