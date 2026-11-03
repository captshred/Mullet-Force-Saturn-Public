#ifndef MF_CORPORATE_ANIMATION_H
#define MF_CORPORATE_ANIMATION_H
#include "game.h"
#include <jo/jo.h>
int mf_corporate_load(jo_palette *palette);
void mf_corporate_step(const mf_game *g);
int mf_corporate_pose(const mf_game *g,int actor);
/* Caller owns palette and horizontal-flip state, as for legacy enemies. */
int mf_corporate_draw(const mf_game *g,int actor,int x,int ground,int depth);
#endif
