#include <assert.h>
#include <stdio.h>
#include "../src/music.c"

static int reject_stop, reject_start, starts[2], stops;

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
    return SND_RET_SET;
}

int SND_StopSeq(int port)
{
    assert(port==0);
    if(reject_stop)return 1;
    ++stops;
    return SND_RET_SET;
}

int main(void)
{
    update_music(1,0);
    assert(starts[0]==1);
    reject_stop=1;
    update_music(1,MF_BRUCE_ENTRANCE_JUMP);
    assert(stops==0 && music_state==MUSIC_STOPPING);
    reject_stop=0;
    reject_start=1;
    update_music(1,0);
    assert(stops==1 && music_state==MUSIC_STARTING_BRUCE);
    update_music(1,MF_BRUCE_ENTRANCE_JUMP);
    assert(stops==1 && starts[1]==0);
    reject_start=0;
    update_music(1,0);
    assert(starts[1]==1 && music_state==MUSIC_BRUCE);
    update_music(1,MF_COMBAT_HURT(0)|MF_BRUCE_ENTRANCE_JUMP);
    assert(starts[1]==1 && stops==1);
    update_music(0,0);
    assert(stops==2 && music_state==MUSIC_IDLE);
    update_music(1,0);
    assert(starts[0]==2);
    update_music(1,MF_BRUCE_ENTRANCE_JUMP);
    assert(starts[1]==2 && stops==3 && music_state==MUSIC_BRUCE);
    puts("PASS Bruce music: same-update port 0 handoff, retries, one shot, reset");
    return 0;
}
