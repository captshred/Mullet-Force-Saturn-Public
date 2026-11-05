#ifndef MF_WINGSUIT_H
#define MF_WINGSUIT_H
#include "input.h"
#define MF_WS_PLAYERS 2
#define MF_WS_SHOTS 32
#define MF_WS_HOSTILE 16
#define MF_WS_HOSTILE_SPEED 768 /* 3 pixels/tick in 24.8. */
#define MF_WS_ENEMIES 8
#define MF_WS_FIRE_TICKS 7 /* Mobile fan minimum repeat interval. */
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
/* Coordinates are centers in 24.8 screen pixels; active area x=48..271. */
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
    unsigned ticks,wave; int spawn,paused,game_over,scroll;
} mf_wingsuit;
int mf_ws_beam_active(const mf_wingsuit *,int);
void mf_ws_init(mf_wingsuit *,int coop);
void mf_ws_step(mf_wingsuit *,const unsigned held[2],const unsigned pressed[2],unsigned connected);
#endif
