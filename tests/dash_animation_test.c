#include <assert.h>
#include <stdio.h>
#include "../src/player_animation.c"
static int calls,last_actor,last_pose;
int mf_animation_draw_actor(int a,int f,int x,int y,int facing,int z)
{(void)x;(void)y;(void)facing;(void)z;++calls;last_actor=a;last_pose=f;return 1;}
int main(void)
{
 mf_game g;int actor,t,count[3]={0,0,0};mf_game_init(&g);
 for(actor=0;actor<2;actor++) {
  g.players[actor].active=1;g.players[actor].health=100;g.players[actor].moving=1;
  for(t=0;t<90;t++){g.players[actor].walk=t;assert(mf_player_animation_pose(&g,actor)==15+(t/10)%3);}
  g.dash[actor].dir=1;g.dash[actor].anim=0;
  for(t=0;t<150;t++){
   g.dash[actor].anim=(g.dash[actor].anim+MF_DASH_ANIM_NUM)%MF_DASH_ANIM_CYCLE;
   assert(mf_player_animation_pose(&g,actor)==15+((7*(t+1))%150)/50);
   if(!actor)++count[mf_player_animation_pose(&g,actor)-15];
   assert(mf_player_animation_draw(&g,actor,100,200,300));assert(last_actor==actor && last_pose>=15 && last_pose<=17);
  }
  g.dash[actor].dir=0;g.players[actor].moving=0;assert(mf_player_animation_pose(&g,actor)==0);
  g.players[actor].attack=1;assert(mf_player_animation_pose(&g,actor)==-1);g.players[actor].attack=0;
 }
 assert(count[0]==50 && count[1]==50 && count[2]==50 && calls==300);
 puts("PASS exact1.4x rational dash phase using the same three resource poses; normal10-tick walk/idle/combat fallback unchanged");return 0;
}
