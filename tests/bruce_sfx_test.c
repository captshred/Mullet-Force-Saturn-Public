#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#define MF_BRUCE_RUNTIME 1
#define MF_VEHICLE_AMBUSH 1
#define MF_DEV_MODE 1
char *jo_fs_read_file_in_dir(const char *,const char *,int *);
int SND_CtrlDirMidi(int,int,int,int,int,int);
#include "../src/music.c"

static int modes[8],starts,stops,last_song,last_priority,uploads,fail_start,fail_stop;
static int laugh_stops, overlap_starts, combat_starts;

void SND_GetSeqStat(SndSeqStat *status,int port)
{
    status->mode=modes[port];
}

int SND_SetSeqVl(int port,int volume,int fade)
{
    assert(port>=0 && port<8 && volume>=0 && !fade);
    return SND_RET_SET;
}

int SND_StartSeq(int port,int bank,int song,int priority)
{
    assert(port>=0 && port<8 && bank>=0 && bank<=2);
    if(fail_start)return 1;
    last_song=song;
    last_priority=priority;
    modes[port]=SND_MD_PLAY;
    if(port==BRUCE_OVERLAP_PORT && bank==2)++overlap_starts;
    if(port==5 && bank==0)++combat_starts;
    ++starts;
    return SND_RET_SET;
}

int SND_StopSeq(int port)
{
    if(fail_stop)return 1;
    if(port==BRUCE_SFX_PORT && bruce_voice==BRUCE_LAUGH_SONG)++laugh_stops;
    modes[port]=SND_MD_STOP;
    ++stops;
    return SND_RET_SET;
}

int SND_CtrlDirMidi(int port,int priority,int command,int channel,int note,int velocity)
{
    assert(port==3 && !priority && !command && channel==15 && note==61 && !velocity);
    return SND_RET_SET;
}

char *jo_fs_read_file(const char *name,int *length)
{
    assert(name[0]=='C');
    *length=CAR_TON_BYTES;
    return malloc(*length);
}

char *jo_fs_read_file_in_dir(const char *name,const char *dir,int *length)
{
    assert(name[0]=='B' && dir[0]=='R');
    *length=MF_BRUCE_TON_BYTES;
    return malloc(*length);
}

void jo_free(void *data){free(data);}
void slDMACopy(void *src,void *dst,unsigned bytes)
{
    assert(src && (unsigned long)dst==0x25a00000u+CAR_TON_ADDR);
    assert(bytes==CAR_TON_BYTES || bytes==MF_BRUCE_TON_BYTES);
    ++uploads;
}
void slDMAWait(void){}
int SND_PauseSeq(int port){assert(port!=BRUCE_SFX_PORT && port!=BRUCE_OVERLAP_PORT);return SND_RET_SET;}
int SND_ContSeq(int port){assert(port!=BRUCE_SFX_PORT && port!=BRUCE_OVERLAP_PORT);return SND_RET_SET;}

int main(void)
{
    ready=1;
    car_sound_playing=1;
    car_safe_at=110;
    assert(!mf_music_bruce_bank(1,109) && !uploads && !car_sound_playing);
    assert(mf_music_bruce_bank(1,110) && uploads==1 && bruce_tone_owner==1);
    assert(mf_music_bruce_bank(1,111) && uploads==1);

    fail_start=1;
    bruce_audio_update(MF_BRUCE_ENTRANCE_JUMP,111,0,0);
    assert(!starts);
    fail_start=0;
    bruce_audio_update(0,112,0,0);
    assert(starts==1 && last_song==BRUCE_JUMP_SONG && last_priority==29);
    bruce_audio_update(MF_BRUCE_SFX_LAND|MF_BRUCE_SFX_HURT|MF_BRUCE_SFX_LAUGH,113,0,0);
    bruce_audio_update(MF_BRUCE_SFX_CHARGE,114,0,0);
    assert(!stops && starts==1 && bruce_laugh_pending);
    modes[BRUCE_SFX_PORT]=SND_MD_STOP;
    bruce_audio_update(0,130,0,0);
    assert(starts==1);
    bruce_audio_update(0,190,0,0);
    assert(starts==2 && last_song==BRUCE_LAUGH_SONG && last_priority==MF_SFX_PRIORITY);
    assert(!bruce_laugh_pending && bruce_laugh_played);

    music_state=MUSIC_BRUCE;
    mf_music_update(1,0,MF_BRUCE_SFX_CHARGE|MF_COMBAT_JAB(0),191);
    assert(combat_starts==1 && !laugh_stops && bruce_voice==BRUCE_LAUGH_SONG);
    fail_stop=1;
    mf_music_update(1,0,MF_BRUCE_SFX_DEATH|MF_BRUCE_SFX_LAUGH,192);
    assert(!overlap_starts && !laugh_stops && !bruce_laugh_pending);
    fail_stop=0;
    mf_music_update(1,0,0,193);
    mf_music_update(1,1,0,196);
    assert(overlap_starts==1 && last_song==BRUCE_HURT_SONG);
    assert(modes[BRUCE_SFX_PORT]==SND_MD_PLAY && modes[BRUCE_OVERLAP_PORT]==SND_MD_PLAY);
    mf_music_update(1,0,0,197);
    modes[BRUCE_OVERLAP_PORT]=SND_MD_STOP;
    modes[BRUCE_SFX_PORT]=SND_MD_STOP;
    mf_music_update(1,0,0,236);
    assert(bruce_voice==BRUCE_LAUGH_SONG && !laugh_stops);
    assert(mf_music_bruce_bank(0,236)==MF_BRUCE_BANK_WAIT);
    mf_music_update(1,0,0,245);
    assert(bruce_voice<0 && bruce_overlap==BRUCE_OVERLAP_IDLE && !laugh_stops);
    bruce_audio_update(MF_BRUCE_SFX_LAUGH,246,0,0);
    assert(bruce_voice<0 && !bruce_laugh_pending);
    assert(mf_music_bruce_bank(0,247)==MF_BRUCE_BANK_TRANSFERRED && uploads==2);

    /* Legacy POOWAH still owns control 7 until its full natural completion. */
    assert(bruce_legacy_death_update(MF_COMBAT_HUMAN_DEATH(1),250));
    assert(last_song==8 && death_active);
    assert(mf_music_bruce_bank(1,251)==MF_BRUCE_BANK_WAIT && uploads==2);
    assert(bruce_legacy_death_update(0,251));
    modes[BRUCE_SFX_PORT]=SND_MD_STOP;
    assert(bruce_legacy_death_update(0,297) && !death_active);
    assert(!bruce_legacy_death_update(0,298));
    assert(mf_music_bruce_bank(1,298)==MF_BRUCE_BANK_TRANSFERRED && uploads==3);

    /* Two successive section restarts clear both leased controls and one-shot state. */
    for(unsigned now=300;now<320;now+=10){
        bruce_audio_update(MF_BRUCE_SFX_LAUGH,now,0,0);
        bruce_audio_update(MF_BRUCE_SFX_DEATH,now+1,0,0);
        bruce_audio_update(0,now+4,0,0);
        assert(bruce_voice==BRUCE_LAUGH_SONG && bruce_overlap==BRUCE_OVERLAP_PLAY);
        assert(!mf_music_section_reset(now+5,0));
        assert(mf_music_section_reset(now+8,0));
        assert(bruce_voice<0 && !bruce_laugh_played && bruce_overlap==BRUCE_OVERLAP_IDLE);
    }
    puts("PASS Bruce laugh protection, combat overlap, lethal cue, legacy POOWAH and repeated resets");
}
