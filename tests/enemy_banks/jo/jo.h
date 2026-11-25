#ifndef MF_ENEMY_BANK_MOCK_JO_H
#define MF_ENEMY_BANK_MOCK_JO_H
#include "../../hud_panel/jo/jo.h"
#define COL_256 1
#define COL_32K 0
extern volatile unsigned short bank_mock_ptmr,bank_mock_edsr;
#define JO_VDP1_PTMR bank_mock_ptmr
#define JO_VDP1_EDSR bank_mock_edsr
void jo_sprite_free_from(int);
#if MF_NOAH_RUN
#define MF_NOAH_HOST_CACHE 1
char *jo_fs_read_file_in_dir(const char *, const char *, int *);
void slDMACopy(void *, void *, unsigned);
void slDMAWait(void);
#endif
#endif
