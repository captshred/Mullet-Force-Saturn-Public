#ifndef MF_WS_AUDIO_H
#define MF_WS_AUDIO_H
typedef char *(*mf_ws_audio_reader)(const char *,int);
int mf_ws_audio_load(mf_ws_audio_reader);
void mf_ws_audio_events(int count);
void mf_ws_audio_step(unsigned now);
#endif
