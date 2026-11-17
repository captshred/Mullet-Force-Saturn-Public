/* Native test image only: real approved mf_music_update/SDK/driver, no gameplay.
   Exercise every existing SFX port while the complete retained song runs. */
#include <jo/jo.h>
#include "game.h"
#include "music.h"
static volatile unsigned clock_tick;
static void tick(void){clock_tick++;}
static void update(void)
{
 unsigned now=clock_tick,phase;int events=0;
 if(now<240)return; /* Driver initialization completes before stress playback. */
 phase=(now-240)%60;
 events|=MF_TORCH_HISS;
 if(phase==0)events|=MF_TORCH_IGNITE|MF_JUMP_SOUND|MF_WORLD_IMPACT|MF_COMBAT_JAB(0)|MF_COMBAT_BAT(1);
 if(phase==15)events|=MF_COMBAT_NONKILL(0)|MF_COMBAT_CONNECT(1);
 if(phase==30)events|=MF_WORLD_IMPACT|MF_COMBAT_BAT(0)|MF_COMBAT_JAB(1);
 if(phase==45)events|=MF_COMBAT_CONNECT(0)|MF_COMBAT_NONKILL(1);
 mf_music_update(1,0,events,now);
}
void jo_main(void)
{
 jo_core_init(JO_COLOR_RGB(0,0,0));
 if(!mf_music_init()){jo_print(1,1,"AUDIO STRESS INIT FAILED");return;}
 jo_print(1,1,"LEVEL1 NATIVE AUDIO STRESS");
 jo_core_add_vblank_callback(tick);jo_core_add_callback(update);jo_core_run();
}
