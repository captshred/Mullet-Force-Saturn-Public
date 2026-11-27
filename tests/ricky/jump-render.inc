extern unsigned bank_mock_palette_hash(void);
static void check_ricky_bank(void)
{
#if MF_NOAH_RUN && !MF_RICKY_FULL_ART
 const int poses = 23;
 const unsigned bytes = 106112;
#else
 const int poses = 25;
 const unsigned bytes = 114048;
#endif
 assert(mf_enemy_bank_current() == &mf_ricky_bank_spec);
 assert(jo_get_last_sprite_id() + 1 == MF_ENEMY_PREFIX_DEFS + MF_ENEMY_CP_DEFS + poses);
 assert(mf_enemy_bank_diagnostics()->peak_bytes == MF_ENEMY_PREFIX_BYTES + MF_ENEMY_CP_BYTES + bytes);
 for (int pose = 0; pose < 25; ++pose)
  assert(mf_ricky_draw_pose(pose, 1, 100, 200, 200) == (pose < poses));
 for (int slot = 0; slot < MF_ENEMIES; ++slot) {
  for (int state = MF_ENEMY_ABSENT; state <= MF_ENEMY_DYING; ++state)
   for (int jump = 0; jump <= 1; ++jump)
    for (int punch = 0; punch <= 1; ++punch)
     for (int counter = 0; counter < 36; ++counter) {
      game.enemies[slot].state = state;
      game.enemies[slot].walk = game.enemies[slot].timer = game.ticks = counter;
      game.ricky_jump[slot].active = jump;
      game.ricky_punch[slot] = punch;
      int pose = mf_ricky_pose(&game, slot);
      assert(state == MF_ENEMY_ABSENT ? pose == -1 : pose >= 0 && pose < 23);
     }
 }
 printf("PASS Ricky bank: %d poses, %u bytes, gameplay poses below 23\n", poses, bytes);
}

int main(void) {
 load_assets();assert(!asset_error);unsigned hash=bank_mock_palette_hash();check_ricky_bank();
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
