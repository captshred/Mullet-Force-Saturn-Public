#ifndef MF_ENEMY_BANK_MOCK_JO_H
#define MF_ENEMY_BANK_MOCK_JO_H
#include "../../hud_panel/jo/jo.h"
#define COL_256 1
#define COL_32K 0
extern volatile unsigned short bank_mock_ptmr,bank_mock_edsr;
#define JO_VDP1_PTMR bank_mock_ptmr
#define JO_VDP1_EDSR bank_mock_edsr
void jo_sprite_free_from(int);
#endif
