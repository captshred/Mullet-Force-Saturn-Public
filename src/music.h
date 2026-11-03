#ifndef MF_MUSIC_H
#define MF_MUSIC_H
int mf_music_init(void);
void mf_music_update(int started,int paused,int events,unsigned int vblank);
int mf_music_ready(void);
#endif
