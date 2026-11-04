/* Native SEQ/TON playback through the pinned Sega sound driver, not an SH-2 synth. */
#include <jo/jo.h>
#include <SEGA_SND.H>
#include "music.h"
#include "music_data.h"
#include "game.h"

extern char sddrvstsk[]; /* Existing Jo Engine driver 2.10; no second/new driver. */
static int ready,playing,paused_state,pause_target=-1;
static unsigned int pause_mask;
static unsigned char sfx_wait[3];
static int torch_playing;
static unsigned int audio_tick,hiss_stopped_at;
static int hiss_guard;
typedef struct { int playing,pending,stopping; unsigned int stopped_at,ends_at; unsigned char hit_wait; } combat_sound;
static const unsigned char custom_ticks[8]=MF_CUSTOM_SFX_TICKS;
static combat_sound combat[3]={{0,-1,0,0,0,0},{0,-1,0,0,0,0},{0,-1,0,0,0,0}};
static const unsigned char retrigger_ticks[3]=MF_SFX_RETRIGGER_TICKS;

static int upload(const char *name,unsigned int expected,unsigned int address)
{
    int bytes=0;
    char *data=jo_fs_read_file(name,&bytes);
    if(!data) return 0;
    if(bytes!=(int)expected || (bytes&3) || (address&3) || address+bytes>0x80000) {
        jo_free(data); return 0;
    }
    slDMACopy(data,(void *)((volatile unsigned char *)0x25a00000+address),bytes);
    slDMAWait(); /* Source stays live until the asynchronous DMA completes. */
    jo_free(data);
    return 1;
}
int mf_music_init(void)
{
    int size=0,ok;
    char *map=jo_fs_read_file("CUSTOM.MAP",&size);
    SndIniDt init;
    volatile unsigned int *p;
    if(!map || size!=MF_CUSTOM_MAP_BYTES) { if(map) jo_free(map); return 0; }
    /* Same SND_Init + slInitSound pairing as the compatible SRL SEQ sample.
       Driver/work 0..B000 and standard DSP/transfer reservations stay intact. */
    slSoundOffWait();
    SND_INI_PRG_ADR(init)=(Uint16 *)sddrvstsk;
    SND_INI_PRG_SZ(init)=MF_SOUND_DRIVER_BYTES;
    SND_INI_ARA_ADR(init)=(Uint16 *)map;
    SND_INI_ARA_SZ(init)=size;
    SND_Init(&init);
    SND_ChgMap(0);
    slInitSound((Uint8 *)sddrvstsk,MF_SOUND_DRIVER_BYTES,(Uint8 *)map,size);
    slDMAWait();
    /* Defined, silent DSP memory; this project uses only dry PCM voices. */
    for(p=(volatile unsigned int *)0x25a0c000;p<(volatile unsigned int *)0x25a1c580;++p) *p=0;
    jo_free(map);
    ok=upload("FX.SEQ",MF_FX_SEQ_BYTES,MF_FX_SEQ_ADDR);
    ok=upload("FX.TON",MF_FX_TON_BYTES,MF_FX_TON_ADDR)&&ok;
    ok=upload("STAGE.SEQ",MF_STAGE_SEQ_BYTES,MF_STAGE_SEQ_ADDR)&&ok;
    ok=upload("STAGE.TON",MF_STAGE_TON_BYTES,MF_STAGE_TON_ADDR)&&ok;
    *(volatile unsigned char *)0x25a004e1=0;
    slSoundOnWait();
    slSndFlush();
    slDMAWait();
    /* Use the SDK SND command interface exclusively after initialization. */
    SND_StopDsp();
    SND_SetCdDaLev(0,0);
    SND_SetTlVl(15);
    ready=ok;
    return ready;
}
int mf_music_ready(void) { return ready; }

/* Combat ports 5/6 and world destruction port 3. A confirmed collision wins over
   initiation in the same tick. Stop -> one real VBlank for RR31 -> replacement.
   The guard uses the hardware VBlank clock, not catch-up simulation steps. */
static int combat_port(int actor) {return actor==2?3:5+actor;}
static void combat_update(int player,int events,unsigned int now,unsigned int elapsed)
{
    combat_sound *c=&combat[player];int port=combat_port(player),song=-1;
    if(c->playing && (int)(now-c->ends_at)>=0)c->playing=0;
    c->hit_wait=elapsed>=c->hit_wait?0:c->hit_wait-elapsed;
    if(events&(MF_COMBAT_JAB(player)|MF_COMBAT_BAT(player)|MF_COMBAT_HURT(player)))c->hit_wait=0;
    if(player==2 && (events&MF_WORLD_IMPACT)) {
        song=2;
    }else if(events&MF_COMBAT_CONNECT(player)) {
        song=6;c->hit_wait=4; /* Lethal results always take precedence. */
    }else if((events&MF_COMBAT_NONKILL(player)) && !c->hit_wait) {
        song=0;c->hit_wait=4;
    }else if(events&MF_COMBAT_BAT(player))song=7;
    else if(events&MF_COMBAT_JAB(player))song=5;
    if(player<2 && song<0 && (events&MF_COMBAT_DESTROY(player))) {
        c->pending=-1;if(c->playing)c->stopping=1;
    }
    if(song>=0) {
        c->pending=song;
        if(c->playing && !c->stopping)c->stopping=1;
    }
    if(c->stopping==1) {
        if(SND_StopSeq(port)!=SND_RET_SET)return;
        c->playing=0;c->stopping=2;c->stopped_at=now;
        return;
    }
    if(c->stopping==2) {
        if(now==c->stopped_at)return;
        c->stopping=0;
    }
    if(c->pending>=0 && SND_SetSeqVl(port,MF_SFX_VOLUME,0)==SND_RET_SET &&
       SND_StartSeq(port,0,c->pending,MF_SFX_PRIORITY)==SND_RET_SET) {
        c->ends_at=now+custom_ticks[c->pending];c->playing=1;c->pending=-1;
    }
}
void mf_music_update(int started,int paused,int events,unsigned int now)
{
    int i;unsigned int elapsed=now-audio_tick;audio_tick=now;
    if(!ready)return;
    if(paused || paused_state)for(i=0;i<3;i++)if(combat[i].playing)combat[i].ends_at+=elapsed;
    if(torch_playing && (!started || paused || !(events&MF_TORCH_HISS))) {
        if(SND_StopSeq(4)==SND_RET_SET){torch_playing=0;hiss_guard=1;hiss_stopped_at=now;}
    }
    if(!started) {
        for(i=0;i<3;i++) {
            combat[i].pending=-1;
            if(combat[i].playing && SND_StopSeq(combat_port(i))==SND_RET_SET)combat[i].playing=0;
        }
        return;
    }
    if(!playing) {
        if(SND_SetSeqVl(0,MF_MUSIC_VOLUME,0)!=SND_RET_SET)return;
        if(SND_StartSeq(0,1,0,MF_MUSIC_PRIORITY)!=SND_RET_SET)return;
        playing=1;
    }
    /* Hiss is stopped above. Pause/resume owns all other fixed ports 0..6. */
    if(paused!=paused_state || pause_target>=0) {
        if(pause_target!=paused){pause_target=paused;pause_mask=0;}
        for(i=0;i<7;i++)if(i!=4 && !(pause_mask&(1u<<i))) {
            if((paused?SND_PauseSeq(i):SND_ContSeq(i))==SND_RET_SET)pause_mask|=1u<<i;
        }
        if(pause_mask!=0x6f)return;
        paused_state=paused;pause_mask=0;pause_target=-1;
        /* A collision awaiting a replacement must not become a stale hit on resume. */
        if(paused)for(i=0;i<3;i++)combat[i].pending=-1;
    }
    if(paused)return;
    for(i=0;i<3;i++)sfx_wait[i]=elapsed>=sfx_wait[i]?0:sfx_wait[i]-elapsed;
    /* Shared ignition/hiss and original jump retain their sounds.
       No ignition cooldown bypass: at most one retirement tail per legacy port. */
    if(hiss_guard && now-hiss_stopped_at>=3)hiss_guard=0;
    if((events&MF_TORCH_HISS) && !torch_playing && !hiss_guard) {
        if(SND_SetSeqVl(4,MF_SFX_VOLUME,0)==SND_RET_SET &&
           SND_StartSeq(4,0,4,MF_SFX_PRIORITY)==SND_RET_SET)torch_playing=1;
    }
    for(i=0;i<2;i++)if(((i==0 && (events&MF_TORCH_IGNITE)) ||
       (i==1 && (events&MF_JUMP_SOUND))) && !sfx_wait[i]) {
        int port=i+1;
        if(SND_StopSeq(port)!=SND_RET_SET)continue;
        if(SND_SetSeqVl(port,MF_SFX_VOLUME,0)!=SND_RET_SET)continue;
        if(SND_StartSeq(port,0,i==0?3:i,MF_SFX_PRIORITY)==SND_RET_SET)sfx_wait[i]=retrigger_ticks[i];
    }
    for(i=0;i<3;i++)combat_update(i,i==2?(int)(events&MF_WORLD_IMPACT):events,now,elapsed);
}
