/* Separate native audio test: sustained opening guitar plus real explosion,
   full-loop pause with held event requests, then rapid pause/resume. */
#include <jo/jo.h>
#include "game.h"
#include "music.h"
static volatile unsigned clock_tick;
static void tick(void){clock_tick++;}
static void update(void){unsigned now=clock_tick;int paused,events=0;if(now<240)return;
 paused=now>=315 && now<15000;
 if(now>=15050 && now<15150)paused=(now/10)&1;
 if(now==300 || (now>315 && now<15000))events=MF_WORLD_IMPACT|MF_COMBAT_JAB(0)|MF_TORCH_HISS;
 mf_music_update(1,paused,events,now);}
void jo_main(void){jo_core_init(JO_COLOR_RGB(0,0,0));if(!mf_music_init()){jo_print(1,1,"AUDIO INIT FAILED");return;}jo_print(1,1,"LEVEL1 PAUSE CONTINUITY TEST");jo_core_add_vblank_callback(tick);jo_core_add_callback(update);jo_core_run();}
