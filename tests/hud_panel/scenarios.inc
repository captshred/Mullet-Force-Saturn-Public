static void hud_scenarios(void)
{
    static const int hp[]={0,1,25,50,99,100},kills[]={0,39,40};
    int join,mode,h,k,debug,j,v;
    cleanup_context=8;
    for(join=0;join<2;join++)for(mode=0;mode<5;mode++)for(h=0;h<6;h++)for(k=0;k<3;k++)for(debug=0;debug<2;debug++) {
        reset_scene(0,1);game.players[1].active=join;
        for(j=0;j<2;j++) {
            game.players[j].health=hp[(h+j)%6];game.players[j].defeated=120;
            game.enemies[j]=(mf_enemy){.x=(100+j*140)*256,.y=202*256,.hp=(h+j)%7,.state=(h+j)%7?MF_ENEMY_ACTIVE:MF_ENEMY_ABSENT,.facing=1};
        }
        game.score=k==0?0:k==1?12345:999999;game.stage_kills=kills[k];game.debug=debug;
        if(mode==1)game.started=0;
        if(mode==2)game.paused=1;
        if(mode>=3)game.stage=mode==3?MF_STAGE_CLEAR:MF_STAGE_LEVEL2_ENTRY;
        render();
    }
    /* Every health-bar fill endpoint, including zero and Chuck's width 88. */
    cleanup_context=16;
    for(v=0;v<=100;v++) {
        cleanup_frame();health_bar(16,25,80,v,100);health_bar(216,25,88,v,100);
    }
    for(v=0;v<=MF_ENEMY_MAX_HP;v++) {
        cleanup_frame();health_bar(16,50,80,v,MF_ENEMY_MAX_HP);health_bar(224,50,80,v,MF_ENEMY_MAX_HP);
    }
}
