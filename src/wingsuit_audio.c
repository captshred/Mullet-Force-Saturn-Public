#include <jo/jo.h>
#include <SEGA_SND.H>
#include "music_data.h"
#include "wingsuit_audio_data.h"
#include "wingsuit_audio.h"
#ifndef MF_WS_SOUND_BASE
#define MF_WS_SOUND_BASE ((unsigned char *)0x25a00000)
#endif
extern char sddrvstsk[];
static unsigned ends[4];
static unsigned pending,ports;
static int ready;
static int upload(mf_ws_audio_reader read,const char *name,int expected,unsigned addr)
{
    int n=expected;char *p=read(name,expected);
    if(!p)return 0;
    if(addr+(unsigned)n>0x80000){jo_free(p);return 0;}
    slDMACopy(p,MF_WS_SOUND_BASE+addr,n);slDMAWait();jo_free(p);return 1;
}
int mf_ws_audio_load(mf_ws_audio_reader read)
{
    int n=MF_WS_MAP_BYTES,i,ok;char *map;SndIniDt init;
    ready=pending=ports=0;for(i=0;i<4;i++)ends[i]=0;
    map=read("WDEATH.MAP",n);
    if(!map)return 0;
    slSoundOffWait();
    SND_INI_PRG_ADR(init)=(Uint16 *)sddrvstsk;SND_INI_PRG_SZ(init)=MF_SOUND_DRIVER_BYTES;
    SND_INI_ARA_ADR(init)=(Uint16 *)map;SND_INI_ARA_SZ(init)=n;
    SND_Init(&init);SND_ChgMap(0);
    slInitSound((Uint8 *)sddrvstsk,MF_SOUND_DRIVER_BYTES,(Uint8 *)map,n);slDMAWait();jo_free(map);
    ok=upload(read,"WDEATH.SEQ",MF_WS_SEQ_BYTES,MF_WS_SEQ_ADDR);
    ok=upload(read,"WDEATH.TON",MF_WS_TON_BYTES,MF_WS_TON_ADDR)&&ok;
    if(!ok)return 0; /* Keep the sound CPU stopped on partial failure. */
    /* Same driver transfer-complete flag reset as the approved music loader. */
    MF_WS_SOUND_BASE[0x4e1]=0;
    slSoundOnWait();slSndFlush();slDMAWait();SND_StopDsp();SND_SetCdDaLev(0,0);SND_SetTlVl(15);
    ready=1;return 1;
}
void mf_ws_audio_events(int count)
{
    /* At most ten deaths in one tick, with paced eight-slot enemy spawning.
       Four one-shot ports drain faster than the sustainable death rate. */
    if(ready && count>0)pending+=(unsigned)count;
}
void mf_ws_audio_step(unsigned now)
{
    int i;if(!ready)return;
    for(i=0;i<4 && pending;i++)if(!(ports&(1u<<i)) || (int)(now-ends[i])>=0){
        if(SND_SetSeqVl(i+1,MF_SFX_VOLUME,0)==SND_RET_SET &&
           SND_StartSeq(i+1,0,0,MF_SFX_PRIORITY)==SND_RET_SET){
            --pending;ports|=1u<<i;ends[i]=now+49; /* Canonical 47-tick one-shot + release guard. */
        }
    }
}
