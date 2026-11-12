#ifndef MF_HUD_PANEL_MOCK_JO_H
#define MF_HUD_PANEL_MOCK_JO_H
#include <stdbool.h>
#include "../../sprite_cleanup/jo/jo.h"
typedef struct { int x,y; } jo_pos2D_fixed;
void jo_sprite_draw_4p_fixed(int,const jo_pos2D_fixed *,int,bool);
#endif
