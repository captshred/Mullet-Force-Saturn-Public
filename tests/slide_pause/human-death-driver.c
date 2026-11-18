/* Diagnostic image only: production music.c, unchanged driver and runtime banks. */
#include <jo/jo.h>
#include "game.h"
#include "music.h"
static volatile unsigned clock_tick;
static void tick(void){clock_tick++;}
static void update(void){unsigned now=clock_tick;int events=0,paused=now>=2000 && now<15000;if(now<240)return;
 if(now>=400 && now<1800 && now%160==80)events=MF_COMBAT_HUMAN_DEATH(0)|MF_COMBAT_CONNECT(0);
 if(now>=400 && now<1800 && now%160==120)events=MF_COMBAT_NONKILL(1)|MF_COMBAT_HEAVY_HIT(1);
 if(now>=400 && now<1800 && now%160==0)events=MF_COMBAT_JAB(0)|MF_WORLD_IMPACT;
 if(now>=400 && now<1800 && now%160==40)events=MF_COMBAT_NONKILL(0);
 if(now>=15200 && now<16000){if(now%90==0)events|=MF_COMBAT_HUMAN_DEATH(0)|MF_COMBAT_CONNECT(0)|MF_COMBAT_NONKILL(0)|MF_COMBAT_HEAVY_HIT(0);if(now%90==1)events|=MF_COMBAT_NONKILL(1)|MF_COMBAT_HEAVY_HIT(1);if(now%120==15)events|=MF_WORLD_IMPACT;events|=MF_TORCH_HISS;}
 mf_music_update(1,paused,events,now);}
void jo_main(void){jo_core_init(JO_COLOR_RGB(0,0,0));if(!mf_music_init()){jo_print(1,1,"AUDIO INIT FAILED");return;}jo_print(1,1,"HUMAN DEATH SHARED IMPACT TEST");jo_core_add_vblank_callback(tick);jo_core_add_callback(update);jo_core_run();}
