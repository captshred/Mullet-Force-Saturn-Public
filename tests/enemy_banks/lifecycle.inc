extern unsigned bank_mock_prefix_hash(void),bank_mock_palette_hash(void),bank_mock_frees;
extern int bank_mock_fail_after,bank_mock_load_count,bank_mock_draws;
static int never_valid(int first){(void)first;return 0;}
int main(int argc,char **argv)
{
    jo_texture_definition defs[138];jo_picture_definition pics[138];
    unsigned pixels,palettes,i,tick=20,draws;mf_enemy_bank_spec invalid=mf_corporate_bank_spec;
    int mode=argc>1?argv[1][0]:'0';const mf_enemy_bank_info *d;
    load_assets();assert(!asset_error);assert(mf_enemy_bank_ready());
    assert(mf_enemy_bank_current()==&mf_corporate_bank_spec);
    assert(jo_get_last_sprite_id()==151 && mf_animation_texture_bytes()==257024u);
    memcpy(defs,__jo_sprite_def,sizeof defs);memcpy(pics,__jo_sprite_pic,sizeof pics);
    pixels=bank_mock_prefix_hash();palettes=bank_mock_palette_hash();
    memset(&game,0,sizeof game);
    assert(!mf_enemy_bank_prepare(&mf_corporate_bank_spec,&game,tick));game.started=1;
    game.paused=1;assert(!mf_enemy_bank_prepare(&mf_corporate_bank_spec,&game,tick));game.paused=0;
    game.stage=MF_STAGE_CLEAR;assert(!mf_enemy_bank_prepare(&mf_corporate_bank_spec,&game,tick));game.stage=MF_STAGE_LEVEL1;
    invalid.bytes=458488u;assert(!mf_enemy_bank_prepare(&invalid,&game,tick));
    assert(mf_enemy_bank_ready());
    game.enemies[1].state=MF_ENEMY_DYING;assert(!mf_enemy_bank_prepare(&mf_corporate_bank_spec,&game,tick));
    game.enemies[1].state=MF_ENEMY_ABSENT;
    invalid=mf_corporate_bank_spec;if(mode=='h')invalid.validate=never_valid;
    for(i=0;i<256;i++) {
        assert(mf_enemy_bank_service(tick)==MF_BANK_READY);assert(bank_mock_frees==i);
        assert(mf_enemy_bank_prepare(&invalid,&game,tick));
        assert(!mf_enemy_bank_current());
        draws=bank_mock_draws;game.enemies[0].state=MF_ENEMY_IDLE;
        assert(mf_corporate_draw(&game,0,100,200,200)==1 && bank_mock_draws==(int)draws);
        game.enemies[0].state=MF_ENEMY_ABSENT;
        assert(mf_enemy_bank_service(tick)==MF_BANK_DRAIN);
        assert(mf_enemy_bank_diagnostics()->drains==0);
        tick+=1000;assert(mf_enemy_bank_service(tick)==MF_BANK_DRAIN);
        assert(mf_enemy_bank_service(tick)==MF_BANK_DRAIN);
        assert(mf_enemy_bank_diagnostics()->drains==1 && bank_mock_frees==i);
        assert(mf_enemy_bank_service(++tick)==MF_BANK_DRAIN && bank_mock_frees==i);
        if(mode=='b')bank_mock_edsr=0;
        if(mode=='f'){bank_mock_fail_after=2;bank_mock_load_count=0;}
        mf_enemy_bank_service(++tick);d=mf_enemy_bank_diagnostics();
        if(mode=='b' || mode=='f' || mode=='h') {
            assert(d->state==MF_BANK_FAILED && bank_mock_ptmr==0);
            assert(d->error==(mode=='b'?MF_BANK_VDP1:mode=='h'?MF_BANK_HANDLES:MF_BANK_LOAD));
            assert(bank_mock_frees==(mode=='b'?0:2));
            assert(jo_get_last_sprite_id()==(mode=='b'?151:137));
            assert(!mf_enemy_bank_prepare(&mf_corporate_bank_spec,&game,tick));
            draws=bank_mock_draws;game.enemies[0].state=MF_ENEMY_IDLE;
            assert(mf_corporate_draw(&game,0,100,200,200)==1 && bank_mock_draws==(int)draws);
            game.enemies[0].state=MF_ENEMY_ABSENT;
        }else {
            assert(d->state==MF_BANK_READY && bank_mock_ptmr==2);
            assert(mf_enemy_bank_current()->kind==MF_ENEMY_BANK_CORPORATE);
            assert(jo_get_last_sprite_id()==151 && mf_animation_texture_bytes()==257024u);
            assert(d->swaps==i+1 && d->generation==i+2 && d->peak_bytes==257024u);
        }
        assert(!memcmp(defs,__jo_sprite_def,sizeof defs));assert(!memcmp(pics,__jo_sprite_pic,sizeof pics));
        assert(bank_mock_prefix_hash()==pixels && bank_mock_palette_hash()==palettes);
        if(mode=='b' || mode=='f' || mode=='h')break;
    }
    mf_enemy_bank_retire();assert(!mf_enemy_bank_ready());
    assert(!mf_enemy_bank_prepare(&mf_corporate_bank_spec,&game,tick));
    draws=bank_mock_draws;game.enemies[0].state=MF_ENEMY_IDLE;
    assert(mf_corporate_draw(&game,0,100,200,200)==1 && bank_mock_draws==(int)draws);
    printf("PASS suffix lifecycle mode %c: prefix pixels/metadata/all palettes retained; no stale draws; swaps=%u peak=%u\n",mode,mf_enemy_bank_diagnostics()->swaps,mf_enemy_bank_diagnostics()->peak_bytes);
    return 0;
}
