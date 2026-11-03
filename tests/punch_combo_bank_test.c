#define main historical_bank_test
#include "sequence_bank_test.c"
#undef main
int jo_get_last_sprite_id(void){return count-1;}
int main(void)
{
 mf_game g,copy;int a,t,f,k,boot;
 {const int gallery[2][3]={{0,1,2},{3,4,5}};jo_palette pal={7};int j,q;
 for(j=0;j<2;j++)for(q=0;q<3;q++){int id=gallery[j][q];widths[id]=animation_parts[j][0][q].width;heights[id]=animation_parts[j][0][q].height;}
 addresses[5]=cursor-((widths[5]*heights[5]+31u)&~31u);assert(mf_animation_load(&pal,gallery));}
 count=253;last_resource=252;cursor=0x10000+446304;addresses[252]=cursor-32;widths[252]=8;heights[252]=4;
 assert(mf_cross_load());assert(count==255 && cursor==0x10000+453344 && texture_bytes==453344);boot=count;
 assert(mf_cross_load() && count==boot);
 memset(&g,0,sizeof(g));
 for(a=0;a<2;a++)for(f=-1;f<=1;f+=2)for(t=1;t<=28;t++){
  mf_player *p=&g.players[a];p->active=1;p->health=100;p->facing=f;p->attack=t;p->bat=0;g.combo[a].phase=2;draws=0;copy=g;
  assert(mf_combat_prototype_draw(&g,a,100,202,230));assert(!memcmp(&g,&copy,sizeof(g)) && count==255 && !flip);
  if(t<=11){assert(draws==4 && drawn_ids[3]==cross_ids[a]);for(k=0;k<3;k++)assert(drawn_ids[k]==ca_ids[seq_lower[a][k].resource]);}
  else assert(draws==3);
  for(k=0;k<draws;k++)assert(draw_flips[k]==(f<0));
 }
 puts("PASS combo bank: two safe final uploads,255 slots/453344 bytes,exact existing legs,cross/guard/recovery/mirrors,no per-frame uploads,immutable state,idempotent load");return 0;
}
