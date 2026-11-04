#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <jo/jo.h>
#include "../src/game.c"
#include "arcade_fx.h"
static int draws,ids[8],xs[8],ys[8],zs[8];
void jo_sprite_draw3D2(int id,int x,int y,int z)
{assert(draws<8);ids[draws]=id;xs[draws]=x;ys[draws]=y;zs[draws++]=z;}
static void setup(mf_game *g)
{
    int i;mf_game_init(g);g->started=1;
    for(i=0;i<MF_ENEMIES;i++){g->enemies[i].hp=0;g->enemies[i].state=MF_ENEMY_ABSENT;}
    for(i=0;i<MF_DRUMS;i++)g->drums[i].hp=0;
    for(i=0;i<MF_PLAYERS;i++) {
        mf_player *p=&g->players[i];p->active=1;p->health=100;p->hurt=p->invulnerable=0;
        p->x=(200+i*100)*256;p->y=200*256;p->facing=1;p->attack=6;p->hit_mask=0;
    }
}
int main(void)
{
    mf_game g,copy;unsigned previous[2]={0,0};int lethal,p,t,kind;
    for(p=0;p<2;p++)for(lethal=0;lethal<2;lethal++) {
        setup(&g);g.drums[0].hp=lethal?1:3;
        g.drums[0].x=g.players[p].x+30*256;g.drums[0].y=g.players[p].y;
        player_hits(&g,&g.players[p]);assert(g.events&MF_IMPACT);
        kind=mf_fx_spark_explosion(&g,previous,0);assert(kind==(MF_ARCADE_FX?lethal:0));
        copy=g;draws=0;
        mf_fx_draw_drum(&g.drums[0],17,23,230,200,240);
        mf_fx_draw_spark(&g,17,23,kind,239);
        assert(draws==2 && ids[0]==(MF_ARCADE_FX&&lethal?23:17) && ids[1]==ids[0]);
        assert(xs[0]==214 && ys[0]==160 && zs[0]==239);
        assert(xs[1]==g.spark_x-g.camera-16 && ys[1]==g.spark_y-g.spark_z-16 && zs[1]==239);
        assert(!memcmp(&g,&copy,sizeof(g)));
        g.events=0;assert(mf_fx_spark_explosion(&g,previous,kind)==kind);
    }
    /* Equal world coordinates: enemy is resolved last, so its spark stays LEFT. */
    setup(&g);g.drums[0].hp=1;g.drums[0].x=230*256;g.drums[0].y=200*256;
    g.enemies[0].hp=6;g.enemies[0].state=MF_ENEMY_IDLE;
    g.enemies[0].x=g.drums[0].x;g.enemies[0].y=g.drums[0].y;
    player_hits(&g,&g.players[0]);assert(!g.drums[0].hp && g.enemies[0].hp==5);
    kind=mf_fx_spark_explosion(&g,previous,1);assert(!kind);copy=g;draws=0;
    mf_fx_draw_drum(&g.drums[0],17,23,230,200,240);
    mf_fx_draw_spark(&g,17,23,kind,239);
    assert(draws==2 && ids[0]==(MF_ARCADE_FX?23:17) && ids[1]==17);
    assert(!memcmp(&g,&copy,sizeof(g)));
    /* Player 2's destruction follows player 1's enemy hit in the same tick. */
    setup(&g);g.enemies[0].hp=6;g.enemies[0].state=MF_ENEMY_IDLE;
    g.enemies[0].x=230*256;g.enemies[0].y=200*256;
    g.drums[0].hp=1;g.drums[0].x=330*256;g.drums[0].y=200*256;
    player_hits(&g,&g.players[0]);player_hits(&g,&g.players[1]);
    assert(mf_fx_spark_explosion(&g,previous,0)==MF_ARCADE_FX);
    /* Old hit-mask bits must not reclassify a later world impact. */
    previous[0]=(unsigned)g.players[0].hit_mask;previous[1]=(unsigned)g.players[1].hit_mask;
    assert(!mf_fx_spark_explosion(&g,previous,1));
    /* Every existing flash/respawn predicate, with no new animation clock. */
    for(lethal=0;lethal<2;lethal++)for(t=0;t<24;t++) {
        mf_drum d={0};d.hp=lethal?0:2;d.flash=t<10?10-t:0;d.respawn=t;draws=0;
        mf_fx_draw_drum(&d,17,23,50,100,220);
        assert(draws==((d.flash || (!d.hp && d.respawn<12))?1:0));
    }
    puts(MF_ARCADE_FX?"PASS dual FX: real hit resolution, co-op ordering, simultaneous LEFT/RIGHT draws, unchanged anchors/lifetimes/state":"PASS legacy FX routing and timing");
    return 0;
}
