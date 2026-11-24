#ifndef MF_DEV_SECTIONS_H
#define MF_DEV_SECTIONS_H

#include "game.h"

#if MF_DEV_MODE
#if !MF_LEVEL1_WORLD_FLOW || !MF_BRUCE_RUNTIME || !MF_VEHICLE_AMBUSH
#error Developer sections require the complete Level 1 profile
#endif

typedef enum {
    MF_SECTION_OPENING, MF_SECTION_ION, MF_SECTION_INTERSECTION,
    MF_SECTION_DOWNHILL, MF_SECTION_VEHICLE, MF_SECTION_GARAGE,
    MF_SECTION_BRUCE, MF_SECTION_APRON, MF_SECTION_COUNT
} mf_section;

const char *mf_section_name(mf_section section);
mf_section mf_section_current(const mf_game *game, mf_section previous);
void mf_section_init(mf_game *game, mf_section section);
#endif

#endif
