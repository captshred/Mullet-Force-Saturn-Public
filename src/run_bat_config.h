#ifndef MF_RUN_BAT_CONFIG_H
#define MF_RUN_BAT_CONFIG_H
#ifndef MF_RUN_BAT
#define MF_RUN_BAT 0
#endif
#if MF_RUN_BAT && !MF_DASH_ENABLED
#error Running bat requires dash enabled
#endif
/* Opt-in experiment: historical profiles remain available as controls. */
#ifndef MF_FAST_RUNNING_BAT
#define MF_FAST_RUNNING_BAT 0
#endif
#if MF_FAST_RUNNING_BAT && !MF_RUN_BAT
#error Fast horizontal bat requires the running bat system
#endif
#define MF_BAT_RUNNING 2 /* p->bat discriminator; player/game ABI is unchanged. */
#define MF_FAST_BAT_ACTIVE_FIRST 4
#define MF_FAST_BAT_ACTIVE_LAST 7
#define MF_FAST_BAT_RECOVERY_FIRST 9
#define MF_FAST_BAT_TOTAL_TICKS 12
#define MF_RUN_FRAME_HOLD 6
#define MF_RUNNING_BAT_CARRY_TICKS 8
#define MF_RUNNING_BAT_SPEED (390*17/10)
#endif
