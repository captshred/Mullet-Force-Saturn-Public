#ifndef MF_JAB_CONFIG_H
#define MF_JAB_CONFIG_H
#ifndef MF_JAB_COHESION
#define MF_JAB_COHESION 0
#endif
#ifndef MF_PUNCH_COMBO
#define MF_PUNCH_COMBO 0
#endif
#define MF_COMBO_TIMEOUT_TICKS 45
#define MF_CROSS_RECOVERY_EXTRA 4
#define MF_CROSS_TOTAL_TICKS (24+MF_CROSS_RECOVERY_EXTRA)
#if MF_PUNCH_COMBO && (!MF_JAB_COHESION || !MF_FAST_RUNNING_BAT)
#error Punch combo requires the latest responsive jab / fast-bat profile
#endif
#ifndef MF_JAB_BUFFER_TICKS
#define MF_JAB_BUFFER_TICKS 6
#endif
/* Counter1 is the activation tick;13 means12 elapsed simulation ticks. */
#ifndef MF_JAB_REPEAT_COUNTER
#define MF_JAB_REPEAT_COUNTER 13
#endif
#if MF_JAB_BUFFER_TICKS<1 || MF_JAB_BUFFER_TICKS>24 || MF_JAB_REPEAT_COUNTER<=10 || MF_JAB_REPEAT_COUNTER>24
#error Invalid jab repeat tuning
#endif
#endif
