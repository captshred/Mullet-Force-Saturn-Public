#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/animation_preview.c"
static unsigned cursor=0x10000+302336,addresses[128];
static int widths[128],heights[128],uploads[MF_REVIEW_RESOURCES],count=6,draws,flip;
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
    assert(rid<MF_REVIEW_RESOURCES && ++uploads[rid]==1);
    widths[count]=w;heights[count]=h;addresses[count]=cursor;cursor+=bytes;return count++;
}
void jo_sprite_restore_sprite_scale(void){}
void jo_sprite_disable_horizontal_flip(void){flip=0;}
void jo_sprite_enable_horizontal_flip(void){flip=1;}
void jo_sprite_set_palette(int id){assert(id==7);}
void jo_sprite_draw3D2(int id,int x,int y,int z)
{assert(id>=0 && id<count && x>-100 && y>0 && z==230);draws++;}
void jo_clear_screen_line(int line){(void)line;}
void jo_print(int x,int y,const char *s){(void)x;(void)y;(void)s;}
void jo_printf(int x,int y,const char *s,...){(void)x;(void)y;(void)s;}
void mf_street_draw(const int street[5],int palid,int camera){(void)street;(void)palid;(void)camera;}
int main(void)
{
    const int gallery[2][3]={{0,1,2},{3,4,5}};jo_palette palette={7};int a,p,r,f,d,boot_count;
    for(a=0;a<2;a++)for(p=0;p<3;p++){
        int id=gallery[a][p];widths[id]=animation_parts[a][0][p].width;heights[id]=animation_parts[a][0][p].height;
    }
    addresses[5]=cursor-((widths[5]*heights[5]+31u)&~31u);
    assert(mf_animation_load(&palette,gallery));boot_count=count;
#if MF_ORIGINAL_THREE_WALK
    assert(texture_bytes==MF_ORIGINAL_THREE_BOOT_BYTES && texture_bytes==351104u);
    for(r=0;r<MF_REVIEW_RESOURCES;r++)assert((resource_ids[r]>=0)==(original_three_required[r]!=0));
    for(a=0;a<2;a++)for(f=15;f<18;f++)for(d=-1;d<=1;d+=2){draws=0;assert(mf_animation_draw_actor(a,f,100,202,d,230) && draws==3 && !flip);}
#else
    assert(texture_bytes==MF_SWAGGER_BOOT_BYTES && texture_bytes==346368u);
    for(r=0;r<MF_REVIEW_RESOURCES;r++)assert((resource_ids[r]>=0)==(swagger_required[r]!=0));
    for(a=0;a<2;a++)for(f=0;f<15;f++)if(f<4 || f>=12)for(d=-1;d<=1;d+=2){
        draws=0;assert(mf_animation_draw_actor(a,f,100,202,d,230) && draws==3 && !flip);
    }
    #endif
    draws=0;assert(!mf_animation_draw_actor(0,9,100,202,1,230) && !draws);
    assert(count==boot_count);
    assert(mf_animation_toggle() && mf_animation_active());
#if MF_ORIGINAL_THREE_WALK
    assert(count==MF_REVIEW_RESOURCES && texture_bytes==427104u);
#else
    assert(count==MF_REVIEW_RESOURCES && texture_bytes==MF_SWAGGER_FULL_BYTES && texture_bytes==439776u);
#endif
    for(a=0;a<2;a++)for(f=4;f<10;f++){draws=0;assert(mf_animation_draw_actor(a,f,100,202,1,230) && draws==3);}
    mf_animation_leave();assert(mf_animation_toggle());mf_animation_leave();assert(count==MF_REVIEW_RESOURCES);
    for(r=0;r<MF_REVIEW_RESOURCES;r++)assert(uploads[r]<=1);
    addresses[last_resource]=0x7fef8u;assert(!mf_animation_toggle() && !mf_animation_active());assert(count==MF_REVIEW_RESOURCES);
    puts("PASS swagger banks: exact compact/full budgets, required-only uploads, shared IDs, no partial unavailable draw, all idle/swagger/six poses, one-shot review expansion, no duplicate uploads, preflight overflow guard.");
    return 0;
}
