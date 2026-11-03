#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/animation_preview.c"
static unsigned cursor=0x10000+302336,addresses[256];
static int widths[256],heights[256],uploads[MF_REVIEW_RESOURCES+MF_RBV_NEW+MF_CA_NEW],count=6,draws,flip;
static int drawn_ids[64];
void *jo_sprite_get_raw_data(int id){return (void *)(unsigned long)(JO_VDP1_VRAM+addresses[id]);}
int jo_sprite_get_width(int id){return widths[id];}
int jo_sprite_get_height(int id){return heights[id];}
void jo_set_tga_default_palette(jo_palette *p){assert(!p || p->id==7);}
int jo_sprite_add_tga(void *dir,const char *name,int transparent)
{
    int rid,w,h;unsigned bytes;const char *expected;
    assert(transparent==1 && count<256);
    assert(dir ? !strcmp((const char *)dir,"COMBAT") : strncmp(name,"CA",2));
    for(rid=0;rid<MF_REVIEW_RESOURCES;rid++){
        resource_info(rid,&expected,&w,&h,&bytes);
        if(!strcmp(name,expected))break;
    }
    if(rid==MF_REVIEW_RESOURCES){int v;for(v=0;v<MF_RBV_NEW;v++)if(!strcmp(name,rbv_resources[v].name)){w=rbv_resources[v].width;h=rbv_resources[v].height;bytes=rbv_resources[v].bytes;rid=MF_REVIEW_RESOURCES+v;break;}}
    if(rid==MF_REVIEW_RESOURCES){int v;for(v=0;v<MF_CA_NEW;v++)if(!strcmp(name,ca_resources[v].name)){w=ca_resources[v].width;h=ca_resources[v].height;bytes=ca_resources[v].bytes;rid=MF_REVIEW_RESOURCES+MF_RBV_NEW+v;break;}}
    assert(rid<MF_REVIEW_RESOURCES+MF_RBV_NEW+MF_CA_NEW && ++uploads[rid]==1);
    widths[count]=w;heights[count]=h;addresses[count]=cursor;cursor+=bytes;return count++;
}
void jo_sprite_restore_sprite_scale(void){}
void jo_sprite_disable_horizontal_flip(void){flip=0;}
void jo_sprite_enable_horizontal_flip(void){flip=1;}
void jo_sprite_set_palette(int id){assert(id==7);}
void jo_sprite_draw3D2(int id,int x,int y,int z)
{assert(id>=0 && id<count && x>-100 && y>0 && (z==230 || z==231));drawn_ids[draws++%64]=id;}
void jo_clear_screen_line(int line){(void)line;}
void jo_print(int x,int y,const char *s){(void)x;(void)y;(void)s;}
void jo_printf(int x,int y,const char *s,...){(void)x;(void)y;(void)s;}
void mf_street_draw(const int street[5],int palid,int camera){(void)street;(void)palid;(void)camera;}
int main(void)
{
 const int gallery[2][3]={{0,1,2},{3,4,5}};jo_palette palette={7};int a,p,r,f,d,boot;
 for(a=0;a<2;a++)for(p=0;p<3;p++){int id=gallery[a][p];widths[id]=animation_parts[a][0][p].width;heights[id]=animation_parts[a][0][p].height;}
 addresses[5]=0x7fef8u-32;assert(!mf_animation_load(&palette,gallery) && count==6);
 addresses[5]=cursor-((widths[5]*heights[5]+31u)&~31u);
 assert(mf_animation_load(&palette,gallery));boot=count;assert(texture_bytes==351104u+MF_RUN_BYTES+MF_RBV_BYTES+MF_CA_BYTES);
 for(a=0;a<2;a++)for(f=18;f<22;f++)for(d=-1;d<=1;d+=2){draws=0;assert(mf_animation_draw_actor(a,f,100,202,d,230) && draws==4 && !flip);}
 assert(mf_animation_toggle() && mf_animation_active() && count==boot);mf_animation_update(0,MF_UP,1);assert(current_frame(0)==18);mf_animation_draw((int[5]){0},0);
 for(r=0;r<MF_REVIEW_RESOURCES+MF_RBV_NEW+MF_CA_NEW;r++)assert(uploads[r]<=1);
 {
  mf_game game,copy;int t,j,face;memset(&game,0,sizeof(game));
  for(j=0;j<2;j++){game.players[j].active=1;game.players[j].health=40;}
  for(j=0;j<2;j++)for(face=-1;face<=1;face+=2)for(t=1;t<=36;t++) {
   mf_player *p=&game.players[j];p->facing=face;p->attack=t;p->bat=1;game.running_bat[j].active=1;copy=game;draws=0;
   assert(mf_combat_prototype_draw(&game,j,100,202,230)==(MF_BAT_MOMENTUM || t>=6));assert(!memcmp(&copy,&game,sizeof(game)));assert(!flip);
#if MF_BAT_MOMENTUM
   {const mf_polish_piece *part=ca_lower[j][1];int q=0;for(;part->resource>=0;part++,q++)assert(drawn_ids[q]==ca_ids[part->resource]);}
#endif
   game.running_bat[j].active=0;copy=game;assert(mf_combat_prototype_draw(&game,j,100,202,230));assert(!memcmp(&copy,&game,sizeof(game)));
   if(t<=24){p->bat=0;copy=game;assert(mf_combat_prototype_draw(&game,j,100,202,230));assert(!memcmp(&copy,&game,sizeof(game)));}
   p->height=1;assert(!mf_combat_prototype_draw(&game,j,100,202,230));p->height=0;
   p->hurt=1;assert(!mf_combat_prototype_draw(&game,j,100,202,230));p->hurt=0;
  }
  assert(!mf_combat_prototype_draw(&game,-1,100,202,230));
 }
 mf_animation_leave();assert(count==boot);
 puts("PASS combat bank: preflight overflow, exact aligned budget, shared resources, both fighters and mirrors/all attack counters, immutable game state, aerial/hurt fallback, no gallery expansion");return 0;
}
