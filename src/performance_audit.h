#ifndef MF_PERFORMANCE_AUDIT_H
#define MF_PERFORMANCE_AUDIT_H

enum {
    MF_PERF_CPU, MF_PERF_LOGIC, MF_PERF_AI, MF_PERF_RENDER, MF_PERF_AUDIO,
    MF_PERF_BANK, MF_PERF_FENCE, MF_PERF_INSTALL, MF_PERF_STREAM,
    MF_PERF_DECODE, MF_PERF_TILE_UPLOAD, MF_PERF_SECTIONS
};
enum { MF_PERF_P2=1, MF_PERF_TORCH=2, MF_PERF_VEHICLE=4, MF_PERF_BRUCE=8, MF_PERF_DOWNHILL=16,
    MF_PERF_PLAYING=32, MF_PERF_PAUSED=64 };

#if defined(MF_PERFORMANCE_AUDIT) && MF_PERFORMANCE_AUDIT
typedef struct {
    unsigned publishing, sequence, blank, gap, missed, same_blank, gap_ticks;
    unsigned clocks_per_tick, hz, blank_ticks, timer_faults;
    unsigned edsr_start, edsr_end, edsr_blank, busy_blanks;
    unsigned flags, camera, enemies, game_ticks, bank_state, bank_kind, bank_bytes;
    unsigned tile_bytes, map_bytes, decoded_blocks;
    unsigned ticks[MF_PERF_SECTIONS];
} mf_perf_sample;

extern volatile mf_perf_sample mf_perf_latest;
void mf_perf_init(void);
unsigned mf_perf_time(void);
void mf_perf_add(unsigned section,unsigned start);
void mf_perf_vblank(void);
void mf_perf_begin(void);
void mf_perf_end(unsigned flags,unsigned camera,unsigned enemies,unsigned game_ticks);
void mf_perf_overlay(int y_held,int visible);
void mf_perf_bank(unsigned state,unsigned kind,unsigned bytes);
void mf_perf_stream(unsigned tile_bytes,unsigned map_bytes,unsigned decoded_blocks);
#define MF_PERF_BEGIN(name) unsigned name=mf_perf_time()
#define MF_PERF_END(section,name) mf_perf_add(section,name)
#else
#define MF_PERF_BEGIN(name) ((void)0)
#define MF_PERF_END(section,name) ((void)0)
#define mf_perf_vblank() ((void)0)
#define mf_perf_bank(state,kind,bytes) ((void)0)
#define mf_perf_stream(tiles,map,blocks) ((void)0)
#endif
#endif
