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
static unsigned cursor=0x10000+422208-5120-6336,addresses[256];
static int widths[256],heights[256],count=241,loads,draws,flip,last_id;
void *jo_sprite_get_raw_data(int id){return (void *)(unsigned long)(JO_VDP1_VRAM+addresses[id]);}
int jo_sprite_get_width(int id){return widths[id];}
int jo_sprite_get_height(int id){return heights[id];}
void jo_set_tga_default_palette(jo_palette *p){assert(!p || p->id==7);}
int jo_sprite_add_tga(void *dir,const char *name,int key){const mf_polish_resource *p=loads<10?&ph_resources[loads]:&pd_resources[loads-10];loads++;assert(key==1 && !strcmp(dir,loads<=10?"HQHURT":"HQDEATH") && !strcmp(name,p->name) && count<255);addresses[count]=cursor;widths[count]=p->width;heights[count]=p->height;cursor+=p->bytes;return count++;}
void jo_sprite_restore_sprite_scale(void){}
void jo_sprite_disable_horizontal_flip(void){flip=0;}
void jo_sprite_enable_horizontal_flip(void){flip=1;}
void jo_sprite_set_palette(int id){assert(id==7);}
void jo_sprite_draw3D2(int id,int x,int y,int z){assert(id>=0 && id<254 && x>0 && y>0 && z==220);last_id=id;draws++;}
int main(void){jo_palette pal={7};mf_game g={0},before;int a,t,f,holds[3]={0},rid,w,h;const char *name;unsigned bytes;
 addresses[235]=cursor-32;widths[235]=8;heights[235]=4;last_resource=235;resource_palette=&pal;palette_id=7;
 for(rid=0;rid<MF_REVIEW_RESOURCES;rid++)resource_ids[rid]=20;
 resource_info(99,&name,&w,&h,&bytes);assert(!strcmp(name,"RD0.TGA"));resource_info(100,&name,&w,&h,&bytes);assert(!strcmp(name,"RD1.TGA"));
 assert(!mf_player_death_load());assert(mf_player_hurt_load() && loads==10 && count==251 && texture_bytes==442336);
 assert(mf_player_death_load() && loads==12 && count==253 && texture_bytes==446304);assert(mf_player_death_load() && loads==12);
 for(a=0;a<2;a++)for(t=120;t>0;t--)for(f=-1;f<=1;f+=2){g.players[a].active=1;g.players[a].health=0;g.players[a].defeated=t;g.players[a].facing=f;before=g;draws=0;assert(mf_player_death_draw(&g,a,160,210,220) && draws==2 && !flip);assert(!memcmp(&g,&before,sizeof(g)));if(!a && f==1)holds[mf_player_death_phase(&g,a)]++;}
 assert(holds[0]==8 && holds[1]==16 && holds[2]==96);g.players[0].health=1;assert(mf_player_death_phase(&g,0)==-1);g.players[0].health=0;g.players[0].defeated=0;assert(mf_player_death_phase(&g,0)==-1);assert(mf_player_death_phase(&g,-1)==-1);assert(mf_player_death_phase(&g,2)==-1);
 pd_loaded=0;last_resource=254;assert(!mf_player_death_load() && loads==12);
 puts("PASS HQ player defeat: original 120 ticks / 8-16-96 visual phase, two actors and facings, alive/recovered excluded, no simulation writes, idempotent two uploads and capacity rejection");return 0;}
