/* Diagnostic native image: production transport, fixed real-SDK request schedule. */
#include <jo/jo.h>
#include "game.h"
#include "music.h"
static volatile unsigned clock_tick;
static void tick(void){clock_tick++;}
static void update(void){unsigned now=clock_tick;int events=0,paused=now>=2200 && now<15000;if(now<240)return;
 /* Isolated complete one-shots before the protected stress episode. */
 if(now>=300 && now<1500 && now%140==20){unsigned song=(now-300)/140;events=song==0?MF_COMBAT_NONKILL(0):song==1?MF_JUMP_SOUND:song==2?MF_WORLD_IMPACT:song==3?MF_TORCH_IGNITE:song==4?MF_TORCH_HISS:song==5?MF_COMBAT_JAB(0):song==6?MF_COMBAT_NONKILL(0)|MF_COMBAT_HEAVY_HIT(0):MF_COMBAT_BAT(0);}
 if(now==1550)events=MF_COMBAT_BAT(1)|MF_TORCH_HISS|MF_WORLD_IMPACT;
 if(now>=1550 && now<2000)events|=MF_TORCH_HISS;
 if(now==1560 || now==1800 || now==2220)events|=MF_COMBAT_HUMAN_DEATH(0)|MF_COMBAT_CONNECT(0);
 if((now>1560 && now<1720)||(now>1800 && now<1960)||(now>2220 && now<2400))events|=MF_COMBAT_JAB(0)|MF_COMBAT_NONKILL(1)|MF_COMBAT_HEAVY_HIT(1)|MF_COMBAT_BAT(1)|MF_WORLD_IMPACT|MF_JUMP_SOUND|MF_TORCH_IGNITE|MF_COMBAT_HUMAN_DEATH(1);
 /* No new SFX during stable long pause, but UGH deliberately completes in pause. */
 if(now>=15000 && now<15800){if(now%110==0)events|=MF_COMBAT_HUMAN_DEATH(0)|MF_COMBAT_CONNECT(0);else events|=MF_COMBAT_JAB(0)|MF_COMBAT_BAT(1)|MF_WORLD_IMPACT|MF_JUMP_SOUND;}
 mf_music_update(1,paused,events,now);
 if(now%16==0)jo_printf(1,3,"CLOCK%u PROTECTED%d",now,mf_music_protected());}
void jo_main(void){jo_core_init(JO_COLOR_RGB(0,0,0));if(!mf_music_init()){jo_print(1,1,"AUDIO INIT FAILED");return;}jo_print(1,1,"UGH PROTECTION NATIVE TEST");jo_core_add_vblank_callback(tick);jo_core_add_callback(update);jo_core_run();}
