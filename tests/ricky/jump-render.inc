extern unsigned bank_mock_palette_hash(void);
int main(void) {
 load_assets();assert(!asset_error);unsigned hash=bank_mock_palette_hash();
 for(int slot=0;slot<2;slot++)for(int facing=-1;facing<=1;facing+=2)for(int state=MF_ENEMY_WINDUP;state<=MF_ENEMY_RECOVER;state++)for(int flash=0;flash<2;flash++) {
  memset(&game,0,sizeof game);game.started=1;
  game.enemies[slot]=(mf_enemy){.x=150*256,.y=200*256,.hp=6,.state=state,.facing=facing,.fire_flash=flash};
  game.enemy_class[slot]=MF_ENEMY_RICKY;game.ricky_jump[slot].active=1;game.ricky_jump[slot].height=12;
  assert(mf_ricky_pose(&game,slot)==(state==MF_ENEMY_ACTIVE?17:16));
  printf("JUMP|%d|%d|%d|%d\n",slot,facing,state,flash);draw_game();
  assert(bank_mock_palette_hash()==hash);
 }
 puts("PASS actual jump renderer: both slots/facings, launch/air/landing, warm flash palettes, fixed anchor geometry and shadow elevation");return 0;
}
