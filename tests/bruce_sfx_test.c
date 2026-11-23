#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#define MF_BRUCE_RUNTIME 1
#define MF_VEHICLE_AMBUSH 1
char *jo_fs_read_file_in_dir(const char *,const char *,int *);
int SND_CtrlDirMidi(int,int,int,int,int,int);
#include "../src/music.c"

static int mode,starts,stops,last_song,last_priority,uploads,fail_start,fail_stop;

void SND_GetSeqStat(SndSeqStat *status,int port)
{
    assert(port==BRUCE_SFX_PORT);
    status->mode=mode;
}

int SND_SetSeqVl(int port,int volume,int fade)
{
    assert(port==BRUCE_SFX_PORT && volume==105 && !fade);
    return SND_RET_SET;
}

int SND_StartSeq(int port,int bank,int song,int priority)
{
    assert(port==BRUCE_SFX_PORT && bank==2 && song>=0 && song<4);
    if(fail_start)return 1;
    last_song=song;
    last_priority=priority;
    mode=SND_MD_PLAY;
    ++starts;
    return SND_RET_SET;
}

int SND_StopSeq(int port)
{
    assert(port==BRUCE_SFX_PORT);
    if(fail_stop)return 1;
    mode=SND_MD_STOP;
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

int main(void)
{
    ready=1;
    car_sound_playing=1;
    car_safe_at=110;
    assert(!mf_music_bruce_bank(1,109) && !uploads && !car_sound_playing);
    assert(mf_music_bruce_bank(1,110) && uploads==1 && bruce_tone_owner==1);
    assert(mf_music_bruce_bank(1,111) && uploads==1);

    fail_start=1;
    bruce_audio_update(MF_BRUCE_SFX_JUMP,111,0,0);
    assert(!starts);
    fail_start=0;
    bruce_audio_update(0,112,0,0);
    assert(starts==1 && last_song==BRUCE_JUMP_SONG && last_priority==29);
    bruce_audio_update(MF_BRUCE_SFX_HURT|MF_BRUCE_SFX_LAUGH,113,0,0);
    bruce_audio_update(MF_BRUCE_SFX_CHARGE,114,0,0);
    assert(!stops && starts==1 && bruce_laugh_pending);
    mode=SND_MD_STOP;
    bruce_audio_update(0,130,0,0);
    assert(starts==1);
    bruce_audio_update(0,190,0,0);
    assert(starts==2 && last_song==BRUCE_LAUGH_SONG && !bruce_laugh_pending);
    fail_stop=1;
    bruce_audio_update(MF_BRUCE_SFX_DEATH|MF_BRUCE_SFX_LAUGH,191,0,0);
    assert(!stops && starts==2 && !bruce_laugh_pending);
    fail_stop=0;
    bruce_audio_update(0,192,1,0);
    assert(!stops && starts==2); /* Protected legacy death owns its own port. */
    bruce_audio_update(0,193,0,0);
    assert(stops==1 && starts==2);
    bruce_audio_update(0,196,0,0);
    assert(starts==3 && last_song==BRUCE_HURT_SONG && last_priority==30);
    assert(!mf_music_bruce_bank(0,197) && uploads==1);
    mode=SND_MD_STOP;
    assert(mf_music_bruce_bank(0,237) && uploads==2 && bruce_tone_owner==0);
    assert(mf_music_bruce_bank(1,240) && uploads==3);
    bruce_audio_update(MF_BRUCE_SFX_CHARGE,241,0,0);
    assert(starts==4 && last_song==BRUCE_CHARGE_SONG);
    assert(!mf_music_bruce_bank(0,242) && stops==2);
    assert(!mf_music_bruce_bank(0,244));
    assert(mf_music_bruce_bank(0,245) && uploads==4);
    puts("PASS Bruce cue arbitration, independent control, PCM completion and reversible bank guards");
}
