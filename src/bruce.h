#ifndef MF_BRUCE_H
#define MF_BRUCE_H
#include "game.h"

#if MF_BRUCE_RUNTIME
enum {
    MF_BRUCE_ENTRANCE, MF_BRUCE_ENTRANCE_IMPACT, MF_BRUCE_RECOVERY,
    MF_BRUCE_READY, MF_BRUCE_PUNCH, MF_BRUCE_CHARGE, MF_BRUCE_SLAM,
    MF_BRUCE_HURT, MF_BRUCE_FALL, MF_BRUCE_DOWN, MF_BRUCE_RISE, MF_BRUCE_DEFEATED,
    MF_BRUCE_COUNTER, MF_BRUCE_COUNTER_RECOVERY
};
enum { MF_BRUCE_LOT_RETURN = MF_WORLD_SLOPE_END + 80, MF_BRUCE_LOT_FIRST = 2758,
       MF_BRUCE_ARCADE_DOORS = 3095, MF_BRUCE_MAX_HP = 75 };
enum {
    MF_BRUCE_PRESSURE_HITS = 3, MF_BRUCE_PRESSURE_WINDOW = 72,
    MF_BRUCE_COUNTER_WINDUP = 20, MF_BRUCE_COUNTER_AIR = 26,
    MF_BRUCE_COUNTER_RECOVERY_TICKS = 24, MF_BRUCE_COUNTER_COOLDOWN = 150
};

int mf_bruce_approach(mf_bruce *bruce, const mf_game *game);
void mf_bruce_step(mf_bruce *bruce, const mf_game *game);
int mf_bruce_vulnerable(const mf_bruce *bruce);
void mf_bruce_receive(mf_bruce *bruce, int damage, int bat, int direction);
int mf_bruce_strike(const mf_bruce *bruce, const mf_player *player);
int mf_bruce_pose(const mf_bruce *bruce);

#if defined(MF_BRUCE_SATURN) && MF_ENEMY_SPRITE_BANKS
#include "enemy_sprite_bank.h"
extern const mf_enemy_bank_spec mf_bruce_bank_spec;
void mf_bruce_use_palette(jo_palette *palette);
void mf_bruce_restore_palette(void);
void mf_bruce_draw(const mf_bruce *bruce, int x, int ground, int depth);
#endif
#endif
#endif
