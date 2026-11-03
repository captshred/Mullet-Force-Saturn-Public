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
static unsigned cursor=0x10000+302336-16320-22784,addresses[256];
static int widths[256],heights[256],uploads[MF_REVIEW_RESOURCES+MF_RBV_NEW+MF_CA_NEW+MF_HT_NEW+MF_HJ_NEW],count=6,draws,flip;
static int drawn_ids[64],draw_flips[64];
void *jo_sprite_get_raw_data(int id){return (void *)(unsigned long)(JO_VDP1_VRAM+addresses[id]);}
int jo_sprite_get_width(int id){return widths[id];}
int jo_sprite_get_height(int id){return heights[id];}
void jo_set_tga_default_palette(jo_palette *p){assert(!p || p->id==7);}
int jo_sprite_add_tga(void *dir,const char *name,int transparent)
{
    int rid,w,h;unsigned bytes;const char *expected;
    assert(transparent==1 && count<256);
    assert(dir ? (!strcmp((const char *)dir,"COMBAT") || !strcmp((const char *)dir,"HQTORCH") || !strcmp((const char *)dir,"HQJUMP")) : strncmp(name,"CA",2));
    for(rid=0;rid<MF_REVIEW_RESOURCES;rid++){
        resource_info(rid,&expected,&w,&h,&bytes);
        if(!strcmp(name,expected))break;
    }
    if(rid==MF_REVIEW_RESOURCES){int v;for(v=0;v<MF_RBV_NEW;v++)if(!strcmp(name,rbv_resources[v].name)){w=rbv_resources[v].width;h=rbv_resources[v].height;bytes=rbv_resources[v].bytes;rid=MF_REVIEW_RESOURCES+v;break;}}
    if(rid==MF_REVIEW_RESOURCES){int v;for(v=0;v<MF_CA_NEW;v++)if(!strcmp(name,ca_resources[v].name)){w=ca_resources[v].width;h=ca_resources[v].height;bytes=ca_resources[v].bytes;rid=MF_REVIEW_RESOURCES+MF_RBV_NEW+v;break;}}
    if(rid==MF_REVIEW_RESOURCES){int v;for(v=0;v<MF_HT_NEW;v++)if(!strcmp(name,ht_resources[v].name)){w=ht_resources[v].width;h=ht_resources[v].height;bytes=ht_resources[v].bytes;rid=MF_REVIEW_RESOURCES+MF_RBV_NEW+MF_CA_NEW+v;break;}}
    if(rid==MF_REVIEW_RESOURCES){int v;for(v=0;v<MF_HJ_NEW;v++)if(!strcmp(name,hj_resources[v].name)){w=hj_resources[v].width;h=hj_resources[v].height;bytes=hj_resources[v].bytes;rid=MF_REVIEW_RESOURCES+MF_RBV_NEW+MF_CA_NEW+MF_HT_NEW+v;break;}}
    assert(rid<MF_REVIEW_RESOURCES+MF_RBV_NEW+MF_CA_NEW+MF_HT_NEW+MF_HJ_NEW && ++uploads[rid]==1);
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
{assert(id>=0 && id<count && x>-100 && y>-100 && (z>=228 && z<=231));draw_flips[draws%64]=flip;drawn_ids[draws++%64]=id;}
void jo_clear_screen_line(int line){(void)line;}
void jo_print(int x,int y,const char *s){(void)x;(void)y;(void)s;}
void jo_printf(int x,int y,const char *s,...){(void)x;(void)y;(void)s;}
void mf_street_draw(const int street[5],int palid,int camera){(void)street;(void)palid;(void)camera;}
int main(void)
{
 const int gallery[2][3]={{0,1,2},{3,4,5}};jo_palette palette={7};mf_game g,copy;jo_texture_definition before[256];int a,k,d,p,boot;
 for(a=0;a<2;a++)for(p=0;p<3;p++){int id=gallery[a][p];widths[id]=animation_parts[a][0][p].width;heights[id]=animation_parts[a][0][p].height;__jo_sprite_def[id]=(jo_texture_definition){widths[id],heights[id],0,0};}
 addresses[5]=cursor-((widths[5]*heights[5]+31u)&~31u);
 assert(mf_animation_load(&palette,gallery) && mf_hq_torch_load(3) && mf_hq_jump_load());assert(texture_bytes==454400-22784+MF_HJ_BYTES-11744);boot=count;
 memset(&g,0,sizeof(g));
 for(a=0;a<2;a++)for(k=1;k<=6;k++)for(d=-1;d<=1;d+=2){
  mf_player *q=&g.players[a];memset(q,0,sizeof(*q));q->active=1;q->health=100;q->facing=d;
  if(k==5)q->landing=6;else{q->height=8000;q->vz=k==1?1436:k==2?1000:k==3?0:-700;}
  if(k==6){q->attack=7;q->attack_air=1;}
  assert(mf_hq_jump_phase(q)==k);copy=g;memcpy(before,__jo_sprite_def,sizeof(before));draws=0;
  assert(mf_hq_jump_draw(&g,a,100,202,230) && draws==(k==1 || k==5 || k==4 || k==6?4:3) && !flip);
  assert(!memcmp(&g,&copy,sizeof(g)) && !memcmp(before,__jo_sprite_def,sizeof(before)) && count==boot);
  q->bat=1;assert(!mf_hq_jump_draw(&g,a,100,202,230));q->bat=0;q->hurt=1;assert(!mf_hq_jump_draw(&g,a,100,202,230));q->hurt=0;q->health=0;assert(!mf_hq_jump_draw(&g,a,100,202,230));
 }
 {mf_player q={0};q.active=1;q.health=100;q.height=100;q.vz=1362;assert(mf_hq_jump_phase(&q)==1);q.vz=1361;assert(mf_hq_jump_phase(&q)==2);q.vz=296;assert(mf_hq_jump_phase(&q)==3);q.vz=-296;assert(mf_hq_jump_phase(&q)==3);q.vz=-297;assert(mf_hq_jump_phase(&q)==4);q.height=q.vz=0;q.landing=1;assert(mf_hq_jump_phase(&q)==5);q.attack=1;assert(mf_hq_jump_phase(&q)==0);}
 puts("PASS HQ jump bank: six distinct phase mappings, both actors/facings, grounded boot compression, stable alias definitions, no simulation writes/uploads, aerial bat/hurt/torch priority preserved");return 0;
}
