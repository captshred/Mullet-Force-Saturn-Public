/* TEST ONLY: replaces update in temporary builds, never in the playable image.
   Exercises the real loader/draw_game/SGL/VDP1/font/background composition. */
volatile unsigned mf_hud_fixture_case,mf_hud_fixture_clock;
static void update(void)
{
    static const int health[]={0,1,25,50,99,100},kills[]={0,39,40};
    unsigned c=mf_hud_fixture_clock++/12%180,t=c;
    int count=t%3,h,mode,join,j;t/=3;h=t%6;t/=6;mode=t%5;join=t/5;
    mf_hud_fixture_case=c;
    if(asset_error){draw_asset_diagnostics();return;}
    mf_game_init(&game);game.started=1;game.ticks=0;game.camera=0;
    game.players[1].active=join;
    for(j=0;j<2;j++) {
        game.players[j].x=(100+j*120)*256;game.players[j].y=202*256;
        game.players[j].moving=1;game.players[j].walk=0;game.players[j].facing=j?-1:1;
        game.players[j].health=health[h];game.players[j].defeated=120;
        game.enemies[j]=(mf_enemy){.x=(100+j*140)*256,.y=202*256,.hp=(h+j)%7,.state=(h+j)%7?MF_ENEMY_ACTIVE:MF_ENEMY_ABSENT,.facing=1};
    }
    for(j=0;j<3;j++){game.drums[j].hp=0;game.drums[j].respawn=99;}
    game.score=count==0?0:count==1?12345:999999;game.stage_kills=kills[count];
    if(mode==1)game.started=0;
    if(mode==2)game.paused=1;
    if(mode>=3)game.stage=mode==3?MF_STAGE_CLEAR:MF_STAGE_LEVEL2_ENTRY;
    draw_game();
}
