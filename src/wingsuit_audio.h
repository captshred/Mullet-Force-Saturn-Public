#ifndef MF_WS_AUDIO_H
#define MF_WS_AUDIO_H
typedef char *(*mf_ws_audio_reader)(const char *,int);
enum {
    MF_WS_AUDIO_MAP_READ=1,MF_WS_AUDIO_SOUND_OFF,MF_WS_AUDIO_SND_INIT,
    MF_WS_AUDIO_MAP_CHANGE,MF_WS_AUDIO_SGL_INIT,MF_WS_AUDIO_SEQ_UPLOAD,
    MF_WS_AUDIO_TON_UPLOAD,MF_WS_AUDIO_CPU_RESTART,MF_WS_AUDIO_FLUSH,
    MF_WS_AUDIO_DSP_STOP,MF_WS_AUDIO_CDDA_LEVEL,MF_WS_AUDIO_TOTAL_VOLUME
};
typedef struct {
    unsigned stage,completed;
    const char *operation;
    int has_status,expected,actual;
} mf_ws_audio_diagnostic;
typedef void (*mf_ws_audio_progress)(const mf_ws_audio_diagnostic *);
int mf_ws_audio_load(mf_ws_audio_reader,mf_ws_audio_progress);
const mf_ws_audio_diagnostic *mf_ws_audio_diagnostics(void);
void mf_ws_audio_events(int explosions,unsigned shots);
void mf_ws_audio_step(unsigned now,unsigned focused);
unsigned mf_ws_audio_fault(void);
#endif
