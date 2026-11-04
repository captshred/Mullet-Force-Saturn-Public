#ifndef MF_ARCADE_FX_CONFIG_H
#define MF_ARCADE_FX_CONFIG_H
#ifndef MF_ARCADE_FX
#define MF_ARCADE_FX 0
#endif
/* BU01 is obsolete only in the complete, successfully loaded HQ profile. */
#if MF_ARCADE_FX && !(MF_PLAYABLE_ANIMATION && MF_ANIMATION_PREVIEW && MF_ORIGINAL_THREE_WALK && MF_HQ_TORCH && MF_HQ_JUMP && MF_PLAYER_HURT && MF_PLAYER_DEATH && MF_CP_HQ_COMBAT && MF_PUNCH_COMBO && MF_FAST_RUNNING_BAT && MF_LIVE_CITY_PARALLAX && MF_CITY_CLEANUP)
#error Arcade FX requires the complete HQ gameplay/parallax profile
#endif
#define MF_FX_SAVED_BYTES (MF_ARCADE_FX ? 544u : 0u)
#define MF_FX_TEXTURE_BYTES 452800u
#define MF_FX_DEFINITIONS 255
#endif
