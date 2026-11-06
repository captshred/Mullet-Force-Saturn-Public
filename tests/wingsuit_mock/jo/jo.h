#ifndef WS_JO_MOCK_H
#define WS_JO_MOCK_H
#include <stddef.h>
#include <stdint.h>
extern unsigned short ws_vdp1[262144],ws_a0[65536],ws_b0[65536],ws_scsp[262144];
extern unsigned short ws_ptmr,ws_edsr;
extern unsigned short ws_cram[2050];
#define JO_VDP2_CRAM ((uintptr_t)ws_cram)
#define JO_VDP1_PTMR ws_ptmr
#define JO_VDP1_EDSR ws_edsr
#define JO_VDP1_VRAM ((uintptr_t)ws_vdp1)
#define JO_VDP1_TEXTURE_DEF_BASE_ADDRESS 0x10000
#define JO_VDP1_USER_AREA_END_ADDR (JO_VDP1_VRAM+0x7fef8)
#define VDP2_VRAM_A0 ((uintptr_t)ws_a0)
#define VDP2_VRAM_B0 ((uintptr_t)ws_b0)
#define MF_WS_SOUND_RAM ws_scsp
#define COL_TYPE_256 4
#define CHAR_SIZE_1x1 0
#define PNB_1WORD 0x8000
#define CN_12BIT 0x4000
#define PL_SIZE_1x1 0
#define TV_320x240 1
#define winFar 0
#define SPR_PAL_RGB 1
#define OFF 0
#define SPRON (1<<6)
#define NBG0ON 1
#define NBG1ON 2
#define NBG2ON 4
#define NBG1OFF 0x200
#define NBG2OFF 0x400
#define win0_IN 3
typedef unsigned short jo_color;
typedef struct {int id;jo_color *data;} jo_palette;
typedef struct {unsigned short width,height;jo_color *data;} jo_img;
typedef signed char Sint8;
#define JO_PARENT_DIR ".."
int GFS_NameToId(Sint8 *);
void jo_fs_cd(const char *);
char *jo_fs_read_file(const char *,int *);
void jo_free(void *);
void jo_dma_copy(const void *,void *,unsigned);
int jo_sprite_add(const jo_img *);
void jo_sprite_free_all(void);
int jo_get_last_sprite_id(void);
void slSoundOffWait(void);
void slScrDisp(unsigned);
void slCharNbg1(int,int);
void slPageNbg1(void *,void *,int);
void slPlaneNbg1(int);
void slMapNbg1(void *,void *,void *,void *);
void slZoomNbg1(int,int);
void slScrPosNbg1(int,int);
void slScrWindow0(unsigned short,unsigned short,unsigned short,unsigned short);
void slScrWindowModeNbg1(unsigned short);
void slSetSprTVMode(unsigned short);
void slCurWindow(unsigned char);
void slFrameClipSize(short,short);
int slWindow(short,short,short,short,short,short,short);
void slSetScreenDist(int);
void slZdspLevel(unsigned short);
void slSpriteColMode(unsigned short);
void slSpriteWinMode(unsigned short);
void slScrWindowModeSPR(unsigned short);
void test_sprite_priority(int,int);
#define slPrioritySpr0(n) test_sprite_priority(0,n)
#define slPrioritySpr1(n) test_sprite_priority(1,n)
#define slPrioritySpr2(n) test_sprite_priority(2,n)
#define slPrioritySpr3(n) test_sprite_priority(3,n)
#define slPrioritySpr4(n) test_sprite_priority(4,n)
#define slPrioritySpr5(n) test_sprite_priority(5,n)
#define slPrioritySpr6(n) test_sprite_priority(6,n)
#define slPrioritySpr7(n) test_sprite_priority(7,n)
void slPriorityNbg1(int);
void slPriorityNbg0(int);
int slScrAutoDisp(unsigned);
void jo_sprite_disable_horizontal_flip(void);
void jo_sprite_disable_vertical_flip(void);
void jo_sprite_disable_half_transparency(void);
void jo_sprite_disable_dark_filter(void);
void jo_sprite_disable_gouraud_shading(void);
void jo_sprite_restore_sprite_scale(void);
void jo_sprite_disable_clipping(void);
void jo_sprite_draw3D2(int,int,int,int);
void jo_clear_screen(void);
void jo_print(int,int,const char *);
void jo_printf(int,int,const char *,...);
#endif

void jo_sprite_enable_clipping(int);
void jo_sprite_set_clipping_area(unsigned,unsigned,unsigned,unsigned,int);

void slCharNbg2(int,int);
void slPageNbg2(void *,void *,int);
void slPlaneNbg2(int);
void slMapNbg2(void *,void *,void *,void *);
void slScrPosNbg2(int,int);
void slScrWindowModeNbg2(unsigned short);
void slPriorityNbg2(int);
