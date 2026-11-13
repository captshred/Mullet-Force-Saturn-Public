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
#endif
