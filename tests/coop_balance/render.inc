int main(void) {
 load_assets();assert(!asset_error);mf_game_init(&game);game.started=1;
 /* Both heroes, a running bat, sustained flame, three live enemies, Ricky
    airborne chain, independent fire palettes/embers, impact and all drums. */
 for(int ricky=0;ricky<MF_ENEMIES;ricky++)for(int attacker=0;attacker<MF_PLAYERS;attacker++)for(int tick=0;tick<MF_RICKY_JUMP_AIR;tick++) {
  for(int p=0;p<MF_PLAYERS;p++) {
   game.players[p]=(mf_player){.active=1,.health=100,.x=(80+p*160)*256,.y=200*256,.facing=p?-1:1};
   if(p==attacker){game.players[p].attack=MF_FAST_BAT_ACTIVE_FIRST;game.players[p].bat=MF_BAT_RUNNING;game.running_bat[p].active=1;}
   else game.players[p].torch=MF_TORCH_FIRE;
  }
  for(int j=0;j<MF_ENEMIES;j++) {
   game.enemies[j]=(mf_enemy){.hp=6,.state=j==ricky?MF_ENEMY_ACTIVE:MF_ENEMY_WALK,.x=(100+j*60)*256,.y=(190+j*10)*256,.fire_flash=1,.burn=10,.facing=j&1?1:-1,.timer=MF_RICKY_JUMP_AIR-tick};
   game.enemy_class[j]=j==ricky?MF_ENEMY_RICKY:MF_ENEMY_CORPORATE_PUNK;
   game.ricky_jump[j]=(mf_ricky_jump){.active=j==ricky,.height=tick<12?tick*3:(24-tick)*3};
  }
  game.spark=4;game.spark_x=180;game.spark_y=200;game.spark_z=48;game.ticks=tick;
  printf("CASE|%d|%d|%d\n",ricky,attacker,tick);draw_game();
 }
 puts("PASS three-slot mixed-enemy actual renderer, both players, bat/flame/impact/embers and Ricky leap phases");return 0;
}
