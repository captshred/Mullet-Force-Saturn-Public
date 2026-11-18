/* Diagnostic native image: production transport, fixed real-SDK request schedule. */
#include <jo/jo.h>
#include "game.h"
#include "music.h"
static volatile unsigned clock_tick;
static void tick(void){clock_tick++;}
static void update(void){unsigned now=clock_tick;int events;if(now<240)return;
 events=MF_COMBAT_JAB(0)|MF_COMBAT_BAT(1)|MF_WORLD_IMPACT|MF_JUMP_SOUND|MF_TORCH_IGNITE|MF_TORCH_HISS;
 if(now%97==0)events|=MF_COMBAT_HUMAN_DEATH(0)|MF_COMBAT_CONNECT(0);
 if(now%97==1)events|=MF_COMBAT_HUMAN_DEATH(1)|MF_COMBAT_CONNECT(1);
 mf_music_update(1,0,events,now);
}
void jo_main(void){jo_core_init(JO_COLOR_RGB(0,0,0));if(!mf_music_init()){jo_print(1,1,"AUDIO INIT FAILED");return;}jo_print(1,1,"UGH PROTECTION NATIVE TEST");jo_core_add_vblank_callback(tick);jo_core_add_callback(update);jo_core_run();}
