#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "corporate_animation.h"
#include "corporate_bank.h"
static int loads,draws,palette_sets,fail_load=-1;
static mf_game game;
static int last_id,last_x,last_y,last_z;
void jo_set_tga_default_palette(jo_palette *p){(void)p;++palette_sets;}
int jo_sprite_add_tga(void *root,const char *name,int key){int i=loads++;(void)root;assert(key==1);assert(!strcmp(name,cp_resources[i].name));return i==fail_load?-1:i;}
int jo_sprite_get_width(int id){return cp_resources[id].width;}
int jo_sprite_get_height(int id){return cp_resources[id].height;}
void *jo_sprite_get_raw_data(int id){return (void *)(JO_VDP1_VRAM+0x10000ul+id*4096);}
void jo_sprite_draw3D2(int id,int x,int y,int z){++draws;last_id=id;last_x=x;last_y=y;last_z=z;}
int main(void)
{
    int a,f,t;jo_palette p={4};mf_game before;
    assert(mf_corporate_load(&p));assert(loads==MF_CP_RESOURCES && palette_sets==2);
    for(a=0;a<2;a++)game.enemies[a].state=MF_ENEMY_IDLE;
    for(t=0;t<110;t++) {
        before=game;mf_corporate_step(&game);assert(!memcmp(&before,&game,sizeof(game)));
        for(a=0;a<2;a++)assert(mf_corporate_pose(&game,a)>=0 && mf_corporate_pose(&game,a)<3);
    }
    game.enemies[0].state=MF_ENEMY_ABSENT;mf_corporate_step(&game);
    game.enemies[0].state=MF_ENEMY_IDLE;
    {int count[3]={0,0,0};for(t=0;t<54;t++){mf_corporate_step(&game);++count[mf_corporate_pose(&game,0)];}assert(count[0]==24 && count[1]==12 && count[2]==18);}
    for(a=0;a<2;a++)for(f=0;f<3;f++)for(t=-1;t<=1;t+=2) {
        const mf_cp_piece *v=&cp_poses[3+f][MF_CP_PARTS-1];
        game.enemies[a].state=MF_ENEMY_WALK;game.enemies[a].walk=f*7;game.enemies[a].facing=t;
        before=game;draws=0;assert(mf_corporate_draw(&game,a,150,200,250));assert(draws==MF_CP_PARTS && last_id==v->resource);
        assert(last_x==(t>0?150-48+v->x:150+48-v->x-v->width));assert(last_y==200-92+v->y && last_z==250);assert(!memcmp(&before,&game,sizeof(game)));
    }
    for(a=MF_ENEMY_WINDUP;a<=MF_ENEMY_DYING;a++){game.enemies[0].state=a;draws=0;assert(!mf_corporate_draw(&game,0,0,0,0) && !draws);}
    assert(mf_corporate_pose(&game,-1)==-1 && mf_corporate_pose(&game,2)==-1);
    assert(loads==MF_CP_RESOURCES && palette_sets==2); /* No loads/allocations in draw/step. */
    loads=0;fail_load=0;assert(!mf_corporate_load(&p));
    puts("PASS Corporate Punk shared loader, failure path, independent presentation, both facings, fallback selection, immutable gameplay state");return 0;
}
