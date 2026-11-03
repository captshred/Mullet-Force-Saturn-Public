#ifndef MF_STREET_MOCK_JO_H
#define MF_STREET_MOCK_JO_H
#include <stddef.h>
extern unsigned char street_a0[131072],street_b0[131072];
#define VDP2_VRAM_A0 ((unsigned long)street_a0)
#define VDP2_VRAM_B0 ((unsigned long)street_b0)
#define JO_NULL NULL
#define JO_ROOT_DIR NULL
#define JO_VDP2_RAM_CELL_NBG1 1
#define JO_VDP2_RAM_MAP_NBG1 2
#define COL_TYPE_256 0x10
#define CHAR_SIZE_1x1 0
#define PNB_1WORD 0x8000
#define CN_12BIT 0x4000
#define PL_SIZE_2x1 1
#define NBG0ON 1
#define NBG1ON 2
#define win0_IN 3
typedef unsigned short jo_color;
typedef signed char Sint8;
int GFS_NameToId(Sint8 *);
void jo_printf(int,int,const char *,...);
typedef struct {int id;jo_color *data;} jo_palette;
char *jo_fs_read_file(const char *,int *);
void jo_free(void *);
void jo_dma_copy(const void *,void *,unsigned);
void jo_palette_to_cram(unsigned short *,unsigned short *,unsigned);
void jo_vdp2_free(const void *);
void *jo_vdp2_malloc(int,unsigned);
void slTVOff(void);
void slTVOn(void);
void slCharNbg1(int,int);
void slPageNbg1(void *,void *,int);
void slPlaneNbg1(int);
void slMapNbg1(void *,void *,void *,void *);
void slZoomNbg1(int,int);
void slScrPosNbg1(int,int);
void slScrWindow0(unsigned short,unsigned short,unsigned short,unsigned short);
void slScrWindowModeNbg1(unsigned short);
void slPriorityNbg1(int);
void slPriorityNbg0(int);
void test_priority(int,int);
#define slPrioritySpr0(n) test_priority(0,n)
#define slPrioritySpr1(n) test_priority(1,n)
#define slPrioritySpr2(n) test_priority(2,n)
#define slPrioritySpr3(n) test_priority(3,n)
#define slPrioritySpr4(n) test_priority(4,n)
#define slPrioritySpr5(n) test_priority(5,n)
#define slPrioritySpr6(n) test_priority(6,n)
#define slPrioritySpr7(n) test_priority(7,n)
int slScrAutoDisp(unsigned);
void jo_set_tga_default_palette(jo_palette *);
int jo_sprite_add_tga(void *,const char *,int);
void jo_sprite_set_palette(int);
void jo_sprite_draw3D2(int,int,int,int);
#endif
