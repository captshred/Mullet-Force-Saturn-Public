/* Native SEQ/TON playback through the pinned Sega sound driver, not an SH-2 synth. */
#include <jo/jo.h>
#include <SEGA_SND.H>
#include "game.h"
#include "music.h"
#include "music_data.h"
#if MF_BRUCE_RUNTIME && MF_VEHICLE_AMBUSH
#include "bruce_sfx_data.h"
#endif

extern char sddrvstsk[]; /* Existing Jo Engine driver 2.10; no second/new driver. */
static int ready,paused_state,pause_target=-1;
enum { MUSIC_IDLE, MUSIC_STREET, MUSIC_STOPPING, MUSIC_STARTING_BRUCE, MUSIC_BRUCE };
static int music_state;
static unsigned int pause_mask;
static unsigned char sfx_wait[3];
static int torch_playing;
static unsigned int audio_tick,hiss_stopped_at;
static int hiss_guard;
typedef struct { int playing,pending,stopping; unsigned int stopped_at,ends_at; unsigned char hit_wait; } combat_sound;
static const unsigned char custom_ticks[9]=MF_CUSTOM_SFX_TICKS;
static combat_sound combat[3]={{0,-1,0,0,0,0},{0,-1,0,0,0,0},{0,-1,0,0,0,0}};
static const unsigned char retrigger_ticks[3]=MF_SFX_RETRIGGER_TICKS;

/* Control7 is unused by Level1's existing effects. It is a logical sequencer
   control, not a permanently reserved SCSP slot. Never stop/pause/restart an active UGH. */
static int death_pending,death_prepared,death_active,death_seen,death_retiring;
static unsigned int death_started,death_stopped_at;
int mf_music_protected(void){return death_pending || death_active || death_retiring;}
static int death_update(int events,unsigned int now)
{
    int i;
    if(death_retiring && now!=death_stopped_at)death_retiring=0;
    if(death_active) {
        SndSeqStat status;
        SND_GetSeqStat(&status,7);
        if(SND_SEQ_STAT_MODE(status)!=SND_MD_STOP && !death_seen) {
            death_seen=1;death_started=now;
        }
        /* Ignore the initial STOP before the accepted start reaches the68K.
           The score extends past PCM LEA; the sample-derived floor also guards
           a stale/early status. No short timeout can release this protection. */
        if(death_seen && SND_SEQ_STAT_MODE(status)==SND_MD_STOP &&
           now-death_started>=MF_DEATH_MIN_TICKS && SND_StopSeq(7)==SND_RET_SET) {
            /* The sample has already finished. Retire only our cached control,
               then allow a real VBlank for the68K before reuse/stage teardown. */
            death_active=0;death_retiring=1;death_stopped_at=now;
        }
    }
    if(!mf_music_protected() && (events&(MF_COMBAT_HUMAN_DEATH(0)|MF_COMBAT_HUMAN_DEATH(1)))) {
        death_pending=1;death_prepared=0;
    }
    if(mf_music_protected())for(i=0;i<3;i++)combat[i].pending=-1;
    if(death_pending) {
        if(!death_prepared) {
            if(SND_SetSeqVl(7,MF_SFX_VOLUME,0)!=SND_RET_SET)return 1;
            death_prepared=1;
        }
        if(SND_StartSeq(7,0,8,MF_SFX_PRIORITY)==SND_RET_SET) {
            death_pending=0;death_active=1;death_seen=0;
        }
    }
    return mf_music_protected();
}


static int upload_data(char *data,int bytes,unsigned int expected,unsigned int address)
{
    if(!data) return 0;
    if(bytes!=(int)expected || (bytes&3) || (address&3) || address+bytes>0x80000) {
        jo_free(data); return 0;
    }
    slDMACopy(data,(void *)((volatile unsigned char *)0x25a00000+address),bytes);
    slDMAWait(); /* Source stays live until the asynchronous DMA completes. */
    jo_free(data);
    return 1;
}
static int upload(const char *name,unsigned int expected,unsigned int address)
{
    int bytes=0;
    char *data=jo_fs_read_file(name,&bytes);
    return upload_data(data,bytes,expected,address);
}
#if MF_VEHICLE_AMBUSH
enum {
    CAR_SOUND_PORT=3, CAR_SOUND_CHANNEL=15, CAR_TONE_BANK=2,
    CAR_TON_ADDR=MF_STAGE_TON_ADDR+MF_STAGE_TON_BYTES, CAR_TON_BYTES=MF_CAR_TON_BYTES, CAR_DRIVE_NOTE=61
};
static int car_sound_playing,car_sound_setup,car_sound_triggered;
#if MF_BRUCE_RUNTIME
static unsigned car_safe_at;
#endif

static void car_sound_update(int in_pass,int requested,int paused)
{
    /* Pause and temporary SFX priority changes can stop a clip, but only
       leaving the pass arms the next one-shot. */
    if(!in_pass && !paused)car_sound_triggered=0;
    if(!requested){
        car_sound_setup=0;
        if(car_sound_playing &&
           SND_CtrlDirMidi(CAR_SOUND_PORT,0,0,CAR_SOUND_CHANNEL,CAR_DRIVE_NOTE,0)==SND_RET_SET)
            car_sound_playing=0;
        return;
    }
    if(car_sound_triggered || car_sound_playing || combat[2].pending>=0 || combat[2].stopping ||
       (combat[2].playing && (int)(audio_tick-combat[2].ends_at)<0))return;
    if(car_sound_setup==0){
        if(SND_SetSeqVl(CAR_SOUND_PORT,80,0)==SND_RET_SET)car_sound_setup=1;
    }else if(car_sound_setup==1){
        if(SND_CtrlDirMidi(CAR_SOUND_PORT,0,3,CAR_SOUND_CHANNEL,32,CAR_TONE_BANK)==SND_RET_SET)
            car_sound_setup=2;
    }else if(car_sound_setup==2){
        if(SND_CtrlDirMidi(CAR_SOUND_PORT,0,4,CAR_SOUND_CHANNEL,3,0)==SND_RET_SET)
            car_sound_setup=3;
    }else if(SND_CtrlDirMidi(CAR_SOUND_PORT,0,1,CAR_SOUND_CHANNEL,CAR_DRIVE_NOTE,110)==SND_RET_SET){
        car_sound_triggered=car_sound_playing=1;
#if MF_BRUCE_RUNTIME
        car_safe_at=audio_tick+105; /* 18441 samples at 11025 Hz plus release. */
#endif
    }
}
#endif

#if MF_BRUCE_RUNTIME && MF_VEHICLE_AMBUSH
/* The pinned driver has eight playable SEQ controls. Bruce owns control 7
   during his encounter. The protected POOWAH dispatcher uses it on the street. */
enum { BRUCE_SFX_PORT=7, BRUCE_OVERLAP_PORT=3, BRUCE_SFX_BANK=2,
       BRUCE_SFX_SEQ_ADDR=CAR_TON_ADDR+MF_BRUCE_TON_BYTES };
enum { BRUCE_OVERLAP_IDLE, BRUCE_OVERLAP_STOP, BRUCE_OVERLAP_START, BRUCE_OVERLAP_PLAY };
static int bruce_overlap, bruce_overlap_seen, bruce_laugh_played;
static unsigned bruce_overlap_at;
/* Song IDs start at zero independently of the SCSP addresses. */
enum { BRUCE_JUMP_SONG, BRUCE_CHARGE_SONG, BRUCE_HURT_SONG, BRUCE_LAUGH_SONG, BRUCE_DEATH_CUE };
typedef char bruce_sfx_ram_bound[BRUCE_SFX_SEQ_ADDR+MF_BRUCE_SEQ_BYTES<=0x80000?1:-1];
static const unsigned char bruce_sfx_ticks[4]=MF_BRUCE_SFX_MIN_TICKS;
static const unsigned char bruce_cue_priority[]={3,2,0,1,4};
static int bruce_encounter, bruce_tone_owner, bruce_voice=-1, bruce_pending=-1, bruce_laugh_pending;
static int bruce_seen, bruce_stop_guard, bruce_audio_fault;
static unsigned bruce_voice_at, bruce_stopped_at, bruce_pending_at;

static int bruce_cd_upload(const char *name,unsigned size,unsigned address)
{
    int bytes=0;
    char *data=jo_fs_read_file_in_dir(name,"RICKY",&bytes);
    return upload_data(data,bytes,size,address);
}

static int bruce_sample_done(int port,int song,unsigned now,int *seen,unsigned *started)
{
    SndSeqStat status;
    int mode;
    SND_GetSeqStat(&status,port);
    mode=SND_SEQ_STAT_MODE(status);
    if(mode!=SND_MD_STOP && !*seen){
        *seen=1;
        *started=now;
    }
    /* The score has a guard after the PCM. Check both real driver status
       and the sample-derived floor, including an asynchronous start. */
    return mode==SND_MD_STOP &&
        now-*started >= (unsigned)(*seen ? bruce_sfx_ticks[song]+(song==BRUCE_LAUGH_SONG?0:3) : 120);
}

static int bruce_voice_reap(unsigned now)
{
    if(bruce_voice<0)return 1;
    if(!bruce_sample_done(BRUCE_SFX_PORT,
        bruce_voice==BRUCE_DEATH_CUE?BRUCE_HURT_SONG:bruce_voice,
        now,&bruce_seen,&bruce_voice_at))return 0;
    bruce_voice=-1;
    return 1;
}

/* After a lethal hit Bruce can no longer issue a landing cue. Borrow the
   world-effects control for his existing death cue during a protected laugh. */
static void bruce_overlap_update(unsigned now)
{
    SndSeqStat status;
    if(bruce_overlap==BRUCE_OVERLAP_STOP){
        if(SND_StopSeq(BRUCE_OVERLAP_PORT)!=SND_RET_SET)return;
        combat[2]=(combat_sound){.pending=-1};
        bruce_overlap_at=now;
        bruce_overlap=BRUCE_OVERLAP_START;
    }else if(bruce_overlap==BRUCE_OVERLAP_START){
        if(now-bruce_overlap_at<3)return;
        SND_GetSeqStat(&status,BRUCE_OVERLAP_PORT);
        if(SND_SEQ_STAT_MODE(status)!=SND_MD_STOP)return;
        if(SND_SetSeqVl(BRUCE_OVERLAP_PORT,105,0)!=SND_RET_SET ||
           SND_StartSeq(BRUCE_OVERLAP_PORT,BRUCE_SFX_BANK,BRUCE_HURT_SONG,MF_SFX_PRIORITY)!=SND_RET_SET)return;
        bruce_overlap_seen=0;
        bruce_overlap_at=now;
        bruce_overlap=BRUCE_OVERLAP_PLAY;
    }else if(bruce_overlap==BRUCE_OVERLAP_PLAY &&
        bruce_sample_done(BRUCE_OVERLAP_PORT,BRUCE_HURT_SONG,now,&bruce_overlap_seen,&bruce_overlap_at)){
        bruce_overlap=BRUCE_OVERLAP_IDLE;
    }
}

static int bruce_stop_voice(unsigned now)
{
    if(SND_StopSeq(BRUCE_SFX_PORT)!=SND_RET_SET)return 0;
    bruce_voice=-1;
    bruce_stop_guard=1;
    bruce_stopped_at=now;
    return 1;
}

static int bruce_stop_complete(unsigned now)
{
    SndSeqStat status;
    if(!bruce_stop_guard)return 1;
    if(now-bruce_stopped_at<3)return 0;
    SND_GetSeqStat(&status,BRUCE_SFX_PORT);
    if(SND_SEQ_STAT_MODE(status)!=SND_MD_STOP)return 0;
    bruce_stop_guard=0;
    return 1;
}

static int bruce_legacy_death_update(unsigned events,unsigned now)
{
    if(bruce_encounter)events&=~(MF_COMBAT_HUMAN_DEATH(0)|MF_COMBAT_HUMAN_DEATH(1));
    return death_update(events,now);
}

static void bruce_audio_update(unsigned events,unsigned now,int legacy_death,int paused)
{
    int cue=-1;
    bruce_voice_reap(now);
    if(bruce_tone_owner!=1)return;
    if((events&MF_BRUCE_SFX_LAUGH) && !bruce_laugh_played)
        bruce_laugh_pending=1;
    if(events&MF_BRUCE_SFX_DEATH){
        if(bruce_voice==BRUCE_LAUGH_SONG || bruce_laugh_pending){
            if(bruce_overlap==BRUCE_OVERLAP_IDLE)bruce_overlap=BRUCE_OVERLAP_STOP;
            bruce_pending=-1;
        }else bruce_pending=BRUCE_DEATH_CUE;
    }
    bruce_overlap_update(now);
    if(!(events&MF_BRUCE_SFX_DEATH) && !paused && !legacy_death &&
       bruce_pending!=BRUCE_DEATH_CUE && !bruce_laugh_pending && bruce_voice!=BRUCE_LAUGH_SONG){
        if(events&(MF_BRUCE_SFX_JUMP|MF_BRUCE_ENTRANCE_JUMP))cue=BRUCE_JUMP_SONG;
        else if(events&MF_BRUCE_SFX_CHARGE)cue=BRUCE_CHARGE_SONG;
        else if((events&MF_BRUCE_SFX_HURT) && bruce_voice<0)cue=BRUCE_HURT_SONG;
        if(cue>=0 && (bruce_pending<0 ||
           bruce_cue_priority[cue]>=bruce_cue_priority[bruce_pending])){
            bruce_pending=cue;
            bruce_pending_at=now;
        }
    }
    if(bruce_pending>=0 && bruce_pending!=BRUCE_DEATH_CUE && now-bruce_pending_at>4)
        bruce_pending=-1;
    if(legacy_death || paused)return;
    if(bruce_laugh_pending && bruce_voice<0 && bruce_pending!=BRUCE_DEATH_CUE){
        bruce_pending=BRUCE_LAUGH_SONG;
        bruce_pending_at=now;
    }
    if(bruce_pending<0)return;
    if(bruce_voice>=0){
        if(bruce_voice==BRUCE_LAUGH_SONG)return;
        /* Preserve WOOPAH against nonlethal overlaps. */
        if(bruce_cue_priority[bruce_pending]<=bruce_cue_priority[bruce_voice])return;
        if(!bruce_stop_voice(now))return;
    }
    if(!bruce_stop_complete(now))return;
    if(SND_SetSeqVl(BRUCE_SFX_PORT,105,0)!=SND_RET_SET)return;
    if(SND_StartSeq(BRUCE_SFX_PORT,BRUCE_SFX_BANK,
                    bruce_pending==BRUCE_DEATH_CUE?BRUCE_HURT_SONG:bruce_pending,
                    (bruce_pending==BRUCE_DEATH_CUE || bruce_pending==BRUCE_LAUGH_SONG)?MF_SFX_PRIORITY:29)==SND_RET_SET){
        bruce_voice=bruce_pending;
        bruce_voice_at=now;
        bruce_seen=0;
        bruce_pending=-1;
        bruce_stop_guard=0;
        if(bruce_voice==BRUCE_LAUGH_SONG){
            bruce_laugh_pending=0;
            bruce_laugh_played=1;
        }
    }
}

static int bruce_release_bank(unsigned now)
{
    if(bruce_pending==BRUCE_DEATH_CUE || bruce_overlap!=BRUCE_OVERLAP_IDLE)return 0;
    bruce_pending=-1;
    bruce_laugh_pending=0;
    if(!bruce_voice_reap(now) &&
       (bruce_voice==BRUCE_DEATH_CUE || bruce_voice==BRUCE_LAUGH_SONG || !bruce_stop_voice(now)))return 0;
    return bruce_stop_complete(now);
}

int mf_music_bruce_bank(int requested,unsigned now)
{
    /* Let any already protected street death finish before Bruce enters.
       The encounter then has exclusive use of the shared sequencer control. */
    if(requested && mf_music_protected())return MF_BRUCE_BANK_WAIT;
    bruce_encounter=requested;
    if(!ready || bruce_audio_fault || bruce_tone_owner==requested)return MF_BRUCE_BANK_READY;
    if(requested){
        car_sound_update(0,0,0);
        if(car_sound_playing || (int)(now-car_safe_at)<0)return MF_BRUCE_BANK_WAIT;
        if(!bruce_cd_upload("BSFX.TON",MF_BRUCE_TON_BYTES,CAR_TON_ADDR)){
            bruce_audio_fault=1;
            return MF_BRUCE_BANK_TRANSFERRED; /* The old bank stays mapped if the read fails. */
        }
    }else{
        if(!bruce_release_bank(now))return MF_BRUCE_BANK_WAIT;
        if(!upload("CARPASS.TON",CAR_TON_BYTES,CAR_TON_ADDR)){
            bruce_audio_fault=1;
            return MF_BRUCE_BANK_TRANSFERRED;
        }
    }
    bruce_tone_owner=requested;
    if(requested)bruce_laugh_played=0;
    return MF_BRUCE_BANK_TRANSFERRED;
}

int mf_music_bruce_exit(void)
{
    return bruce_tone_owner!=1 || bruce_release_bank(audio_tick);
}
#endif

int mf_music_init(void)
{
    int size=0,ok;
    char *map=jo_fs_read_file("CUSTOM.MAP",&size);
    SndIniDt init;
    volatile unsigned int *p;
#if MF_VEHICLE_AMBUSH
    /* Preserve all six stock map entries. One more describes the standalone
       vehicle bank. Padding covers the SDK's word-sized initialization copy. */
    unsigned int extended_map[36]={0};
    static const unsigned char car_entries[]={
#if MF_BRUCE_RUNTIME
        0x02,CAR_TON_ADDR>>16,(CAR_TON_ADDR>>8)&255,CAR_TON_ADDR&255,0x80,0,MF_BRUCE_TON_BYTES>>8,MF_BRUCE_TON_BYTES&255,
        0x12,BRUCE_SFX_SEQ_ADDR>>16,(BRUCE_SFX_SEQ_ADDR>>8)&255,BRUCE_SFX_SEQ_ADDR&255,
        0x80,0,MF_BRUCE_SEQ_BYTES>>8,MF_BRUCE_SEQ_BYTES&255,
#else
        0x02,CAR_TON_ADDR>>16,(CAR_TON_ADDR>>8)&255,CAR_TON_ADDR&255,0x80,0,CAR_TON_BYTES>>8,CAR_TON_BYTES&255,
#endif
        0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff
    };
    char *original_map=map;
#endif
    ready=0;
    music_state=MUSIC_IDLE;
    if(!map || size!=MF_CUSTOM_MAP_BYTES) { if(map) jo_free(map); return 0; }
#if MF_VEHICLE_AMBUSH
    for(int i=0;i<MF_CUSTOM_MAP_BYTES-8;i++)((unsigned char *)extended_map)[i]=(unsigned char)map[i];
    for(unsigned i=0;i<sizeof(car_entries);i++)
        ((unsigned char *)extended_map)[MF_CUSTOM_MAP_BYTES-8+i]=car_entries[i];
    map=(char *)extended_map;
    size=MF_CUSTOM_MAP_BYTES-8+sizeof(car_entries);
    car_sound_triggered=car_sound_playing=car_sound_setup=0;
#endif
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
#if MF_VEHICLE_AMBUSH
    jo_free(original_map);
#else
    jo_free(map);
#endif
    ok=upload("FX.SEQ",MF_FX_SEQ_BYTES,MF_FX_SEQ_ADDR);
    ok=upload("FX.TON",MF_FX_TON_BYTES,MF_FX_TON_ADDR)&&ok;
    ok=upload("STAGE.SEQ",MF_STAGE_SEQ_BYTES,MF_STAGE_SEQ_ADDR)&&ok;
    ok=upload("STAGE.TON",MF_STAGE_TON_BYTES,MF_STAGE_TON_ADDR)&&ok;
#if MF_VEHICLE_AMBUSH
    ok=upload("CARPASS.TON",CAR_TON_BYTES,CAR_TON_ADDR)&&ok;
#if MF_BRUCE_RUNTIME
    bruce_encounter=bruce_tone_owner=bruce_audio_fault=bruce_stop_guard=bruce_laugh_pending=0;
    bruce_voice=bruce_pending=-1;
    car_safe_at=0;
    ok=bruce_cd_upload("BSFX.SEQ",MF_BRUCE_SEQ_BYTES,BRUCE_SFX_SEQ_ADDR)&&ok;
#endif
#endif
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
    if(player==2 && (events&(MF_WORLD_IMPACT|MF_BRUCE_SFX_LAND))) {
        song=2;
    }else if(player==2 && (events&MF_VEHICLE_WARNING)){
        song=7;
    }else if(events&MF_COMBAT_CONNECT(player)) {
        song=6;c->hit_wait=4; /* Lethal results always take precedence. */
    }else if((events&MF_COMBAT_NONKILL(player)) && !c->hit_wait) {
        song=(events&MF_COMBAT_HEAVY_HIT(player))?6:0;c->hit_wait=4;
    }else if(events&(MF_COMBAT_BAT(player)|MF_COMBAT_JAB(player)))song=5;
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
static int start_music(int song)
{
    return SND_SetSeqVl(0,MF_MUSIC_VOLUME,0)==SND_RET_SET &&
           SND_StartSeq(0,1,song,MF_MUSIC_PRIORITY)==SND_RET_SET;
}

static void update_music(int started,int events)
{
    /* Player respawn keeps the current encounter. A new stage starts idle. */
    if(!started) {
        if(music_state!=MUSIC_IDLE && SND_StopSeq(0)==SND_RET_SET)
            music_state=MUSIC_IDLE;
        return;
    }
    if((music_state==MUSIC_IDLE || music_state==MUSIC_STREET) &&
       (events&MF_BRUCE_ENTRANCE_JUMP))
        music_state=MUSIC_STOPPING;
    if(music_state==MUSIC_IDLE && start_music(0))music_state=MUSIC_STREET;
    /* The native queue consumes the stop and start in submission order.
       Retry rejected commands without submitting a second accepted stop. */
    if(music_state==MUSIC_STOPPING && SND_StopSeq(0)==SND_RET_SET)
        music_state=MUSIC_STARTING_BRUCE;
    if(music_state==MUSIC_STARTING_BRUCE && start_music(1))
        music_state=MUSIC_BRUCE;
}

#if MF_DEV_MODE
/* The section loader owns audio until all accepted stops have reached the
   driver. Keep tone ownership and the vehicle sample's reuse deadline. */
int mf_music_section_reset(unsigned now, int post_bruce)
{
    static unsigned stopped, stopped_at;
    unsigned port;
    if (!ready) return 1;

    car_sound_update(0, 0, 0);
    if (car_sound_playing) return 0;
    for (port = 0; port < 8; ++port) {
        if (stopped & (1u << port)) continue;
        if (SND_StopSeq(port) != SND_RET_SET) return 0;
        stopped |= 1u << port;
        stopped_at = now;
    }
    if (now - stopped_at < 3) return 0;
    for (port = 0; port < 8; ++port) {
        SndSeqStat status;
        SND_GetSeqStat(&status, port);
        if (SND_SEQ_STAT_MODE(status) != SND_MD_STOP) return 0;
    }

    music_state = post_bruce ? MUSIC_STARTING_BRUCE : MUSIC_IDLE;
    audio_tick = now;
    pause_mask = paused_state = torch_playing = hiss_guard = 0;
    pause_target = -1;
    for (port = 0; port < 3; ++port) {
        combat[port] = (combat_sound){.pending = -1};
        sfx_wait[port] = 0;
    }
    death_pending = death_prepared = death_active = death_seen = death_retiring = 0;
    bruce_voice = bruce_pending = -1;
    bruce_seen = bruce_stop_guard = bruce_laugh_pending = bruce_laugh_played = 0;
    bruce_overlap = BRUCE_OVERLAP_IDLE;
    stopped = 0;
    return 1;
}
#endif

void mf_music_update(int started,int paused,int events,unsigned int now)
{
    int i,protected,music_events=events;unsigned int elapsed=now-audio_tick;audio_tick=now;
    if(!ready)return;
#if MF_BRUCE_RUNTIME && MF_VEHICLE_AMBUSH
    protected=bruce_legacy_death_update(events,now);
    bruce_audio_update(events,now,protected,paused);
#else
    protected=death_update(events,now);
#endif
#if MF_VEHICLE_AMBUSH
    int vehicle_pass=started && (events&MF_VEHICLE_PASS);
#if MF_BRUCE_RUNTIME
    if(bruce_tone_owner!=0)vehicle_pass=0;
#endif
    car_sound_update(vehicle_pass,vehicle_pass && !paused && !protected && !(events&(MF_WORLD_IMPACT|MF_BRUCE_SFX_LAND)),
                     started && paused);
#endif
    if(protected)events&=MF_TORCH_HISS;
    if(paused || paused_state)for(i=0;i<3;i++)if(combat[i].playing)combat[i].ends_at+=elapsed;
    if(torch_playing && (!started || paused || !(events&MF_TORCH_HISS))) {
        if(SND_StopSeq(4)==SND_RET_SET){torch_playing=0;hiss_guard=1;hiss_stopped_at=now;}
    }
    if(!started) {
        update_music(0,0);
        for(i=0;i<3;i++) {
            combat[i].pending=-1;
            if(combat[i].playing && SND_StopSeq(combat_port(i))==SND_RET_SET)combat[i].playing=0;
        }
        return;
    }
    update_music(1,music_events);
    /* Hiss is stopped above. Pause/resume owns SFX ports1..6; music control0 keeps running. */
    if(paused!=paused_state || pause_target>=0) {
        if(pause_target!=paused){pause_target=paused;pause_mask=0;}
        for(i=1;i<7;i++)if(i!=4 && !(pause_mask&(1u<<i))) {
#if MF_BRUCE_RUNTIME && MF_VEHICLE_AMBUSH
            if(i==BRUCE_OVERLAP_PORT && bruce_overlap!=BRUCE_OVERLAP_IDLE){
                pause_mask|=1u<<i;
                continue;
            }
#endif
            if((paused?SND_PauseSeq(i):SND_ContSeq(i))==SND_RET_SET)pause_mask|=1u<<i;
        }
        if(pause_mask!=0x6e)return;
        paused_state=paused;pause_mask=0;pause_target=-1;
        /* A collision awaiting a replacement must not become a stale hit on resume. */
        if(paused)for(i=0;i<3;i++)combat[i].pending=-1;
    }
    if(paused)return;
    for(i=0;i<3;i++)sfx_wait[i]=elapsed>=sfx_wait[i]?0:sfx_wait[i]-elapsed;
    if(protected) {
        for(i=0;i<3;i++) {
            combat[i].hit_wait=elapsed>=combat[i].hit_wait?0:combat[i].hit_wait-elapsed;
            if(combat[i].playing && (int)(now-combat[i].ends_at)>=0)combat[i].playing=0;
        }
        return; /* Requests are discarded, never queued for a later burst. */
    }
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
    for(i=0;i<3;i++){
#if MF_VEHICLE_AMBUSH
        if(i==2 && (car_sound_playing
#if MF_BRUCE_RUNTIME
                   || bruce_overlap!=BRUCE_OVERLAP_IDLE
#endif
                   ))continue;
#endif
        combat_update(i,i==2?(int)(events&(MF_WORLD_IMPACT|MF_BRUCE_SFX_LAND|MF_VEHICLE_WARNING)):events,now,elapsed);
    }
}
