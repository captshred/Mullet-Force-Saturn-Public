#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <jo/jo.h>
#include "street.h"
jo_texture_definition __jo_sprite_def[255];
jo_picture_definition __jo_sprite_pic[255];
static int count,palette=0,active_palette=-1;
static unsigned cursor=0x10000;
static unsigned bytes[255];
static int palettes[255];
static char names[255][80];
static unsigned char *payloads[255];
static unsigned payload_sizes[255];
static jo_palette *all_palettes[8];
static int flip,scale_x=65536,scale_y=65536,selected_palette;
struct audit_jo_input jo_inputs[12];
unsigned cleanup_case,cleanup_context;
static unsigned short color(unsigned r,unsigned g,unsigned b){return 0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10);}
static void retain(int id,const void *data,unsigned n){if(!n)return;assert(data);payloads[id]=malloc(n);assert(payloads[id]);memcpy(payloads[id],data,n);payload_sizes[id]=n;}

void *jo_malloc(unsigned n){return malloc(n);}
void jo_free(void *p){free(p);}
void jo_create_palette(jo_palette *p){p->id=++palette;p->data=calloc(256,2);assert(p->id<8);all_palettes[p->id]=p;}
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
 char path[160],label[80];unsigned char *file,*pixels;unsigned w,h,bpp,off,n,y,x,i,cm;long length;FILE *f;int id;
 snprintf(label,sizeof(label),"%s%s%s",dir?(char *)dir:"",dir?"/":"",name);
 snprintf(path,sizeof(path),"build/cd/%s",label);f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);length=ftell(f);rewind(f);file=malloc(length);assert(file && fread(file,1,length,f)==(size_t)length);fclose(f);
 w=file[12]+256*file[13];h=file[14]+256*file[15];bpp=file[16]==8?1:2;
 assert(!file[0] && ((bpp==1 && file[2]==1 && file[7]==24) || (bpp==2 && file[2]==2 && file[16]==24)));
 cm=file[5]+256*file[6];off=18+cm*(file[7]/8);n=w*h*bpp;pixels=malloc(n);assert(pixels);
 if(bpp==1 && active_palette>=0){assert(cm==256);for(i=0;i<255;i++)all_palettes[active_palette]->data[i]=color(file[18+i*3+2],file[18+i*3+1],file[18+i*3]);}
 for(y=0;y<h;y++)for(x=0;x<w;x++){
  unsigned at=x+(file[17]&32?y:h-1-y)*w,source=x+y*w;
  if(bpp==1){unsigned char v=(unsigned char)(file[off+source]+1);pixels[at]=(v==(unsigned char)transparent)?0:v;}
  else {unsigned q=off+source*3;unsigned short v=color(file[q+2],file[q+1],file[q]);((unsigned short *)pixels)[at]=v==(unsigned short)transparent?0:v;}
 }
 id=add(label,w,h,bpp);retain(id,pixels,n);free(pixels);free(file);return id;
}
int jo_sprite_add(const jo_img *p){int id=add(p->height==40?"generated:panel":"generated:health-bar",p->width,p->height,2);retain(id,p->data,p->width*p->height*2);return id;}
int jo_sprite_add_8bits_image(const jo_img_8bits *p){return add("alias",p->width,p->height,1);}
void *jo_sprite_get_raw_data(int id){return __jo_sprite_pic[id].data;}
int jo_sprite_get_width(int id){return __jo_sprite_def[id].width;}
int jo_sprite_get_height(int id){return __jo_sprite_def[id].height;}
int jo_get_last_sprite_id(void){return count-1;}
int mf_street_load(jo_palette *p,int ids[5]){(void)p;(void)ids;return 1;}
int mf_parallax_load(void){return 1;}
int mf_parallax_error(void){return 0;}
int mf_music_init(void){return 1;}
int mf_music_ready(void){return 1;}
void mf_street_animate(unsigned n){(void)n;}
void jo_sprite_restore_sprite_scale(void){scale_x=scale_y=65536;}
void jo_sprite_disable_horizontal_flip(void){flip=0;}
void jo_sprite_enable_horizontal_flip(void){flip=1;}
void jo_sprite_set_palette(int n){selected_palette=n;}
static void draw(int id,int x,int y,int z,int kind){assert(id>=0 && id<count);printf("DRAW|%u|%d|%d|%d|%d|%d|%d|%d|%d|%d\n",cleanup_case,id,kind,x,y,z,flip,scale_x,scale_y,selected_palette);}
void jo_sprite_draw3D2(int a,int b,int c,int d){draw(a,b,c,d,2);}
void jo_sprite_draw3D(int a,int b,int c,int d){draw(a,b,c,d,3);}
void jo_sprite_change_sprite_scale_xy_fixed(int x,int y){scale_x=x;scale_y=y;}
void cleanup_frame(void){printf("FRAME|%u|%u\n",cleanup_case++,cleanup_context);}

void jo_clear_screen_line(int n){(void)n;}
void jo_print(int a,int b,const char *s){(void)a;(void)b;(void)s;}
void jo_printf(int a,int b,const char *s,...){(void)a;(void)b;(void)s;}
void mf_street_draw(const int a[5],int b,int c){(void)a;(void)b;(void)c;}
void audit_finish(void){
 int i,j;unsigned k;for(i=0;i<count;i++){
  unsigned at=__jo_sprite_def[i].adr*8,nb=__jo_sprite_def[i].width*__jo_sprite_def[i].height*(__jo_sprite_pic[i].color_mode==1?1:2);
  for(j=0;j<count;j++)if(payloads[j] && at>=((unsigned long)__jo_sprite_pic[j].data-JO_VDP1_VRAM) && at+nb<=((unsigned long)__jo_sprite_pic[j].data-JO_VDP1_VRAM)+payload_sizes[j])break;
  assert(j<count);k=at-((unsigned long)__jo_sprite_pic[j].data-JO_VDP1_VRAM);
  printf("TEXTURE|%d|%s|%u|%u|%d|%u|%u|",i,names[i],__jo_sprite_def[i].width,__jo_sprite_def[i].height,__jo_sprite_pic[i].color_mode,bytes[i],at);
  for(;nb;--nb,k++)printf("%02x",payloads[j][k]);putchar('\n');
 }
 for(i=1;i<8;i++){assert(all_palettes[i]);printf("PALETTE|%d|",i);for(k=0;k<255;k++)printf("%04x",all_palettes[i]->data[k]);putchar('\n');}
 fprintf(stderr,"definitions=%d bytes=%u\n",count,cursor-0x10000);
}
