#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {unsigned short width,height,adr,size;} jo_texture_definition;
static jo_texture_definition __jo_sprite_def[256];
#define JO_MAX_SPRITE 256
typedef struct {void *data;int index,color_mode;} jo_picture_definition;
static jo_picture_definition __jo_sprite_pic[256];
typedef struct {unsigned short width,height;unsigned char *data;} jo_img_8bits;
int jo_sprite_add_8bits_image(const jo_img_8bits *);
#include "../src/animation_preview.c"
static unsigned cursor=0x10000+302336-16320,addresses[256];
static int widths[256],heights[256],uploads[MF_REVIEW_RESOURCES+MF_RBV_NEW+MF_CA_NEW+MF_HT_NEW],count=6,draws,flip;
static int drawn_ids[64],draw_flips[64];
void *jo_sprite_get_raw_data(int id){return (void *)(unsigned long)(JO_VDP1_VRAM+addresses[id]);}
int jo_sprite_get_width(int id){return widths[id];}
int jo_sprite_get_height(int id){return heights[id];}
void jo_set_tga_default_palette(jo_palette *p){assert(!p || p->id==7);}
int jo_sprite_add_tga(void *dir,const char *name,int transparent)
{
    int rid,w,h;unsigned bytes;const char *expected;
    assert(transparent==1 && count<256);
    assert(dir ? (!strcmp((const char *)dir,"COMBAT") || !strcmp((const char *)dir,"HQTORCH")) : strncmp(name,"CA",2));
    for(rid=0;rid<MF_REVIEW_RESOURCES;rid++){
        resource_info(rid,&expected,&w,&h,&bytes);
        if(!strcmp(name,expected))break;
    }
    if(rid==MF_REVIEW_RESOURCES){int v;for(v=0;v<MF_RBV_NEW;v++)if(!strcmp(name,rbv_resources[v].name)){w=rbv_resources[v].width;h=rbv_resources[v].height;bytes=rbv_resources[v].bytes;rid=MF_REVIEW_RESOURCES+v;break;}}
    if(rid==MF_REVIEW_RESOURCES){int v;for(v=0;v<MF_CA_NEW;v++)if(!strcmp(name,ca_resources[v].name)){w=ca_resources[v].width;h=ca_resources[v].height;bytes=ca_resources[v].bytes;rid=MF_REVIEW_RESOURCES+MF_RBV_NEW+v;break;}}
    if(rid==MF_REVIEW_RESOURCES){int v;for(v=0;v<MF_HT_NEW;v++)if(!strcmp(name,ht_resources[v].name)){w=ht_resources[v].width;h=ht_resources[v].height;bytes=ht_resources[v].bytes;rid=MF_REVIEW_RESOURCES+MF_RBV_NEW+MF_CA_NEW+v;break;}}
    assert(rid<MF_REVIEW_RESOURCES+MF_RBV_NEW+MF_CA_NEW+MF_HT_NEW && ++uploads[rid]==1);
    __jo_sprite_def[count]=(jo_texture_definition){w,h,cursor/8,(w/8<<8)|h};
    __jo_sprite_pic[count].data=(void *)(unsigned long)(JO_VDP1_VRAM+cursor);
    widths[count]=w;heights[count]=h;addresses[count]=cursor;cursor+=bytes;return count++;
}
int jo_sprite_add_8bits_image(const jo_img_8bits *p){assert(p->width==8 && p->height==0 && !p->data);return count++;}
void jo_sprite_restore_sprite_scale(void){}
void jo_sprite_disable_horizontal_flip(void){flip=0;}
void jo_sprite_enable_horizontal_flip(void){flip=1;}
void jo_sprite_set_palette(int id){assert(id==7 || id==3);}
void jo_sprite_draw3D2(int id,int x,int y,int z)
{assert(id>=0 && id<count && x>-100 && y>0 && (z>=228 && z<=231));draw_flips[draws%64]=flip;drawn_ids[draws++%64]=id;}
void jo_clear_screen_line(int line){(void)line;}
void jo_print(int x,int y,const char *s){(void)x;(void)y;(void)s;}
void jo_printf(int x,int y,const char *s,...){(void)x;(void)y;(void)s;}
void mf_street_draw(const int street[5],int palid,int camera){(void)street;(void)palid;(void)camera;}
int main(void)
{
 const int gallery[2][3]={{0,1,2},{3,4,5}};jo_palette palette={7};int a,p,mode,walk,d,boot;
 mf_game g,copy;jo_texture_definition before[256];
 for(a=0;a<2;a++)for(p=0;p<3;p++){int id=gallery[a][p];widths[id]=animation_parts[a][0][p].width;heights[id]=animation_parts[a][0][p].height;__jo_sprite_def[id]=(jo_texture_definition){widths[id],heights[id],0,0};}
 addresses[5]=cursor-((widths[5]*heights[5]+31u)&~31u);
 assert(mf_animation_load(&palette,gallery));assert(mf_hq_torch_load(3));assert(texture_bytes==454400-11744);boot=count;
 assert(ht_alias(0,-1,1)==-1 && ht_alias(0,20,1)==-1 && count==boot);
 memset(&g,0,sizeof(g));
 for(a=0;a<2;a++)for(mode=1;mode<=3;mode++)for(walk=0;walk<30;walk++)for(d=-1;d<=1;d+=2){
  mf_player *q=&g.players[a];q->active=1;q->health=40;q->torch=mode;q->walk=walk;q->moving=walk!=0;q->facing=d;
  copy=g;memcpy(before,__jo_sprite_def,sizeof(before));draws=0;
  assert(mf_hq_torch_draw(&g,a,100,202,230) && draws==5 && !flip);
  assert(!memcmp(&copy,&g,sizeof(g)) && !memcmp(before,__jo_sprite_def,sizeof(before)) && count==boot);
  q->hurt=1;assert(!mf_hq_torch_draw(&g,a,100,202,230));q->hurt=0;
 }
 puts("PASS HQ torch bank: both actors/states/facings/30 walk ticks, existing IDs, stable persistent row views, pure renderer, no draw-time uploads");return 0;
}
