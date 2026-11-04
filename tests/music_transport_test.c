/* Test actual transport with SDK commands mocked; not an SCSP playback test. */
#include <assert.h>
#include <stdio.h>
#include "../src/music.c"
char sddrvstsk[1];
char *jo_fs_read_file(const char *name,int *size) {(void)name;*size=0;return NULL;}
void jo_free(void *p){free(p);}
void slSoundOffWait(void){}
void slSoundOnWait(void){}
void slDMACopy(void *s,void *d,unsigned int size){(void)s;(void)d;(void)size;}
void slDMAWait(void){}
void slSndFlush(void){}
void slInitSound(Uint8 *p,unsigned int s,Uint8 *m,unsigned int n){(void)p;(void)s;(void)m;(void)n;}
void SND_Init(SndIniDt *i){(void)i;}
int SND_ChgMap(int map){(void)map;return 0;}
int SND_StopDsp(void){return 0;}
int SND_SetCdDaLev(int l,int r){(void)l;(void)r;return 0;}
int SND_SetTlVl(int v){(void)v;return 0;}

static unsigned int clock_now;
static int accepts=1,fail_stop=-1,fail_pause=-1;
static int started_song[7][8],stopped_port[7],paused_port[7],resumed_port[7];
int SND_SetSeqVl(int p,int v,int fade){assert(p>=0 && p<7 && v==(p?MF_SFX_VOLUME:MF_MUSIC_VOLUME) && fade==0);return !accepts;}
int SND_StartSeq(int p,int bank,int song,int priority){assert(p>=0 && p<7 && song>=0 && song<8);assert(bank==(p?0:1) && priority==(p?MF_SFX_PRIORITY:MF_MUSIC_PRIORITY));if(!accepts)return 1;started_song[p][song]++;return 0;}
int SND_StopSeq(int p){assert(p>0 && p<7);if(!accepts || p==fail_stop)return 1;stopped_port[p]++;return 0;}
int SND_PauseSeq(int p){assert(p>=0 && p<7 && p!=4);paused_port[p]++;return !accepts || p==fail_pause;}
int SND_ContSeq(int p){assert(p>=0 && p<7 && p!=4);resumed_port[p]++;return !accepts;}
static void update(int events){mf_music_update(1,0,events,++clock_now);}
int main(void){int i,n;
 assert(!mf_music_init());update(MF_COMBAT_JAB(0));assert(!started_song[5][5]);ready=1;
 accepts=0;update(0);assert(!playing);accepts=1;update(0);assert(playing && started_song[0][0]==1);
 update(MF_COMBAT_JAB(0)|MF_COMBAT_BAT(1));assert(started_song[5][5]==1 && started_song[6][7]==1);
 update(MF_COMBAT_CONNECT(0));assert(stopped_port[5]==1 && !stopped_port[6] && !started_song[5][6]);
 /* Catch-up updates at the same VBlank cannot bypass the release guard. */
 for(i=0;i<6;i++){mf_music_update(1,0,0,clock_now);}assert(!started_song[5][6]);
 update(0);assert(started_song[5][6]==1 && !stopped_port[6]);
 for(i=0;i<2;i++){update(MF_COMBAT_NONKILL(0));}assert(started_song[5][6]==1);
 /* Stop command rejection never permits CONNECT to overlap the whoosh. */
 fail_stop=6;update(MF_COMBAT_CONNECT(1));update(0);assert(!started_song[6][6]);
 fail_stop=-1;update(0);assert(stopped_port[6]==1 && !started_song[6][6]);update(0);assert(started_song[6][6]==1);
 /* No new sound merely for holding a bat or keeping a hitbox overlapped. */
 n=started_song[6][7];for(i=0;i<60;i++){update(0);}assert(started_song[6][7]==n);
 /* Misses finish naturally; a later jab starts on its first update. */
 update(MF_COMBAT_JAB(0));assert(started_song[5][5]==2);
 for(i=0;i<60;i++){update(0);}n=stopped_port[5];update(MF_COMBAT_JAB(0));assert(started_song[5][5]==3 && stopped_port[5]==n);
 /* Rapid repeats interrupt only their own previous sample. */
 for(i=0;i<12;i++){int j;update(MF_COMBAT_JAB(0)|MF_COMBAT_JAB(1));update(0);for(j=0;j<10;j++)update(0);}
 assert(started_song[5][5]>=14 && started_song[6][5]>=12);
 /* A same-tick immediate hit takes precedence over starting a whoosh. */
 for(i=0;i<60;i++){update(0);}n=started_song[5][5];update(MF_COMBAT_JAB(0)|MF_COMBAT_CONNECT(0));assert(started_song[5][5]==n && started_song[5][6]>=2);
 fail_pause=6;mf_music_update(1,1,0,++clock_now);assert(!paused_state && pause_target==1);
 n=paused_port[5];fail_pause=-1;mf_music_update(1,1,0,++clock_now);assert(paused_state && paused_port[5]==n);
 mf_music_update(1,0,0,++clock_now);assert(!paused_state && resumed_port[5] && resumed_port[6]);
 update(MF_TORCH_IGNITE|MF_TORCH_HISS|MF_JUMP_SOUND|MF_WORLD_IMPACT|MF_COMBAT_DESTROY(0));
 assert(started_song[1][3] && started_song[2][1] && started_song[3][2] && started_song[4][4]);
 n=started_song[4][4];update(0);assert(!torch_playing);for(i=0;i<2;i++){update(MF_TORCH_HISS);}assert(started_song[4][4]==n);update(MF_TORCH_HISS);assert(started_song[4][4]==n+1);
 /* Incoming and outgoing nonlethal hits share the native sample dispatcher. */
 for(i=0;i<60;i++)update(0);
 update(MF_COMBAT_NONKILL(0)|MF_COMBAT_NONKILL(1));assert(started_song[5][0] && started_song[6][0]);
 n=started_song[5][0];update(MF_COMBAT_NONKILL(0)|MF_COMBAT_HURT(0));update(0);assert(started_song[5][0]==n+1);
 update(MF_COMBAT_CONNECT(0));update(0);assert(combat[0].playing && combat[0].ends_at>clock_now);
 for(i=0;i<60;i++)update(0);
 n=started_song[3][2];update(MF_WORLD_IMPACT|MF_COMBAT_DESTROY(0)|MF_COMBAT_CONNECT(0));
 assert(started_song[3][2]==n+1 && combat[0].playing);
 assert(!started_song[3][0] && !started_song[3][6]);
 assert(started_song[0][0]==1);
 puts("PASS custom transport: independent ports, collision precedence, acknowledged stop/release guard, rejection retries, no catch-up bypass, misses/rapid repeats, two-player isolation, pause and unchanged unrelated sounds");return 0;}
