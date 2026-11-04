#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <jo/jo.h>
#include "street.h"
jo_texture_definition __jo_sprite_def[255];
jo_picture_definition __jo_sprite_pic[255];
static int count,palette=-1,active_palette=-1;
static unsigned cursor=0x10000;
static unsigned bytes[255];
static int palettes[255];
static char names[255][80];
void *jo_malloc(unsigned n){return malloc(n);}
void jo_free(void *p){free(p);}
void jo_create_palette(jo_palette *p){p->id=++palette;p->data=calloc(256,2);}
void jo_set_tga_default_palette(jo_palette *p){active_palette=p?p->id:-1;}
int add(const char *name,int w,int h,int bpp){
 int id=count++;assert(id<255);
 if(id){jo_texture_definition *p=&__jo_sprite_def[id-1];cursor=p->adr*8+((p->width*p->height*(__jo_sprite_pic[id-1].color_mode==1?1:2)+31)&~31);}
 bytes[id]=(w*h*bpp+31)&~31;palettes[id]=active_palette;
 __jo_sprite_def[id]=(jo_texture_definition){w,h,cursor/8,(w/8<<8)|h};
 __jo_sprite_pic[id]=(jo_picture_definition){(void *)(unsigned long)(JO_VDP1_VRAM+cursor),id,bpp==1?1:0};
 snprintf(names[id],80,"%s",name);cursor+=bytes[id];return id;
}
int jo_sprite_add_tga(void *dir,const char *name,int transparent){
 char path[160],label[80];unsigned char hdr[18];FILE *f;
 (void)transparent;snprintf(label,80,"%s%s%s",dir?(char *)dir:"",dir?"/":"",name);
 snprintf(path,160,"build/cd/%s",label);f=fopen(path,"rb");assert(f);assert(fread(hdr,1,18,f)==18);fclose(f);
 return add(label,hdr[12]+256*hdr[13],hdr[14]+256*hdr[15],hdr[2]==1?1:2);
}
int jo_sprite_add(const jo_img *p){return add(p->height==40?"generated:panel":"generated:health-bar",p->width,p->height,2);}
int jo_sprite_add_8bits_image(const jo_img_8bits *p){return add("alias",p->width,p->height,1);}
void *jo_sprite_get_raw_data(int id){return __jo_sprite_pic[id].data;}
int jo_sprite_get_width(int id){return __jo_sprite_def[id].width;}
int jo_sprite_get_height(int id){return __jo_sprite_def[id].height;}
int jo_get_last_sprite_id(void){return count-1;}
int mf_street_load(jo_palette *p,int ids[5]){(void)p;(void)ids;return 1;}
int mf_parallax_load(void){return 1;}
int mf_parallax_error(void){return 0;}
int mf_music_init(void){jo_palette p;jo_create_palette(&p);return 1;}
void jo_sprite_restore_sprite_scale(void){}
void jo_sprite_disable_horizontal_flip(void){}
void jo_sprite_enable_horizontal_flip(void){}
void jo_sprite_set_palette(int n){(void)n;}
void jo_sprite_draw3D2(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void jo_clear_screen_line(int n){(void)n;}
void jo_print(int a,int b,const char *s){(void)a;(void)b;(void)s;}
void jo_printf(int a,int b,const char *s,...){(void)a;(void)b;(void)s;}
void mf_street_draw(const int a[5],int b,int c){(void)a;(void)b;(void)c;}
void audit_finish(void){int i;puts("id,path,width,height,format,allocated_bytes,vdp1_offset,palette_at_registration");for(i=0;i<count;i++)printf("%d,%s,%d,%d,%s,%u,%u,%d\n",i,names[i],__jo_sprite_def[i].width,__jo_sprite_def[i].height,__jo_sprite_pic[i].color_mode==1?"indexed8":"RGB555",bytes[i],__jo_sprite_def[i].adr*8,palettes[i]);fprintf(stderr,"definitions=%d bytes=%u\n",count,cursor-0x10000);}
