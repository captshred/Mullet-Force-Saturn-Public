#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/animation_preview.c"
static unsigned cursor=0x10000+302336,addresses[128];
static int widths[128],heights[128],uploads[MF_REVIEW_RESOURCES+MF_RBV_NEW],count=6,draws,flip;
void *jo_sprite_get_raw_data(int id){return (void *)(unsigned long)(JO_VDP1_VRAM+addresses[id]);}
int jo_sprite_get_width(int id){return widths[id];}
int jo_sprite_get_height(int id){return heights[id];}
void jo_set_tga_default_palette(jo_palette *p){assert(!p || p->id==7);}
int jo_sprite_add_tga(void *dir,const char *name,int transparent)
{
    int rid,w,h;unsigned bytes;const char *expected;
    assert(!dir && transparent==1 && count<128);
    for(rid=0;rid<MF_REVIEW_RESOURCES;rid++){
        resource_info(rid,&expected,&w,&h,&bytes);
        if(!strcmp(name,expected))break;
    }
    if(rid==MF_REVIEW_RESOURCES){int v;for(v=0;v<MF_RBV_NEW;v++)if(!strcmp(name,rbv_resources[v].name)){w=rbv_resources[v].width;h=rbv_resources[v].height;bytes=rbv_resources[v].bytes;rid=MF_REVIEW_RESOURCES+v;break;}}
    assert(rid<MF_REVIEW_RESOURCES+MF_RBV_NEW && ++uploads[rid]==1);
    widths[count]=w;heights[count]=h;addresses[count]=cursor;cursor+=bytes;return count++;
}
void jo_sprite_restore_sprite_scale(void){}
void jo_sprite_disable_horizontal_flip(void){flip=0;}
void jo_sprite_enable_horizontal_flip(void){flip=1;}
void jo_sprite_set_palette(int id){assert(id==7);}
void jo_sprite_draw3D2(int id,int x,int y,int z)
{assert(id>=0 && id<count && x>-100 && y>0 && (z==230 || z==231));draws++;}
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
 assert(mf_animation_load(&palette,gallery));boot=count;assert(texture_bytes==351104u+MF_RUN_BYTES+MF_RBV_BYTES);
 for(a=0;a<2;a++)for(f=18;f<22;f++)for(d=-1;d<=1;d+=2){draws=0;assert(mf_animation_draw_actor(a,f,100,202,d,230) && draws==4 && !flip);}
 assert(mf_animation_toggle() && mf_animation_active() && count==boot);mf_animation_update(0,MF_UP,1);assert(current_frame(0)==18);mf_animation_draw((int[5]){0},0);
 for(r=0;r<MF_REVIEW_RESOURCES+MF_RBV_NEW;r++)assert(uploads[r]<=1);
 mf_animation_leave();assert(count==boot);
 puts("PASS visual run bank: exact aligned budget, preflight overflow before upload, shared resources, mirrored three-piece draw, no gallery expansion or duplicate uploads");return 0;
}
