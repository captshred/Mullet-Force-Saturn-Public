#ifndef MF_ARCADE_FX_CONFIG_H
#define MF_ARCADE_FX_CONFIG_H
#ifndef MF_ARCADE_FX
#define MF_ARCADE_FX 0
#endif
/* BU01 is obsolete only in the complete, successfully loaded HQ profile. */
#if MF_ARCADE_FX && !(MF_PLAYABLE_ANIMATION && MF_ANIMATION_PREVIEW && MF_ORIGINAL_THREE_WALK && MF_HQ_TORCH && MF_HQ_JUMP && MF_PLAYER_HURT && MF_PLAYER_DEATH && MF_CP_HQ_COMBAT && MF_PUNCH_COMBO && MF_FAST_RUNNING_BAT && MF_LIVE_CITY_PARALLAX && MF_CITY_CLEANUP)
#error Arcade FX requires the complete HQ gameplay/parallax profile
#endif
/* Production stage-default only; historical profiles retain the old banks. */
#ifndef MF_LEGACY_SPRITE_CLEANUP
#define MF_LEGACY_SPRITE_CLEANUP 0
#endif
#if MF_LEGACY_SPRITE_CLEANUP && !MF_ARCADE_FX
#error Legacy sprite cleanup requires the approved complete fast-bat profile
#endif
/* Phase 2 is safe only with every replacement path enabled. */
#ifndef MF_LEGACY_SPRITE_PHASE2
#define MF_LEGACY_SPRITE_PHASE2 0
#endif
#if MF_LEGACY_SPRITE_PHASE2 && !(MF_LEGACY_SPRITE_CLEANUP && MF_RUN_BAT && MF_RUNNING_BAT_VISUALS && MF_COMBAT_ANIMATION && MF_ATTACK_SEQUENCE && MF_JAB_COHESION)
#error Phase 2 requires the approved HQ fast-bat, jab and movement paths
#endif
/* Share identical idle/combat feet only in the complete production profile. */
#ifndef MF_DUPLICATE_TEXTURE_CLEANUP
#define MF_DUPLICATE_TEXTURE_CLEANUP 0
#endif
#if MF_DUPLICATE_TEXTURE_CLEANUP && !MF_LEGACY_SPRITE_PHASE2
#error Duplicate cleanup requires the Phase 2 production profile
#endif
/* RGB555 panel rows are horizontally constant; use one minimum-width strip. */
#ifndef MF_HUD_PANEL_MEMORY
#define MF_HUD_PANEL_MEMORY 0
#endif
#if MF_HUD_PANEL_MEMORY && !MF_DUPLICATE_TEXTURE_CLEANUP
#error HUD panel optimization requires the complete Phase 3 profile
#endif
#define MF_HUD_PANEL_WIDTH (MF_HUD_PANEL_MEMORY ? 8 : 256)
#define MF_HUD_PANEL_SAVED_BYTES (MF_HUD_PANEL_MEMORY ? 19840u : 0u)
#define MF_DUPLICATE_SAVED_BYTES (MF_DUPLICATE_TEXTURE_CLEANUP ? 2016u : 0u)
#define MF_LEGACY_PLAYER_SAVED_BYTES (MF_LEGACY_SPRITE_PHASE2 ? 70688u : 0u)
#define MF_LEGACY_RBV_SAVED_BYTES (MF_LEGACY_SPRITE_PHASE2 ? 7360u : 0u)
#define MF_LEGACY_CA_SAVED_BYTES (MF_LEGACY_SPRITE_PHASE2 ? 29920u : 0u)
#define MF_LEGACY_PHASE2_BYTES (MF_LEGACY_PLAYER_SAVED_BYTES+MF_LEGACY_RBV_SAVED_BYTES+MF_LEGACY_CA_SAVED_BYTES)
#define MF_LEGACY_SAVED_BYTES (MF_LEGACY_SPRITE_CLEANUP ? 65952u : 0u)
#define MF_LEGACY_SAVED_DEFINITIONS (MF_LEGACY_SPRITE_CLEANUP ? 18 : 0)
#define MF_FX_SAVED_BYTES (MF_ARCADE_FX ? 544u : 0u)
#include "ricky_config.h"
#include "ricky_budget.h"
#define MF_RICKY_EXTRA_BYTES (MF_RICKY_ENEMY ? MF_RICKY_BYTES : 0u)
#define MF_RICKY_EXTRA_DEFS (MF_RICKY_ENEMY ? MF_RICKY_DEFS : 0)
#define MF_FX_TEXTURE_BYTES (MF_RICKY_EXTRA_BYTES+452800u-MF_LEGACY_SAVED_BYTES-MF_LEGACY_PHASE2_BYTES-MF_DUPLICATE_SAVED_BYTES-MF_HUD_PANEL_SAVED_BYTES)
#define MF_FX_DEFINITIONS (MF_RICKY_EXTRA_DEFS+255-MF_LEGACY_SAVED_DEFINITIONS-(MF_LEGACY_SPRITE_PHASE2 ? 83 : 0)-(MF_DUPLICATE_TEXTURE_CLEANUP ? 2 : 0))
#endif
