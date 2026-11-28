#ifndef MF_LEVEL1_PROGRESSION_CONFIG_H
#define MF_LEVEL1_PROGRESSION_CONFIG_H

/* Included by game.c after the world, enemy and event definitions. */
enum {
    MF_ENCOUNTER_PUNK = 1u << MF_ENEMY_CORPORATE_PUNK,
    MF_ENCOUNTER_RICKY = 1u << MF_ENEMY_RICKY,
    MF_ENCOUNTER_WAIT_VEHICLE = 1u
};

typedef struct {
    const char *name;
    int activation_x, camera_limit, player_limit, restart_x;
    int quota, spawn_delay, spawn_jitter, pair_percent;
    unsigned enemy_types, dependencies;
} mf_encounter_definition;

#define MF_STREET_ENEMIES (MF_ENCOUNTER_PUNK | MF_ENCOUNTER_RICKY)
static const mf_encounter_definition mf_encounters[] = {
    /* Name              Start            Camera   Player limit             Restart  KOs Delay Jitter Pair  Enemy types       Dependencies */
    {"Opening street",    MF_WORLD_LEFT,   1100,    1279,                   100,     6,  90,   60,    25,   MF_STREET_ENEMIES, 0},
    {"Intersection",     1280,            1740,    MF_WORLD_BEND_X - 1,    1570,    8,  66,   54,    40,   MF_STREET_ENEMIES, 0},
    {"Downhill street",   MF_WORLD_BEND_X,  2380,    MF_WORLD_SLOPE_END - 1, 1950,    7,  45,   45,    50,   MF_STREET_ENEMIES, MF_ENCOUNTER_WAIT_VEHICLE},
    {"Garage approach",   MF_WORLD_SLOPE_END, 2570,  2757,                   2640, 9, 30, 36, 65, MF_STREET_ENEMIES, 0},
};
#undef MF_STREET_ENEMIES

#define MF_ENCOUNTER_COUNT (sizeof(mf_encounters) / sizeof(mf_encounters[0]))

#endif
