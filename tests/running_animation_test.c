#include <assert.h>
#include <stdio.h>
#include "../src/player_animation.c"
int mf_animation_draw_actor(int a,int f,int x,int y,int facing,int z)
{(void)a;(void)x;(void)y;(void)facing;(void)z;return f>=18 && f<22;}
int main(void)
{mf_game g;int a,t;mf_game_init(&g);for(a=0;a<2;a++){
 g.players[a].active=1;g.players[a].health=100;g.players[a].moving=1;g.dash[a].dir=1;
 for(t=0;t<96;t++){g.dash[a].anim=(t%24)*7;assert(mf_player_animation_pose(&g,a)==18+(t/6)%4);assert(mf_player_animation_draw(&g,a,100,200,300));}
 g.dash[a].dir=0;for(t=0;t<60;t++){g.players[a].walk=t;assert(mf_player_animation_pose(&g,a)==15+(t/10)%3);}
 g.players[a].moving=0;assert(mf_player_animation_pose(&g,a)==0);g.players[a].bat=1;g.players[a].attack=1;assert(mf_player_animation_pose(&g,a)==-1);
 }puts("PASS four running frames in6-tick order,independent selectors,normal walk/idle/bat fallback unchanged");return 0;}
