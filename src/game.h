#ifndef MF_GAME_H
#define MF_GAME_H
#include "input.h"
#include "combat_config.h"
#include "dash_config.h"
#include "run_bat_config.h"
#include "stage_config.h"
#include "ricky_config.h"
#include "world_config.h"
/* 24.8 ground coordinates, fixed 60 Hz NTSC simulation. */
#define MF_SCALE 256
#define MF_DRUMS 3
#define MF_PLAYERS 2
#define MF_ENEMIES 2
#define MF_BUCK_FRAMES 15
#define MF_BUCK_ANCHOR_Y 92
#define MF_ENEMY_FRAMES 12
#define MF_BAT_FRAMES 7
enum { MF_TORCH_OFF, MF_TORCH_EQUIP, MF_TORCH_FIRE, MF_TORCH_AWAY };
enum { MF_ENEMY_ABSENT, MF_ENEMY_IDLE, MF_ENEMY_WALK, MF_ENEMY_WINDUP, MF_ENEMY_ACTIVE, MF_ENEMY_RECOVER, MF_ENEMY_HURT, MF_ENEMY_DYING };
/* JAB BEGIN */
#include "jab_config.h"
#if MF_JAB_COHESION
typedef struct {int buffer;unsigned previous;} mf_jab_repeat_state;
#endif
/* JAB END */
typedef struct { int left,right,back,front,bottom,top; } mf_hitbox;
typedef struct { int x,y,vx,hp,facing,state,timer,walk,hit_done,grace,flash,target,target_lock,burn,burn_clock,fire_flash; } mf_enemy;
/* Per-player sound events; low legacy bits retain their gameplay meaning. */
#define MF_COMBAT_JAB(i) (1u << (5+3*(i)))
#define MF_COMBAT_BAT(i) (1u << (6+3*(i)))
#define MF_COMBAT_CONNECT(i) (1u << (7+3*(i)))
#define MF_WORLD_IMPACT (1u<<11) /* inorganic destruction only */
#define MF_COMBAT_HURT(i) (1u << (16+(i)))
#define MF_COMBAT_DESTROY(i) (1u << (14+(i)))
#define MF_COMBAT_NONKILL(i) (1u << (12+(i)))
enum { MF_SWOOSH=1, MF_JUMP_SOUND=2, MF_IMPACT=4, MF_TORCH_HISS=8, MF_TORCH_IGNITE=16 };
typedef struct { int x,y,hp,flash,vx,respawn; } mf_drum;
typedef struct {
    int active,x,y,height,vz,facing,attack,attack_air,hit_mask,walk,moving;
    int health,landing,invulnerable,hurt,knockback,defeated;
    int bat,air_bat_used,combo_dir,tap_window,bat_window;
    int torch,charge,torch_timer,torch_tick,a_blocked,torch_sound;
    unsigned previous_directions;
    unsigned buffered;
} mf_player;
/* Per-game/per-player movement state, outside the approved combat/player ABI. */
typedef struct {
    int dir,tap_dir,window,released,ready,anim;
    unsigned previous;
} mf_dash_state;
enum { MF_ENEMY_CORPORATE_PUNK, MF_ENEMY_SPECIAL, MF_ENEMY_RICKY };
enum { MF_PUNK_BRAWLER, MF_PUNK_FLANKER, MF_PUNK_AMBUSHER, MF_PUNK_OPPORTUNIST };
enum { MF_PUNK_APPROACH, MF_PUNK_PREP, MF_PUNK_RUSH, MF_PUNK_CLOSE };
typedef struct {
    int punches,expiry;
    unsigned rng; /* Separate stream: never consumes the approved spawn RNG. */
    int behavior,lane,phase,age,clock,side,burst_x,burst_y;
} mf_punk_ai;
/* Fast profile: active/pending are zero or 1 + the captured run pose (0..3). */
typedef struct { int active,carry,dir,pending; } mf_running_bat;
#if MF_PUNCH_COMBO
typedef struct {int next,phase,timeout;} mf_punch_combo;
#endif
#if MF_RICKY_ENEMY
typedef struct {int cooldown,active,start_x,start_y,dx,dy,height,last;} mf_ricky_jump;
#endif
typedef struct {
    mf_player players[MF_PLAYERS];
    mf_enemy enemies[MF_ENEMIES];
    mf_drum drums[MF_DRUMS];
    int camera,score,broken,started,paused,debug,ticks,events;
    int hitstop,spark,spark_x,spark_y,spark_z;
    mf_dash_state dash[MF_PLAYERS];
    mf_running_bat running_bat[MF_PLAYERS];
    int enemy_class[MF_ENEMIES]; /* Explicit KO eligibility, not HP-based. */
#if MF_LEVEL1_STAGE_CLEAR
    int stage,stage_kills,stage_timer,spawn_wait,spawn_pair;
    unsigned spawn_rng;
#endif
/* JAB BEGIN */
#if MF_JAB_COHESION
    mf_jab_repeat_state jab[MF_PLAYERS];
#endif
/* JAB END */
    /* Per-slot pressure; no changes to approved enemy/player render ABI. */
    mf_punk_ai punk[MF_ENEMIES];
    int burn_owner[MF_ENEMIES]; /* Sound attribution only; no damage/state changes. */
#if MF_PUNCH_COMBO
    mf_punch_combo combo[MF_PLAYERS];
#endif
#if MF_RICKY_ENEMY
    unsigned ricky_spawns; /* Separate deterministic class schedule; no spawn RNG consumption. */
    int ricky_punch[MF_ENEMIES];
#endif
#if MF_LEVEL1_WORLD_FLOW
    int camera_floor; /* Configurable progression floor; no actor warps. */
#endif
#if MF_RICKY_ENEMY
    mf_ricky_jump ricky_jump[MF_ENEMIES]; /* Appended: preserve existing ABI prefix. */
#endif
} mf_game;
void mf_game_init(mf_game *g);
void mf_game_step(mf_game *g,unsigned held,unsigned pressed);
void mf_game_step_coop(mf_game *g,const unsigned held[2],const unsigned pressed[2]);
void mf_game_step_inputs(mf_game *g,const unsigned held[2],const unsigned pressed[2],unsigned connected);
int mf_torch_active(const mf_player *);
int mf_torch_hits(const mf_player *p,mf_hitbox target);
int mf_player_frame(const mf_game *g,int player);
int mf_buck_frame(const mf_game *g);
int mf_bat_frame(const mf_player *p);
int mf_enemy_frame(const mf_game *g,int enemy);
int mf_boxes_overlap(mf_hitbox a,mf_hitbox b);
mf_hitbox mf_player_hurtbox(const mf_player *p);
mf_hitbox mf_enemy_hurtbox(const mf_enemy *e);
mf_hitbox mf_player_attackbox(const mf_player *p);
mf_hitbox mf_enemy_attackbox(const mf_enemy *e);
#endif
