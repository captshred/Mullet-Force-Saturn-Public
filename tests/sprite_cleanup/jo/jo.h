#ifndef MF_SPRITE_AUDIT_JO_H
#define MF_SPRITE_AUDIT_JO_H
#ifndef JO_MAX_SPRITE
#define JO_MAX_SPRITE 255
#endif
typedef struct {unsigned short width,height,adr,size;} jo_texture_definition;
typedef struct {void *data;int index,color_mode;} jo_picture_definition;
typedef struct {unsigned short width,height;unsigned char *data;} jo_img_8bits;
typedef struct {unsigned short width,height;unsigned short *data;} jo_img;
extern jo_texture_definition __jo_sprite_def[255];
extern jo_picture_definition __jo_sprite_pic[255];
int jo_sprite_add_8bits_image(const jo_img_8bits *);
int jo_sprite_add(const jo_img *);
void *jo_malloc(unsigned);
void jo_free(void *);
void jo_clear_screen_line(int);
#define JO_COLOR_RGB(r,g,b) (0x8000|((r)>>3)|(((g)>>3)<<5)|(((b)>>3)<<10))
#define JO_VDP1_VRAM 0x25c00000ul
#define JO_ROOT_DIR ((void *)0)
#define JO_NULL ((void *)0)
typedef unsigned short jo_color;
typedef struct { int id; jo_color *data; } jo_palette;
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

struct audit_jo_input {int id;};
extern struct audit_jo_input jo_inputs[12];
void jo_sprite_change_sprite_scale_xy_fixed(int,int);
void jo_sprite_draw3D(int,int,int,int);
extern unsigned cleanup_case,cleanup_context;
void cleanup_frame(void);
#endif
