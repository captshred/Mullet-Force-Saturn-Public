#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "corporate_animation.h"
#include "corporate_bank.h"
static int loads,draws;
static int ids[8],xs[8],ys[8];
void jo_set_tga_default_palette(jo_palette *p){(void)p;}
int jo_sprite_add_tga(void *root,const char *name,int key){int i=loads++;(void)root;assert(key==1);assert(!strcmp(name,i<10?cp_resources[i].name:cphq_resources[i-10].name));return i;}
int jo_sprite_get_width(int id){return id<10?cp_resources[id].width:cphq_resources[id-10].width;}
int jo_sprite_get_height(int id){return id<10?cp_resources[id].height:cphq_resources[id-10].height;}
void *jo_sprite_get_raw_data(int id){return (void *)(JO_VDP1_VRAM+0x10000ul+id*4096);}
void jo_sprite_draw3D2(int id,int x,int y,int z){assert(id>=0 && id<14 && draws<8 && z==200);ids[draws]=id;xs[draws]=x;ys[draws++]=y;}
int main(void){mf_game g={0},before;jo_palette pal={4};int a,s,t,face;
 assert(mf_corporate_load(&pal) && loads==14);
 for(a=0;a<2;a++)for(s=1;s<=7;s++)for(t=1;t<=48;t++)for(face=-1;face<=1;face+=2){
  int i;g.enemies[a].state=s;g.enemies[a].timer=t;g.enemies[a].facing=face;before=g;draws=0;
  assert(mf_corporate_draw(&g,a,150,200,200));assert(draws==(s==6 || s==7?1:4));
  for(i=0;i<draws;i++){assert(xs[i]>0 && xs[i]<300 && ys[i]>0 && ys[i]<230);assert(ids[i]<14);}
  assert(!memcmp(&g,&before,sizeof(g)) && loads==14);
 }
 for(t=1;t<=6;t++){g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=t;assert(mf_corporate_pose(&g,0)==7);}
 for(a=0;a<2;a++){g.enemies[a].state=MF_ENEMY_RECOVER;g.enemies[a].timer=MF_ENEMY_RECOVERY_TICKS+a*12;assert(mf_corporate_pose(&g,a)==7);}
 for(t=1;t<=30;t++){g.enemies[0].state=MF_ENEMY_DYING;g.enemies[0].timer=t;assert(mf_corporate_pose(&g,0)==(t>25?8:t>12?9:10));}
 g.enemies[0].state=MF_ENEMY_ABSENT;assert(mf_corporate_pose(&g,0)==-1);assert(mf_corporate_pose(&g,2)==-1);
 puts("PASS HQ enemy: all existing states/timers/both actors/facings; shared 14 uploads, no simulation mutations, exact active and 30-tick defeat mapping");return 0;}
