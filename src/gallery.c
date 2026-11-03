#include "build-info.h"
#if MF_SPRITE_GALLERY
#include <jo/jo.h>
#include "input.h"
#include "gallery.h"
#include "gallery_data.h"
#include "street.h"
#if MF_ANIMATION_PREVIEW
#include "animation_preview.h"
#endif

static jo_palette gallery_palette;
static int pieces[2][3],active=1,facing=1;
static unsigned texture_bytes;
static unsigned aligned(unsigned n) { return (n+31u)&~31u; }
static unsigned texture_end(int id,int bytes_per_pixel)
{
    void *data=jo_sprite_get_raw_data(id);
    return (unsigned)((unsigned long)data-JO_VDP1_VRAM)
        +aligned(jo_sprite_get_width(id)*jo_sprite_get_height(id)*bytes_per_pixel);
}
int mf_gallery_load(int last_rgb_sprite)
{
    unsigned end;
    int actor,part;
    if(last_rgb_sprite<0) return 0;
    end=texture_end(last_rgb_sprite,2);
    /* Check BEFORE uploading; release SDK allocator does not guard overflow. */
    if(end+MF_GALLERY_BYTES>0x7fef8u) return 0;
    jo_create_palette(&gallery_palette);
    if(gallery_palette.id>=8) return 0;
    jo_set_tga_default_palette(&gallery_palette);
    for(actor=0;actor<2;actor++)for(part=0;part<3;part++) {
        const mf_gallery_piece *p=&gallery_parts[actor][part];
        int id=jo_sprite_add_tga(JO_ROOT_DIR,p->name,1);
        if(id<0) { jo_set_tga_default_palette(JO_NULL); return 0; }
        pieces[actor][part]=id;
        if(jo_sprite_get_width(id)!=p->width || jo_sprite_get_height(id)!=p->height
           || texture_end(id,1)>0x7fef8u) {
            jo_set_tga_default_palette(JO_NULL);return 0;
        }
    }
    texture_bytes=texture_end(pieces[1][2],1)-0x10000u;
#if MF_ANIMATION_PREVIEW
    if(!mf_animation_load(&gallery_palette,pieces)){jo_set_tga_default_palette(JO_NULL);return 0;}
    texture_bytes=mf_animation_texture_bytes();
#endif
    jo_set_tga_default_palette(JO_NULL);
    return texture_bytes<=458488u;
}
int mf_gallery_active(void) { return active; }
int mf_gallery_update(unsigned pressed)
{
    if(pressed&MF_A)facing=-facing;
    if(pressed&MF_START)active=0;
    return active;
}
void mf_gallery_draw(const int street[5],int street_palette_id)
{
    int actor,part;
    const int ground=210,centers[2]={90,226};
    /* Same 320x240 viewport, no scaling, same existing street textures. */
    jo_sprite_restore_sprite_scale();jo_sprite_disable_horizontal_flip();
    mf_street_draw(street,street_palette_id,280);
    jo_sprite_set_palette(gallery_palette.id);
    if(facing<0)jo_sprite_enable_horizontal_flip();
    for(actor=0;actor<2;actor++)for(part=0;part<3;part++) {
        const mf_gallery_piece *p=&gallery_parts[actor][part];
        int origin=gallery_width[actor]/2;
        int x=facing>0?centers[actor]-origin+p->x
            :centers[actor]+origin-p->x-p->width;
        jo_sprite_draw3D2(pieces[actor][part],x,ground-88+p->y,230);
    }
    jo_sprite_disable_horizontal_flip();jo_sprite_restore_sprite_scale();
    jo_sprite_set_palette(street_palette_id);
    jo_print(7,2,"MULLET FORCE SPRITE GALLERY");
    jo_print(7,4,"88PX NATIVE / SHARED PALETTE");
#if MF_ANIMATION_PREVIEW
    texture_bytes=mf_animation_texture_bytes();
#endif
    jo_printf(7,6,"VDP1 %u / 458488 BYTES",texture_bytes);
#if MF_PLAYABLE_ANIMATION
    jo_print(4,28,"A MIRROR START HIGH DETAIL GAME");
#else
    jo_print(9,28,"A MIRROR  START ORIGINAL GAME");
#endif
    jo_print(8,29,"BUCK             CHUCK");
}
#endif
