#include <assert.h>
#include <stdio.h>
#include "../src/music.c"

static int reject_stop, reject_start, mode, starts[2], stops;

int SND_SetSeqVl(int port,int volume,int fade)
{
    assert(port==0 && volume==MF_MUSIC_VOLUME && fade==0);
    return SND_RET_SET;
}

int SND_StartSeq(int port,int bank,int song,int priority)
{
    assert(port==0 && bank==1 && (song==0 || song==1) && priority==MF_MUSIC_PRIORITY);
    if(reject_start)return 1;
    ++starts[song];
    mode=SND_MD_PLAY;
    return SND_RET_SET;
}

int SND_StopSeq(int port)
{
    assert(port==0);
    if(reject_stop)return 1;
    ++stops;
    return SND_RET_SET;
}

void SND_GetSeqStat(SndSeqStat *status,int port)
{
    assert(port==0);
    status->mode=mode;
    status->stat=0;
}

int main(void)
{
    update_music(1,0,10);
    assert(starts[0]==1);
    reject_stop=1;
    update_music(1,MF_BRUCE_ENTRANCE_LANDED,20);
    assert(stops==0 && music_state==MUSIC_STOPPING);
    reject_stop=0;
    update_music(1,0,21);
    assert(stops==1 && music_state==MUSIC_INTERLUDE);

    update_music(1,0,51);
    assert(starts[1]==0); /* Still waiting for Bruce to become combat-ready. */
    update_music(1,MF_BRUCE_COMBAT_READY,52);
    assert(starts[1]==0); /* The accepted stop is still pending in the driver. */
    mode=SND_MD_STOP;
    reject_start=1;
    update_music(1,0,53);
    reject_start=0;
    update_music(1,0,54);
    assert(starts[1]==1 && music_state==MUSIC_BRUCE);

    update_music(1,MF_COMBAT_HURT(0),55);
    update_music(1,MF_BRUCE_ENTRANCE_LANDED|MF_BRUCE_COMBAT_READY,100);
    assert(starts[1]==1 && stops==1);
    update_music(0,0,101);
    assert(stops==2 && music_state==MUSIC_IDLE && !bruce_combat_ready);
    update_music(1,0,102);
    assert(starts[0]==2);
    update_music(1,MF_BRUCE_ENTRANCE_LANDED,110);
    mode=SND_MD_STOP;
    update_music(1,MF_BRUCE_COMBAT_READY,115);
    update_music(1,0,139);
    assert(starts[1]==1);
    update_music(1,0,140);
    assert(starts[1]==2 && stops==3);
    puts("PASS Bruce music: port 0 only, interlude, readiness, retries, one shot, reset");
    return 0;
}
