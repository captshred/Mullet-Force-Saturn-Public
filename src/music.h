#ifndef MF_MUSIC_H
#define MF_MUSIC_H
int mf_music_init(void);
void mf_music_update(int started,int paused,int events,unsigned int vblank);
int mf_music_ready(void);
int mf_music_protected(void);
#if MF_BRUCE_RUNTIME && MF_VEHICLE_AMBUSH
enum { MF_BRUCE_BANK_WAIT, MF_BRUCE_BANK_READY, MF_BRUCE_BANK_TRANSFERRED };
int mf_music_bruce_bank(int requested,unsigned int now);
int mf_music_bruce_exit(void);
#endif
#endif
