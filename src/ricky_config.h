#ifndef MF_RICKY_CONFIG_H
#define MF_RICKY_CONFIG_H
#ifndef MF_RICKY_ENEMY
#define MF_RICKY_ENEMY 0
#endif
#if MF_RICKY_ENEMY && defined(MF_ENEMY_SPRITE_BANKS)
#if !MF_ENEMY_SPRITE_BANKS
#error Ricky requires the Phase 5 resident enemy suffix architecture
#endif
#endif
/* Jump-chain tuning: ticks are fixed 60 Hz simulation steps. */
#define MF_RICKY_JUMP_MIN 75
#define MF_RICKY_JUMP_MAX 125
#define MF_RICKY_JUMP_WINDUP 12
#define MF_RICKY_JUMP_AIR 24
#define MF_RICKY_JUMP_ACTIVE_FIRST 18
#define MF_RICKY_JUMP_ACTIVE_TICKS 5
#define MF_RICKY_JUMP_RECOVERY 18
#define MF_RICKY_JUMP_DAMAGE 1
#define MF_RICKY_JUMP_COOLDOWN 150
#define MF_RICKY_JUMP_LIFT 12
/* Reach is inside the redesigned 64px canvas (anchor X=28). */
#define MF_RICKY_JUMP_REACH 29
#define MF_RICKY_CHAIN_RANGE 82
#define MF_RICKY_ATTACK_LANE 12
#endif
