static void reset_scene(int a,int f){int j;memset(&game,0,sizeof game);game.started=1;
 for(j=0;j<2;j++){game.players[j].active=1;game.players[j].health=100;game.players[j].x=(120+j*80)*256;game.players[j].y=202*256;game.players[j].facing=f;}
 for(j=0;j<3;j++){game.drums[j].hp=3;game.drums[j].x=(60+j*80)*256;game.drums[j].y=210*256;}
 (void)a;}
static unsigned cases;
static void render(void){cleanup_frame();mf_player_animation_step(&game);draw_game();cases++;}
int main(void){int a,f,t,m,k;load_assets();assert(!asset_error);cleanup_context=1;
 for(a=0;a<2;a++)for(f=-1;f<=1;f+=2){
  reset_scene(a,f);for(t=0;t<200;t++)render();
  for(m=0;m<2;m++)for(t=0;t<180;t++){reset_scene(a,f);game.players[a].moving=1;game.players[a].walk=t;game.dash[a].dir=m;game.dash[a].anim=t;render();}
  for(m=0;m<3;m++)for(t=1;t<=24;t++){reset_scene(a,f);game.players[a].attack=t;game.combo[a].phase=m;render();}
  for(k=1;k<=4;k++)for(t=1;t<=12;t++){reset_scene(a,f);game.players[a].attack=t;game.players[a].bat=2;game.running_bat[a].active=k;render();}
  for(m=0;m<6;m++)for(t=0;t<=18;t++){reset_scene(a,f);game.players[a].height=24*256;game.players[a].vz=1510-m*600;game.players[a].attack=t;game.players[a].attack_air=t!=0;render();}
  for(t=1;t<=6;t++){reset_scene(a,f);game.players[a].landing=t;render();}
  for(m=0;m<2;m++)for(t=1;t<=24;t++){reset_scene(a,f);game.players[a].attack=t;game.players[a].attack_air=1;game.players[a].landing=m?6:0;render();}
  for(m=1;m<=3;m++)for(t=0;t<120;t++){reset_scene(a,f);game.players[a].torch=m;game.players[a].moving=t%2;game.players[a].walk=t;game.ticks=t;render();}
  for(m=0;m<2;m++)for(t=1;t<=12;t++){reset_scene(a,f);game.players[a].hurt=t;game.players[a].height=m*24*256;render();}
  for(t=1;t<=120;t++){reset_scene(a,f);game.players[a].health=0;game.players[a].defeated=t;render();}
 }
 for(a=0;a<2;a++)for(f=-1;f<=1;f+=2)for(m=1;m<=7;m++)for(t=1;t<=50;t++){
  reset_scene(a,f);game.enemies[a]=(mf_enemy){.x=160*256,.y=202*256,.hp=6,.facing=f,.state=m,.timer=t,.walk=t,.burn=t%2};game.enemy_class[a]=MF_ENEMY_CORPORATE_PUNK;render();mf_corporate_step(&game);
 }
 for(m=0;m<4;m++)for(t=0;t<16;t++){reset_scene(0,1);game.drums[0].hp=m;game.drums[0].flash=t%2;game.drums[0].respawn=t;game.spark=1;game.spark_x=160;game.spark_y=200;game.spark_z=48;spark_explosion=t%2;game.players[0].charge=60;game.ticks=t;render();}
 reset_scene(0,1);game.started=0;render();game.started=1;game.paused=1;render();game.paused=0;game.stage=MF_STAGE_CLEAR;render();game.stage=MF_STAGE_LEVEL2_ENTRY;render();
 reset_scene(0,1);for(a=0;a<2;a++){game.players[a].torch=MF_TORCH_FIRE;game.players[a].moving=1;game.players[a].walk=20;game.enemies[a]=(mf_enemy){.x=(110+a*100)*256,.y=200*256,.hp=6,.facing=1,.state=MF_ENEMY_ACTIVE,.timer=4,.burn=10};}for(a=0;a<3;a++)game.drums[a].flash=1;game.spark=1;game.spark_x=150;game.spark_y=200;game.spark_z=40;render();
 cleanup_context=2;cleanup_frame();mf_gallery_draw(street,street_palette.id);
 cleanup_context=4;mf_animation_toggle();for(m=0;m<2;m++){if(m)mf_animation_update(0,MF_UP,1);for(t=0;t<160;t++){mf_animation_update(0,0,1);cleanup_frame();mf_animation_draw(street,street_palette.id);}}
 audit_finish();fprintf(stderr,"cases=%u\n",cases);return 0;}
