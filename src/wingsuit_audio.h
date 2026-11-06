#ifndef MF_WS_AUDIO_H
#define MF_WS_AUDIO_H
typedef char *(*mf_ws_audio_reader)(const char *,int);
enum {
    MF_WS_AUDIO_MAP_READ=1,MF_WS_AUDIO_SOUND_OFF,MF_WS_AUDIO_SND_INIT,
    MF_WS_AUDIO_MAP_CHANGE,MF_WS_AUDIO_SGL_INIT,MF_WS_AUDIO_SEQ_UPLOAD,
    MF_WS_AUDIO_TON_UPLOAD,MF_WS_AUDIO_CPU_RESTART,MF_WS_AUDIO_FLUSH,
    MF_WS_AUDIO_DSP_STOP,MF_WS_AUDIO_CDDA_LEVEL,MF_WS_AUDIO_TOTAL_VOLUME,
    MF_WS_AUDIO_DRIVER_READY,MF_WS_AUDIO_MAP_READY,MF_WS_AUDIO_FLAME_READY
};
typedef struct {
    unsigned stage,completed;
    const char *operation;
    int has_status,expected,actual;
} mf_ws_audio_diagnostic;
typedef void (*mf_ws_audio_progress)(const mf_ws_audio_diagnostic *);
int mf_ws_audio_load(mf_ws_audio_reader,mf_ws_audio_progress);
const mf_ws_audio_diagnostic *mf_ws_audio_diagnostics(void);
int mf_ws_audio_ready(void); /* -1: startup failure, 0: pending, 1: play may begin. */
void mf_ws_audio_events(int explosions,unsigned shots);
void mf_ws_audio_step(unsigned now,unsigned focused);
enum {
    MF_WS_FLAME_OFF,MF_WS_FLAME_REQUESTED,MF_WS_FLAME_ATTACK,
    MF_WS_FLAME_SUSTAIN,MF_WS_FLAME_STOPPED,MF_WS_FLAME_MISMATCH,
    MF_WS_FLAME_RELEASING
};
/* ATTACK/SUSTAIN use the selected split tone plus a live driver EG observation; they do
   not claim to measure the hardware waveform cursor or audible output. */
typedef struct {
    unsigned state,requested,age,slots,active_slots;
    unsigned control,sa,lsa,lea,eg;
} mf_ws_flame_diagnostic;
const mf_ws_flame_diagnostic *mf_ws_audio_flame_diagnostics(unsigned player);
unsigned mf_ws_audio_fault(void);
#endif
