/* Production transport, acknowledged commands and asynchronous native status. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/music.c"
char sddrvstsk[1];
char *jo_fs_read_file(const char *n,int *s){(void)n;*s=0;return NULL;}
void jo_free(void *p){free(p);}void slSoundOffWait(void){}void slSoundOnWait(void){}
void slDMACopy(void *s,void *d,unsigned n){(void)s;(void)d;(void)n;}void slDMAWait(void){}void slSndFlush(void){}
void slInitSound(Uint8 *p,unsigned s,Uint8 *m,unsigned n){(void)p;(void)s;(void)m;(void)n;}
void SND_Init(SndIniDt *s){(void)s;}int SND_ChgMap(int m){(void)m;return 0;}int SND_StopDsp(void){return 0;}int SND_SetCdDaLev(int a,int b){(void)a;(void)b;return 0;}int SND_SetTlVl(int a){(void)a;return 0;}
static int starts[8][9],stops[8],pauses[8],vol_reject,start_reject,mode=SND_MD_STOP;static unsigned clock_now;
int SND_SetSeqVl(int p,int v,int f){assert(p>=0 && p<8 && v==(p?MF_SFX_VOLUME:MF_MUSIC_VOLUME) && !f);return p==7?vol_reject:0;}
int SND_StartSeq(int p,int bank,int song,int pri){assert(p>=0 && p<8 && song>=0 && song<9);assert(bank==(p?0:1) && pri==(p?MF_SFX_PRIORITY:MF_MUSIC_PRIORITY));if(p==7 && start_reject)return 1;starts[p][song]++;return 0;}
int SND_StopSeq(int p){assert(p>0 && p<8);if(p==7)assert(mode==SND_MD_STOP && death_seen && clock_now-death_started>=MF_DEATH_MIN_TICKS);stops[p]++;return 0;}
int SND_PauseSeq(int p){assert(p>0 && p<7 && p!=4);pauses[p]++;return 0;}
int SND_ContSeq(int p){assert(p>0 && p<7 && p!=4);return 0;}
void SND_GetSeqStat(SndSeqStat *s,int p){assert(p==7);s->mode=mode;s->stat=0;}
static void update(unsigned events,int paused){mf_music_update(1,paused,events,++clock_now);}
int main(void){int i,j,total_before=0,total_after=0,n;ready=1;update(MF_COMBAT_JAB(0)|MF_TORCH_HISS,0);assert(starts[5][5]==1 && torch_playing);
 vol_reject=1;update(MF_COMBAT_HUMAN_DEATH(0)|MF_COMBAT_CONNECT(0)|MF_WORLD_IMPACT|MF_TORCH_HISS,0);assert(mf_music_protected() && !starts[7][8] && !stops[5] && !stops[4]);
 vol_reject=0;start_reject=1;update(MF_COMBAT_JAB(0),0);assert(mf_music_protected() && !starts[7][8]);start_reject=0;update(0,0);assert(starts[7][8]==1 && death_active);
 for(i=0;i<8;i++)for(j=0;j<9;j++)total_before+=starts[i][j];
 for(i=0;i<100;i++)update(MF_COMBAT_HUMAN_DEATH(1)|MF_COMBAT_NONKILL(0)|MF_COMBAT_HEAVY_HIT(0)|MF_COMBAT_BAT(1)|MF_WORLD_IMPACT|MF_TORCH_IGNITE|MF_JUMP_SOUND|MF_TORCH_HISS,0);
 assert(mf_music_protected()); /* Never unlock on initial/stale STOP. */
 mode=SND_MD_PLAY;update(0,0);mode=SND_MD_STOP;for(i=0;i<MF_DEATH_MIN_TICKS-1;i++)update(MF_COMBAT_HUMAN_DEATH(0),i%2);assert(mf_music_protected());
 for(i=0;i<8;i++){for(j=0;j<9;j++)total_after+=starts[i][j];}
 assert(total_before==total_after && starts[7][8]==1);
 update(0,0);assert(mf_music_protected() && death_retiring);update(0,0);assert(!mf_music_protected());for(i=0;i<3;i++)assert(combat[i].pending<0);n=starts[6][6];update(MF_COMBAT_NONKILL(1)|MF_COMBAT_HEAVY_HIT(1),0);assert(starts[6][6]==n+1);
 n=starts[7][8];update(MF_COMBAT_HUMAN_DEATH(0)|MF_COMBAT_HUMAN_DEATH(1),0);assert(starts[7][8]==n+1);mode=SND_MD_PLAY;update(0,1);for(i=0;i<MF_DEATH_MIN_TICKS+5;i++)update(MF_COMBAT_JAB(0),1);assert(mf_music_protected()); /* PLAY blocks even past the duration floor. */
 mode=SND_MD_STOP;update(0,1);assert(mf_music_protected());update(0,1);assert(!mf_music_protected());assert(starts[0][0]==1);for(i=0;i<3;i++)assert(!combat[i].pending || combat[i].pending==-1);
 puts("PASS protected UGH: dedicated control, existing SFX retained, acknowledged retries, async status, full-duration floor, no restart/backlog, pause-independent completion, immediate fresh hits and continuous music");return 0;}
