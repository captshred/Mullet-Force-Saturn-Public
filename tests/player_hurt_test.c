#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {unsigned short width,height,adr,size;} jo_texture_definition;
static jo_texture_definition __jo_sprite_def[256];
#define JO_MAX_SPRITE 255
typedef struct {void *data;int index,color_mode;} jo_picture_definition;
static jo_picture_definition __jo_sprite_pic[256];
typedef struct {unsigned short width,height;unsigned char *data;} jo_img_8bits;
int jo_sprite_add_8bits_image(const jo_img_8bits *);
#include "../src/animation_preview.c"
static unsigned cursor=0x10000+422208-5120,addresses[256];
static int widths[256],heights[256],count=244,loads,draws,flip,last_id;
void *jo_sprite_get_raw_data(int id){return (void *)(unsigned long)(JO_VDP1_VRAM+addresses[id]);}
int jo_sprite_get_width(int id){return widths[id];}
int jo_sprite_get_height(int id){return heights[id];}
void jo_set_tga_default_palette(jo_palette *p){assert(!p || p->id==7);}
int jo_sprite_add_tga(void *dir,const char *name,int key){const mf_polish_resource *p=&ph_resources[loads++];assert(key==1 && !strcmp(dir,"HQHURT") && !strcmp(name,p->name) && count<255);addresses[count]=cursor;widths[count]=p->width;heights[count]=p->height;cursor+=p->bytes;return count++;}
void jo_sprite_restore_sprite_scale(void){}
void jo_sprite_disable_horizontal_flip(void){flip=0;}
void jo_sprite_enable_horizontal_flip(void){flip=1;}
void jo_sprite_set_palette(int id){assert(id==7);}
void jo_sprite_draw3D2(int id,int x,int y,int z){assert(id>=0 && id<254 && x>0 && y>0 && z==220);last_id=id;draws++;}
int main(void){jo_palette pal={7};mf_game g={0},before;int a,t,f,holds[3]={0},rid,w,h;const char *name;unsigned bytes;
 addresses[238]=cursor-32;widths[238]=8;heights[238]=4;last_resource=238;resource_palette=&pal;palette_id=7;
 for(rid=0;rid<MF_REVIEW_RESOURCES;rid++)resource_ids[rid]=20;
 resource_info(99,&name,&w,&h,&bytes);assert(!strcmp(name,"RC0.TGA"));resource_info(100,&name,&w,&h,&bytes);assert(!strcmp(name,"RC1.TGA"));
 assert(mf_player_hurt_load() && loads==10 && count==254 && texture_bytes==448672);assert(mf_player_hurt_load() && loads==10);
 for(a=0;a<2;a++)for(t=12;t>0;t--)for(f=-1;f<=1;f+=2){g.players[a].active=1;g.players[a].health=100;g.players[a].hurt=t;g.players[a].facing=f;before=g;draws=0;assert(mf_player_hurt_draw(&g,a,160,210,220) && draws==2 && !flip);assert(last_id==ph_ids[ph_upper[a][t>8?0:t>4?1:2].resource]);assert(!memcmp(&g,&before,sizeof(g)));if(!a && f==1)holds[mf_player_hurt_phase(&g,a)]++;}
 assert(holds[0]==4 && holds[1]==4 && holds[2]==4);g.players[0].health=0;g.players[0].hurt=12;assert(mf_player_hurt_phase(&g,0)==-1 && !mf_player_hurt_draw(&g,0,160,210,220));g.players[1].hurt=0;assert(mf_player_hurt_phase(&g,1)==-1);
 ph_loaded=0;last_resource=250;assert(!mf_player_hurt_load() && loads==10);
 puts("PASS HQ player hurt: 4/4/4 existing ticks, both actors/facings, no simulation writes, death excluded, ten shared uploads, 254 definitions and capacity rejection; Chuck-only replacement routing");return 0;}
