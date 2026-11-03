#ifndef MF_GALLERY_MOCK_JO_H
#define MF_GALLERY_MOCK_JO_H
#ifndef JO_MAX_SPRITE
#define JO_MAX_SPRITE 255
#endif
#define JO_VDP1_VRAM 0x25c00000ul
#define JO_ROOT_DIR ((void *)0)
#define JO_NULL ((void *)0)
typedef struct { int id; } jo_palette;
void *jo_sprite_get_raw_data(int id);
int jo_sprite_get_width(int id);
int jo_sprite_get_height(int id);
int jo_get_last_sprite_id(void);
void jo_create_palette(jo_palette *p);
void jo_set_tga_default_palette(jo_palette *p);
int jo_sprite_add_tga(void *root,const char *name,int transparent);
void jo_sprite_restore_sprite_scale(void);
void jo_sprite_disable_horizontal_flip(void);
void jo_sprite_enable_horizontal_flip(void);
void jo_sprite_set_palette(int id);
void jo_sprite_draw3D2(int id,int x,int y,int z);
void jo_print(int x,int y,const char *text);
void jo_printf(int x,int y,const char *format,...);
#endif
