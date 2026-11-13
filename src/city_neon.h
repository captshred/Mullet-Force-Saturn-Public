#ifndef MF_CITY_NEON_H
#define MF_CITY_NEON_H
#ifndef MF_CITY_NEON
#define MF_CITY_NEON 0
#endif
#ifndef MF_CITY_CLEANUP
#define MF_CITY_CLEANUP 0
#endif
#if MF_CITY_CLEANUP && !MF_CITY_NEON
#error City cleanup requires neon stage
#endif
#if MF_CITY_NEON
#if !MF_VDP2_STREET
#error City neon requires the VDP2 street owner
#endif
#include "city_neon_data.h"
#if MF_CITY_CLEANUP
#include "city_cleanup_data.h"
#define MF_STREET_CELL_BYTES MF_CLEANUP_CELL_BYTES
#else
#define MF_STREET_CELL_BYTES MF_CITY_CELL_BYTES
#endif
#define MF_STREET_CELLS "CICELL.BIN"
#define MF_STREET_MAP "CIMAP.BIN"
#include "world_config.h"
#if MF_LEVEL1_WORLD_FLOW && MF_LIVE_CITY_PARALLAX
#define MF_STREET_PALETTE "NSPAL.BIN"
#else
#define MF_STREET_PALETTE "CIPAL.BIN"
#endif
#else
#define MF_STREET_CELL_BYTES 90240u
#define MF_STREET_CELLS "STCELLS.BIN"
#define MF_STREET_MAP "STMAP.BIN"
#define MF_STREET_PALETTE "STPAL.BIN"
#endif
#endif
