/* TEST ONLY: draw actual production renderer with controlled pose/classes. */
volatile unsigned mf_hud_fixture_case,mf_hud_fixture_clock;
int mf_ricky_fixture_pose;
static void update(void)
{
    unsigned c=mf_hud_fixture_clock++/12%50;int a;
    mf_hud_fixture_case=c;mf_ricky_fixture_pose=c%25;
    if(asset_error){draw_asset_diagnostics();return;}
    mf_game_init(&game);game.started=1;game.players[1].active=1;
    for(a=0;a<2;a++) {
        game.players[a].x=(35+a*250)*256;game.players[a].y=225*256;
        game.players[a].facing=a?-1:1;
        game.enemies[a]=(mf_enemy){.x=(110+a*120)*256,.y=202*256,.hp=6,.state=MF_ENEMY_IDLE,.facing=a?-1:1};
        game.enemy_class[a]=a || c>=25?MF_ENEMY_RICKY:MF_ENEMY_CORPORATE_PUNK;
    }
    for(a=0;a<3;a++){game.drums[a].hp=0;game.drums[a].respawn=99;}
    draw_game();
}
