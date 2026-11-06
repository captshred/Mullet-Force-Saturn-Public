#ifndef MF_WINGSUIT_H
#define MF_WINGSUIT_H
#include "input.h"
#define MF_WS_PLAYERS 2
#define MF_WS_SHOTS 32
#define MF_WS_HOSTILE 16
#define MF_WS_HOSTILE_SPEED 768 /* 3 pixels/tick in 24.8. */
#define MF_WS_ENEMIES 8
#define MF_WS_FIRE_TICKS 7 /* Tap minimum repeat interval. */
#define MF_WS_FOCUS_TICKS 20 /* 0.33 s at 60 Hz; taps remain mobile. */
#define MF_WS_MOVE_SPEED 640
#define MF_WS_DIAGONAL_SPEED 452
#define MF_WS_FOCUS_PERCENT 65
#define MF_WS_BEAM_SEGMENT_HEIGHT 32
#define MF_WS_BEAM_ORIGIN_HEIGHT 16
#define MF_WS_BEAM_TOP 0
#define MF_WS_BEAM_EMITTER 15
#define MF_WS_BEAM_HALF_WIDTH 11
#define MF_WS_BEAM_MAX_SEGMENTS 7
#define MF_WS_BEAM_TICKS 6
#define MF_WS_SPAWN_TICKS 45
#define MF_WS_INVULNERABLE 120
#define MF_WS_SCALE 256
/* X is world space; Y retains the existing vertically scrolling stage model.
   Camera/dead-zone values are 24.8 except named pixel dimensions below. */
#define MF_WS_STAGE_WIDTH 512
#define MF_WS_VIEW_LEFT 48
#define MF_WS_VIEW_WIDTH 224
#define MF_WS_PLAYER_MARGIN 16
#define MF_WS_CAMERA_LEFT 50
#define MF_WS_CAMERA_RIGHT 174
#define MF_WS_CAMERA_SPEED (3*MF_WS_SCALE)
#define MF_WS_CAMERA_MAX ((MF_WS_STAGE_WIDTH-MF_WS_VIEW_WIDTH)*MF_WS_SCALE)
#define MF_WS_PLAYER_MIN (MF_WS_PLAYER_MARGIN*MF_WS_SCALE)
#define MF_WS_PLAYER_MAX ((MF_WS_STAGE_WIDTH-MF_WS_PLAYER_MARGIN)*MF_WS_SCALE)
typedef struct { int active,x,y,lives,invulnerable,respawn,cooldown,score,shot_hold; } mf_ws_player;
typedef struct { int active,x,y,owner,ttl,vx; } mf_ws_shot;
/* Hostile physics is a generic fixed velocity; only the drone emitter aims. */
typedef struct { int active,x,y,owner,ttl,vx,vy; } mf_ws_hostile_shot;
typedef struct { int active,x,y,age,explosion; } mf_ws_enemy;
typedef struct {
    mf_ws_player players[MF_WS_PLAYERS];
    mf_ws_shot shots[MF_WS_SHOTS];
    mf_ws_hostile_shot hostile[MF_WS_HOSTILE];
    mf_ws_enemy enemies[MF_WS_ENEMIES];
    int beam_wait[2],deaths;
    unsigned shots_fired;
    unsigned ticks,wave; int spawn,paused,game_over,scroll;
    int camera_x; /* Only horizontal camera state; no per-object screen copies. */
} mf_wingsuit;
int mf_ws_screen_x(const mf_wingsuit *,int world_x);
void mf_ws_camera_step(mf_wingsuit *);
int mf_ws_beam_active(const mf_wingsuit *,int);
void mf_ws_init(mf_wingsuit *,int coop);
void mf_ws_step(mf_wingsuit *,const unsigned held[2],const unsigned pressed[2],unsigned connected);
#endif
