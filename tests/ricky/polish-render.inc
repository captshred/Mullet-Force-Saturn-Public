extern int polish_selected_palette(void);
extern unsigned bank_mock_palette_hash(void);
static unsigned warm(unsigned c) {
 unsigned r=(c&31)+10,g=((c>>5)&31)+3,b=((c>>10)&31)/2;
 return 0x8000|(r>31?31:r)|((g>31?31:g)<<5)|(b<<10);
}
int main(void) {
 unsigned short original[255];unsigned palettes;int i,a,flash;
 setbuf(stdout,NULL);load_assets();assert(!asset_error);
 assert(buck_palette.id==2 && chuck_palette.id==3 && enemy_palette.id==4 && burn_palette.id==5 && fire_palette.id==6);
 memcpy(original,buck_palette.data,sizeof original);
 for(i=0;i<255;i++) {
  assert(chuck_palette.data[i]==warm(buck_palette.data[i]));
  assert(burn_palette.data[i]==warm(enemy_palette.data[i]));
 }
 assert(mf_ricky_bank_spec.validate(138));
 buck_palette.data[7]^=1;assert(!mf_ricky_bank_spec.validate(138));buck_palette.data[7]^=1;
 chuck_palette.data[7]^=1;assert(!mf_ricky_bank_spec.validate(138));chuck_palette.data[7]^=1;
 assert(mf_ricky_bank_spec.validate(138));
 palettes=bank_mock_palette_hash();
 /* All 25 poses, both facings; drawing must never write either palette. */
 for(i=0;i<25;i++)for(a=-1;a<=1;a+=2){assert(mf_ricky_draw_pose(i,a,100,200,200));assert(polish_selected_palette()==2);}
 for(a=0;a<2;a++)for(flash=0;flash<2;flash++) {
  game.enemies[a]=(mf_enemy){.state=MF_ENEMY_IDLE,.hp=6,.fire_flash=flash};
  assert(mf_ricky_draw(&game,a,100,200,200));assert(polish_selected_palette()==(flash?3:2));
 }
 assert(!memcmp(original,buck_palette.data,sizeof original) && bank_mock_palette_hash()==palettes);
 /* Independent slot selection includes simultaneous flashes and ember overlays. */
 for(a=0;a<2;a++)for(flash=0;flash<4;flash++) {
  memset(&game,0,sizeof game);game.started=1;
  for(i=0;i<2;i++){game.enemies[i]=(mf_enemy){.hp=6,.state=MF_ENEMY_IDLE,.x=(120+i*70)*256,.y=200*256,.fire_flash=(flash>>i)&1,.burn=10,.facing=1};game.enemy_class[i]=i==a?MF_ENEMY_RICKY:MF_ENEMY_CORPORATE_PUNK;}
  printf("ENEMIES|%d|%d\n",a,flash);draw_game();
 }
 /* Hurt body is identical with/without newly ignited flame. The flame must
    also survive invulnerability blink and disappear for air/death/inactive. */
 for(a=0;a<2;a++)for(i=0;i<7;i++) {
  memset(&game,0,sizeof game);game.started=1;
  mf_player *p=&game.players[a];*p=(mf_player){.active=1,.health=100,.x=120*256,.y=200*256,.facing=-1,.hurt=12,.invulnerable=100};
  if(i)p->torch=MF_TORCH_FIRE;
  if(i==2)p->hurt=0; /* Body blinks, flame still visible. */
  if(i==3){p->health=0;p->defeated=120;}
  if(i==4)p->height=256;
  if(i==5)p->vz=256;
  if(i==6)p->active=0;
  printf("FLAME|%d|%d|%d\n",a,i,flame[(game.ticks/3+a)%4]);draw_game();
 }
 puts("PASS independent enemy flash palettes and hurt/torch rendering fixtures");return 0;
}
