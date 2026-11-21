#ifndef MF_BRUCE_H
#define MF_BRUCE_H
#include "game.h"

#if MF_BRUCE_RUNTIME
typedef struct {
    int x, y, facing, target, retarget, moving, animation, active, approach;
} mf_bruce;

int mf_bruce_approach(mf_bruce *bruce, const mf_game *game);
void mf_bruce_step(mf_bruce *bruce, const mf_game *game);
int mf_bruce_pose(const mf_bruce *bruce);

#ifdef MF_BRUCE_SATURN
#include "enemy_sprite_bank.h"
extern const mf_enemy_bank_spec mf_bruce_bank_spec;
void mf_bruce_use_palette(jo_palette *palette);
void mf_bruce_restore_palette(void);
void mf_bruce_draw(const mf_bruce *bruce, int x, int ground, int depth);
#endif
#endif
#endif
