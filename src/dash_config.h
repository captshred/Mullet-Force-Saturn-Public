#ifndef MF_DASH_CONFIG_H
#define MF_DASH_CONFIG_H
/* Fixed60Hz input clock. Native review builds opt in; old configurations stay off. */
#ifndef MF_DASH_ENABLED
#define MF_DASH_ENABLED 0
#endif
#define MF_DASH_PRESET_A 15
#define MF_DASH_PRESET_B 17
#ifndef MF_DASH_PRESET
#define MF_DASH_PRESET MF_DASH_PRESET_B
#endif
#define MF_DASH_TAP_TICKS 12 /* Inclusive first-to-second press distance. */
#define MF_DASH_SPEED_NUM MF_DASH_PRESET
#define MF_DASH_SPEED_DEN 10 /* A=1.5x, B=1.7x of existing24.8 walk390. */
#define MF_DASH_ANIM_NUM 7
#define MF_DASH_ANIM_DEN 5 /* Exactly1.4x phase rate using integer fractions. */
#define MF_DASH_BASE_HOLD 10 /* Locked Timing B; does not change normal walk. */
#define MF_DASH_ANIM_CYCLE (3*MF_DASH_BASE_HOLD*MF_DASH_ANIM_DEN)
#if MF_DASH_PRESET != MF_DASH_PRESET_A && MF_DASH_PRESET != MF_DASH_PRESET_B
#error Invalid dash speed preset
#endif
#endif
