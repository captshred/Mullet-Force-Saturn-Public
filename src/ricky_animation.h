#ifndef MF_RICKY_ANIMATION_H
#define MF_RICKY_ANIMATION_H
#include "ricky_config.h"
#if MF_RICKY_ENEMY
#include "game.h"
#include "enemy_sprite_bank.h"
extern const mf_enemy_bank_spec mf_ricky_bank_spec;
/* Boot-only: base slot 2 and reclaimed legacy Chuck slot 3. */
int mf_ricky_palette(jo_palette *,jo_palette *);
int mf_ricky_pose(const mf_game *,int);
/* Explicit pose API also exposes jump and turn artwork without new movement mechanics. */
int mf_ricky_draw_pose(int pose,int facing,int x,int ground,int depth);
int mf_ricky_draw(const mf_game *,int,int,int,int);
#endif
#endif
