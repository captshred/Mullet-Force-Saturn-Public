#ifndef MF_WINGSUIT_H
#define MF_WINGSUIT_H
#include "input.h"
#define MF_WS_PLAYERS 2
#define MF_WS_SHOTS 32
#define MF_WS_HOSTILE 16
#define MF_WS_ENEMIES 8
#define MF_WS_FIRE_TICKS 7
#define MF_WS_SPAWN_TICKS 45
#define MF_WS_INVULNERABLE 120
#define MF_WS_SCALE 256
/* Coordinates are centers in 24.8 screen pixels; active area x=48..271. */
typedef struct { int active,x,y,lives,invulnerable,respawn,cooldown,score; } mf_ws_player;
typedef struct { int active,x,y,owner,ttl; } mf_ws_shot;
typedef struct { int active,x,y,age,explosion; } mf_ws_enemy;
typedef struct {
    mf_ws_player players[MF_WS_PLAYERS];
    mf_ws_shot shots[MF_WS_SHOTS],hostile[MF_WS_HOSTILE];
    mf_ws_enemy enemies[MF_WS_ENEMIES];
    unsigned ticks,wave; int spawn,paused,game_over,scroll;
} mf_wingsuit;
void mf_ws_init(mf_wingsuit *,int coop);
void mf_ws_step(mf_wingsuit *,const unsigned held[2],const unsigned pressed[2],unsigned connected);
#endif
