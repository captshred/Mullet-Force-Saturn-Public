/* TEST ONLY, inserted into temporary source by the native demo tool.
   Normal source contains no call to prepare and no automatic section changes. */
volatile unsigned mf_bank_demo_state,mf_bank_demo_swaps,mf_bank_demo_error;
volatile unsigned mf_bank_demo_generation,mf_bank_demo_peak;
static mf_game bank_demo_saved;
static int bank_demo_holding,bank_demo_gap;
static void bank_demo_tick(unsigned now)
{
    const mf_enemy_bank_info *d=mf_enemy_bank_diagnostics();int a;
    if(bank_demo_holding && mf_enemy_bank_ready()) {
        game=bank_demo_saved;bank_demo_holding=0;bank_demo_gap=4;
    }
    if(bank_demo_gap)bank_demo_gap--;
    else if(mf_enemy_bank_ready() && !bank_demo_holding && d->swaps<8 &&
            game.started && !game.paused && game.stage==MF_STAGE_LEVEL1 && game.ticks>=40) {
        bank_demo_saved=game;
        /* The dedicated fixture temporarily removes actors, never production. */
        for(a=0;a<MF_ENEMIES;a++)game.enemies[a].state=MF_ENEMY_ABSENT;
        if(!mf_enemy_bank_prepare(&mf_corporate_bank_spec,&game,now)) {
            mf_bank_demo_error=99;return;
        }
        bank_demo_holding=1;
    }
    d=mf_enemy_bank_diagnostics();mf_bank_demo_state=d->state;mf_bank_demo_swaps=d->swaps;
    mf_bank_demo_generation=d->generation;mf_bank_demo_peak=d->peak_bytes;
    mf_bank_demo_error=d->error;
}
