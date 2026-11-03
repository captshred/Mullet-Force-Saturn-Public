#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/gallery.c"

static unsigned next_address,addresses[7];
static int widths[7],heights[7],uploads,bank,flip,draws;
static jo_palette *loading;
static int trace[9][6];
void *jo_sprite_get_raw_data(int id) { assert(id>=0 && id<=6);return (void *)(JO_VDP1_VRAM+addresses[id]); }
int jo_sprite_get_width(int id) { return widths[id]; }
int jo_sprite_get_height(int id) { return heights[id]; }
void jo_create_palette(jo_palette *p) {p->id=7;}
void jo_set_tga_default_palette(jo_palette *p) {loading=p;}
int jo_sprite_add_tga(void *root,const char *name,int transparent)
{
    int actor=uploads/3,part=uploads%3,id=++uploads;
    const mf_gallery_piece *p=&gallery_parts[actor][part];
    (void)root;assert(loading && loading->id==7 && transparent==1);
    assert(!strcmp(name,p->name));
    widths[id]=p->width;heights[id]=p->height;addresses[id]=next_address;
    next_address+=aligned(p->width*p->height);return id;
}
void jo_sprite_restore_sprite_scale(void) {}
void jo_sprite_disable_horizontal_flip(void) {flip=0;}
void jo_sprite_enable_horizontal_flip(void) {flip=1;}
void jo_sprite_set_palette(int id) {bank=id;}
void jo_sprite_draw3D2(int id,int x,int y,int z)
{
    assert(draws<9);trace[draws][0]=id;trace[draws][1]=x;trace[draws][2]=y;
    trace[draws][3]=z;trace[draws][4]=bank;trace[draws++][5]=flip;
}
void jo_print(int x,int y,const char *s) {(void)x;(void)y;(void)s;}
void jo_printf(int x,int y,const char *s,...) {(void)x;(void)y;(void)s;}
void mf_street_draw(const int street[5],int palette_id,int camera)
{
    int i;
    assert(camera==280);jo_sprite_set_palette(palette_id);
    for(i=0;i<5;i++) {
        int x=i*128-camera;
        if(x>-128 && x<320)jo_sprite_draw3D2(street[i],x,0,500);
    }
}

int main(void)
{
    const int street[5]={101,102,103,104,105};
    const int right[6][2]={{72,122},{60,142},{51,198},{203,122},{193,142},{185,198}};
    const int left[6][2]={{68,122},{56,142},{49,198},{209,122},{195,142},{179,198}};
    int i;
    widths[0]=256;heights[0]=40;addresses[0]=0x10000+445152-20480;
    next_address=0x10000+445152;
    assert(mf_gallery_load(0));assert(uploads==6 && !loading);
    assert(texture_bytes==455936 && next_address==0x10000+455936);
    mf_gallery_draw(street,1);assert(draws==9 && bank==1 && !flip);
    for(i=0;i<3;i++)assert(trace[i][0]==103+i && trace[i][4]==1 && !trace[i][5]);
    for(i=0;i<6;i++) {
        assert(trace[i+3][0]==i+1 && trace[i+3][1]==right[i][0] && trace[i+3][2]==right[i][1]);
        assert(trace[i+3][3]==230 && trace[i+3][4]==7 && !trace[i+3][5]);
    }
    assert(mf_gallery_update(MF_A));draws=0;mf_gallery_draw(street,1);
    for(i=0;i<6;i++)assert(trace[i+3][1]==left[i][0] && trace[i+3][2]==left[i][1] && trace[i+3][5]);
    assert(!flip && bank==1);
    assert(!mf_gallery_update(MF_START));assert(!mf_gallery_active());
    /* The same unchanged gallery loader after moving 153600 bytes to VDP2. */
    uploads=0;addresses[0]=0x10000+291552-20480;next_address=0x10000+291552;
    assert(mf_gallery_load(0));assert(uploads==6 && texture_bytes==302336);
    /* Budget rejection happens before any gallery uploads, not after overflow. */
    uploads=0;addresses[0]=0x10000+458488-20480;
    assert(!mf_gallery_load(0) && uploads==0);
    puts("PASS: actual gallery C loader/draw calls, shared palette, native positions, mirror padding, render-state restore, exit and pre-upload overflow guard.");
    return 0;
}
