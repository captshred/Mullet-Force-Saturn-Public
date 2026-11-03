#include <assert.h>
#include <stdio.h>
#include "game.h"
int main(void)
{
    mf_game g;mf_player *p;mf_hitbox b;int t;
    mf_game_init(&g);p=&g.players[0];
    for(t=0;t<64;t++){g.ticks=t;assert(mf_player_frame(&g,0)==(t<32?0:1));}
    p->moving=1;for(t=0;t<60;t++){p->walk=t;assert(mf_player_frame(&g,0)==2+(t/5)%6);}p->moving=0;
    for(t=1;t<=24;t++){p->attack=t;assert(mf_player_frame(&g,0)==(t<6?8:(t<=10?9:10)));}
    p->hurt=1;assert(mf_player_frame(&g,0)==8);p->hurt=0;
    p->height=256;assert(mf_player_frame(&g,0)==14);p->attack=0;p->vz=1201;assert(mf_player_frame(&g,0)==11);p->vz=1200;assert(mf_player_frame(&g,0)==12);
    p->height=0;p->landing=6;assert(mf_player_frame(&g,0)==13);p->landing=0;p->health=0;assert(mf_player_frame(&g,0)==13);p->health=100;
    p->x=100*256;p->y=200*256;p->height=10*256;p->facing=1;
    b=mf_player_hurtbox(p);assert(b.left==88 && b.right==112 && b.back==192 && b.front==208 && b.bottom==14 && b.top==94);
    p->bat=0;p->attack_air=0;b=mf_player_attackbox(p);assert(b.left==106 && b.right==152 && b.bottom==40 && b.top==68);
    p->attack_air=1;b=mf_player_attackbox(p);assert(b.right==154 && b.bottom==34 && b.top==55);
    p->bat=1;for(t=1;t<=36;t++) {
        int f=t<6?0:t<12?1:t<14?2:t<17?3:t<20?4:t<28?5:6;
        p->attack=t;assert(mf_bat_frame(p)==f);
        b=mf_player_attackbox(p);assert(b.right==178);
        if(t>=12 && t<=17)assert(b.bottom==(t<14?24:t<17?50:64) && b.top==(t<14?68:t<17?74:100));
    }
    puts("PASS animation contract: both idle holds, six walk holds, punch/jump/hurt/landing/defeat selectors, bat boundaries and preserved 3D collision roots/extents.");
}
