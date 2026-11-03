#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "../src/player_animation.c"
static int calls,seen_actor,seen_pose;
int mf_animation_draw_actor(int a,int f,int x,int y,int face,int z){(void)x;(void)y;(void)face;(void)z;calls++;seen_actor=a;seen_pose=f;return 1;}
int main(void){mf_game g,before;int a,t;mf_game_init(&g);for(a=0;a<2;a++){g.players[a].active=1;g.players[a].health=100;g.players[a].moving=1;g.dash[a].dir=a?-1:1;g.dash[a].anim=(a?1:3)*42;}before=g;mf_player_animation_step(&g);assert(!memcmp(&g,&before,sizeof(g)));for(a=0;a<2;a++){g.dash[a].dir=0;g.running_bat[a].active=1;g.players[a].bat=1;for(t=1;t<6;t++){g.players[a].attack=t;calls=0;assert(mf_player_animation_draw(&g,a,100,202,250));assert(calls==1 && seen_actor==a && seen_pose==18+(a?1:3));}g.players[a].attack=6;calls=0;assert(!mf_player_animation_draw(&g,a,100,202,250) && !calls);g.running_bat[a].active=0;g.players[a].attack=1;assert(!mf_player_animation_draw(&g,a,100,202,250));g.players[a].attack=g.players[a].bat=0;g.players[a].walk=10;assert(mf_player_animation_pose(&g,a)==16);}puts("PASS presentation-only carry/windup bridge,both actors independent,first5ticks only,legacy swing and planted bat fallback unchanged,immutable gameplay");return 0;}
