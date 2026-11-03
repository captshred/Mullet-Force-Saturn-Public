#ifndef MF_PLAYER_ANIMATION_H
#define MF_PLAYER_ANIMATION_H
#include "game.h"
/* Presentation only. Called once after each advanced simulation tick. */
void mf_player_animation_step(const mf_game *g);
int mf_player_animation_pose(const mf_game *g,int actor);
/* Returns zero when the caller must use the complete original renderer. */
int mf_player_animation_draw(const mf_game *g,int actor,int x,int ground,int depth);
#endif
