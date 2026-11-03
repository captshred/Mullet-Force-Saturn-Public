#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/animation_preview.c"
static unsigned cursor=0x10000+302336,addresses[120];
static int widths[120],heights[120],count=6,draws,flipped,missing,bad_width;
static int drawn[6],dx[6],dy[6];
void *jo_sprite_get_raw_data(int id){return (void *)(unsigned long)(JO_VDP1_VRAM+addresses[id]);}
int jo_sprite_get_width(int id){return widths[id];}
int jo_sprite_get_height(int id){return heights[id];}
void jo_set_tga_default_palette(jo_palette *p){assert(!p || p->id==7);}
int jo_sprite_add_tga(void *dir,const char *name,int transparent)
{
    int n=count-6,w,h;const char *expected;
    if(n<36) {
        const mf_animation_piece *p=&animation_parts[n/18][1+(n%18)/3][n%3];w=p->width;h=p->height;expected=p->name;
    }else {const mf_polish_resource *p=&polish_resources[n-36];w=p->width;h=p->height;expected=p->name;}
    assert(!dir && transparent==1 && !strcmp(name,expected));
    if(missing)return -1;
    widths[count]=w+bad_width;heights[count]=h;addresses[count]=cursor;cursor+=(w*h+31u)&~31u;return count++;
}
void jo_sprite_restore_sprite_scale(void){}
void jo_sprite_disable_horizontal_flip(void){flipped=0;}
void jo_sprite_enable_horizontal_flip(void){flipped=1;}
void jo_sprite_set_palette(int id){assert(id==7);}
void jo_sprite_draw3D2(int id,int x,int y,int z)
{assert(draws<6 && z==230 && flipped==(facing<0));drawn[draws]=id;dx[draws]=x;dy[draws++]=y;}
void jo_clear_screen_line(int line){assert(line==2 || line==4 || line==6 || (line>=25 && line<30));}
void jo_print(int x,int y,const char *s){(void)x;(void)s;assert(y==2 || (y>=27 && y<=29));}
void jo_printf(int x,int y,const char *s,...){(void)x;(void)y;(void)s;}
void mf_street_draw(const int street[5],int palid,int camera){(void)street;assert(palid==1 && camera==280);}
static void draw_check(void)
{
    int a,p;int street[5]={0};draws=0;mf_animation_draw(street,1);assert(draws==6);
    for(a=0;a<2;a++)for(p=0;p<3;p++) {
        int f=current_frame(a),rid,x,y,w;
        if(polished){const mf_polish_piece *q=&polish_parts[a][f][p];rid=q->resource;x=q->x;y=q->y;w=q->width;}
        else{const mf_animation_piece *q=&animation_parts[a][f][p];rid=a*21+f*3+p;x=q->x;y=q->y;w=q->width;}
        x=facing>0?(a?226:90)-64+x:(a?226:90)+64-x-w;
        assert(drawn[a*3+p]==resource_ids[rid] && dx[a*3+p]==x && dy[a*3+p]==118+y);
    }
}
int main(void)
{
    int a,p,t;const int old[2][3]={{0,1,2},{3,4,5}};jo_palette palette={7};
    for(a=0;a<2;a++)for(p=0;p<3;p++){int id=old[a][p];widths[id]=animation_parts[a][0][p].width;heights[id]=animation_parts[a][0][p].height;}
    addresses[5]=cursor-((widths[5]*heights[5]+31u)&~31u);
    assert(mf_animation_load(&palette,old) && count==42+MF_POLISH_NEW);
    assert(mf_animation_texture_bytes()==355808+MF_POLISH_BYTES);
    for(a=0;a<2;a++)for(p=0;p<3;p++)assert(resource_ids[a*21+p]==old[a][p]);
    mf_animation_toggle();assert(mf_animation_active() && polished);draw_check();
    for(t=0;t<24;t++)mf_animation_update(0,0,1);
    assert(current_frame(0)==1 && current_frame(1)==0);
    mf_animation_toggle();mf_animation_toggle();
    for(t=0;t<720;t++){draw_check();mf_animation_update(0,0,1);}
    assert(current_frame(0)==0 && current_frame(1)==0);
    mf_animation_update(0,MF_UP,0);assert(transition==1 && current_frame(0)==11);
    mf_animation_update(0,0,5);assert(current_frame(0)==10);
    mf_animation_update(0,0,5);assert(!transition && current_frame(0)==4);
    for(t=0;t<60;t++){assert(current_frame(0)==4+(t/5)%6);draw_check();mf_animation_update(0,0,1);}
    phase=7;mf_animation_update(0,MF_UP,0);assert(transition==2);
    mf_animation_update(0,0,6);mf_animation_update(0,0,2);assert(transition==3 && current_frame(0)==10);
    mf_animation_update(0,0,5);assert(current_frame(0)==11);mf_animation_update(0,0,5);assert(!transition && current_frame(0)==0);
    mf_animation_update(0,MF_B,0);assert(paused);mf_animation_update(0,MF_UP,0);assert(walking && !transition);
    mf_animation_update(0,MF_RIGHT,6);assert(current_frame(0)==5);mf_animation_update(0,MF_LEFT,6);assert(current_frame(0)==4);
    mf_animation_update(0,MF_A,0);assert(facing==-1);draw_check();
    mf_animation_update(MF_A|MF_B,MF_B,0);assert(!polished && facing==-1 && paused && current_frame(0)==1);
    mf_animation_update(0,MF_B,0);
    for(t=0;t<30;t++){assert(current_frame(0)==1+(t/5)%6);draw_check();mf_animation_update(0,0,1);}
    mf_animation_update(MF_A|MF_B,MF_A,0);assert(polished && current_frame(0)==4);
    walking=0;paused=1;transition=0;idle_phase[0]=idle_phase[1]=0;
    for(t=0;t<4;t++){mf_animation_update(0,MF_RIGHT,6);assert(current_frame(0)==(t+1)%4 && current_frame(1)==(t+1)%4);draw_check();}
    /* Gameplay shares loaded IDs, palette and exact padded-piece origins. */
    for(a=0;a<2;a++)for(t=0;t<10;t++)for(facing=-1;facing<=1;facing+=2) {
        draws=0;assert(mf_animation_draw_actor(a,t,123,199,facing,230) && draws==3);
        for(p=0;p<3;p++) {
            const mf_polish_piece *q=&polish_parts[a][t][p];
            assert(drawn[p]==resource_ids[q->resource] && dy[p]==199-92+q->y);
            assert(dx[p]==(facing>0?123-64+q->x:123+64-q->x-q->width));
        }
    }
    facing=1;assert(count==42+MF_POLISH_NEW);
    assert(!mf_animation_draw_actor(-1,0,0,0,1,230));
    assert(!mf_animation_draw_actor(0,12,0,0,1,230));
    assert(count==42+MF_POLISH_NEW);mf_animation_leave();assert(!mf_animation_active());
    addresses[5]=0x7fef8-100;count=6;assert(!mf_animation_load(&palette,old) && count==6);
    addresses[5]=0x10000+302336-((widths[5]*heights[5]+31u)&~31u);missing=1;assert(!mf_animation_load(&palette,old) && count==6);missing=0;
    cursor=0x10000+302336;bad_width=8;assert(!mf_animation_load(&palette,old));
    puts("PASS polish preview: original/shared IDs, exact unique texture allocation, both independent breaths, unchanged walk cadence, reversible bridges, pause/step/mirror/comparison, roots and preflight failure guards; no runtime uploads/cache.");
}
