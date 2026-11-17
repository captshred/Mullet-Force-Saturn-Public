/* Separate native test image. Real Level2 driver/scheduler; no game RAM writes. */
#include <jo/jo.h>
#include "wingsuit_audio.h"
#ifndef MF_WRISTBREAKER_SFX_STRESS
#define MF_WRISTBREAKER_SFX_STRESS 1
#endif
static volatile unsigned clock_tick;
static void tick(void){++clock_tick;}
static char *read_bank(const char *name,int expected){int size;char *b=jo_fs_read_file(name,&size);if(!b)return 0;if(size!=expected){jo_free(b);return 0;}return b;}
static void update(void){unsigned now=clock_tick;if(now>240 && MF_WRISTBREAKER_SFX_STRESS){if(now%5==0)mf_ws_audio_events(8,3);if(now%7==0)mf_ws_audio_hits(2);}if(now>240 && !MF_WRISTBREAKER_SFX_STRESS)mf_ws_audio_events(0,0);mf_ws_audio_step(now,now>240 && MF_WRISTBREAKER_SFX_STRESS?3:0);}
void jo_main(void){jo_core_init(JO_COLOR_RGB(0,0,0));mf_ws_audio_trace_clock(&clock_tick);if(!mf_ws_audio_load(read_bank,0)){jo_print(1,1,"AUDIO LOAD FAILED");return;}jo_print(1,1,"WRISTBREAKER NATIVE STRESS");jo_core_add_vblank_callback(tick);jo_core_add_callback(update);jo_core_run();}
