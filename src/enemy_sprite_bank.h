#ifndef MF_ENEMY_SPRITE_BANK_H
#define MF_ENEMY_SPRITE_BANK_H
#include "enemy_bank_config.h"
#if MF_ENEMY_SPRITE_BANKS
#include <jo/jo.h>
#include "game.h"
/* Callbacks may append only a suffix, must invalidate all private handles,
   and must not modify persistent pixels/palettes. NULL means palette read-only. */
typedef struct {
    unsigned kind,definitions,bytes;
    int (*install)(jo_palette *);
    void (*invalidate)(void);
    int (*validate)(int first);
} mf_enemy_bank_spec;
enum { MF_BANK_COLD,MF_BANK_READY,MF_BANK_DRAIN,MF_BANK_LOADING,MF_BANK_FAILED,MF_BANK_RETIRED };
enum { MF_BANK_OK,MF_BANK_PREFIX,MF_BANK_PALETTE,MF_BANK_CAPACITY,MF_BANK_LOAD,MF_BANK_HANDLES,MF_BANK_VDP1 };
typedef struct {unsigned state,error,generation,swaps,peak_bytes,drains;} mf_enemy_bank_info;
enum { MF_ENEMY_BANK_CORPORATE=1 };
extern const mf_enemy_bank_spec mf_corporate_bank_spec;
/* Boot only, before the core render callback is installed. */
int mf_enemy_bank_boot(const mf_enemy_bank_spec *,jo_palette *shared_palette);
/* Running Level 1 section boundary only (not pause/gallery/clear): both slots ABSENT; caller/core integration freezes
   game/spawns and submits no sprites while draining/loading. Invalid request is
   rejected without changing a live bank. Failed installation latches text-only
   failure until restart. Three distinct core VBlanks + hardware completion needed. */
int mf_enemy_bank_prepare(const mf_enemy_bank_spec *,const mf_game *,unsigned now);
unsigned mf_enemy_bank_service(unsigned now);
int mf_enemy_bank_ready(void);
const mf_enemy_bank_spec *mf_enemy_bank_current(void);
unsigned mf_enemy_bank_bytes(void);
const mf_enemy_bank_info *mf_enemy_bank_diagnostics(void);
/* Transfer full teardown ownership to the unmodified Level 2 loader; no free. */
void mf_enemy_bank_retire(void);
#endif
#endif
