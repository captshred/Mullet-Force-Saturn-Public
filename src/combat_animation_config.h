#ifndef MF_COMBAT_ANIMATION_CONFIG_H
#define MF_COMBAT_ANIMATION_CONFIG_H
#ifndef MF_COMBAT_ANIMATION
#define MF_COMBAT_ANIMATION 0
#endif
#if MF_COMBAT_ANIMATION && (!MF_RUNNING_BAT_VISUALS || !MF_PLAYABLE_ANIMATION)
#error Combat key-pose prototype requires the approved running-bat visual configuration
#endif
#endif
