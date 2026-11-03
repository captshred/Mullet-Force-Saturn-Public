#ifndef MF_ANIMATION_PREVIEW_H
#define MF_ANIMATION_PREVIEW_H
/* PLAYERHURT BEGIN */
#if MF_PLAYER_HURT
#include "game.h"
int mf_player_hurt_load(void);
int mf_player_hurt_phase(const mf_game *,int);
int mf_player_hurt_draw(const mf_game *,int,int,int,int);
#endif
/* PLAYERHURT END */
/* PLAYERDEATH BEGIN */
#if MF_PLAYER_DEATH
int mf_player_death_load(void);
int mf_player_death_phase(const mf_game *,int);
int mf_player_death_draw(const mf_game *,int,int,int,int);
#endif
/* PLAYERDEATH END */
/* Shared resident textures. Gallery clock and gameplay clocks are independent. */
int mf_animation_draw_actor(int actor,int frame,int x,int ground,int facing,int depth);
int mf_animation_load(jo_palette *palette,const int idle_ids[2][3]);
unsigned mf_animation_texture_bytes(void);
int mf_animation_active(void);
int mf_animation_toggle(void);
void mf_animation_leave(void);
void mf_animation_update(unsigned held,unsigned pressed,unsigned ticks);
void mf_animation_draw(const int street[5],int street_palette_id);
void mf_running_bat_metal_draw(int actor,int frame,int x,int ground,int facing,int depth);
#if MF_PUNCH_COMBO
int mf_cross_load(void);
#endif
#if MF_COMBAT_ANIMATION
#include "game.h"
int mf_combat_prototype_draw(const mf_game *g,int actor,int x,int ground,int depth);
#endif
#if MF_HQ_TORCH
int mf_hq_torch_load(int enemy_palette);
#if MF_HQ_JUMP
int mf_hq_jump_load(void);
int mf_hq_jump_draw(const mf_game *,int,int,int,int);
#endif
int mf_hq_torch_draw(const mf_game *,int,int,int,int);
#endif
#endif
