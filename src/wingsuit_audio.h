#ifndef MF_WS_AUDIO_H
#define MF_WS_AUDIO_H
#define MF_WS_EXPLOSION_MIN_SPACING 5u
#define MF_WS_EXPLOSION_PENDING_MAX 8u
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
enum { MF_WS_SFX_FLAME=1,MF_WS_SFX_SHOT,MF_WS_SFX_EXPLOSION };
/* Cached physical EG activity. owner[slot]=0..7, or 255 if not a live SFX.
   free_slots counts globally reusable allocator entries; held ended keys may
   be inactive without being globally reusable. No private driver writes. */
typedef struct {
    unsigned flame,shot,explosion,total,free_slots,owner[32];
    unsigned losses,replacements,lost_kind,lost_control,lost_age,other_note_on,free_at_loss;
    unsigned dropped_shots,dropped_explosions,snapshot;
} mf_ws_mixer_diagnostic;
const mf_ws_mixer_diagnostic *mf_ws_audio_mixer_diagnostics(void);
unsigned mf_ws_audio_fault(void);
#endif
