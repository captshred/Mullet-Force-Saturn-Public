#define jo_sprite_add_tga bank_real_add_tga
#define jo_sprite_draw3D2 bank_real_draw3D2
#include "../hud_panel/trace.c"
#undef jo_sprite_add_tga
#undef jo_sprite_draw3D2
int bank_mock_fail_after=-1,bank_mock_load_count,bank_mock_draws;
int jo_sprite_add_tga(void *dir,const char *name,int transparent)
{
    if(bank_mock_fail_after>=0 && bank_mock_load_count++==bank_mock_fail_after)return -1;
    return bank_real_add_tga(dir,name,transparent);
}
void jo_sprite_draw3D2(int id,int x,int y,int z)
{bank_mock_draws++;bank_real_draw3D2(id,x,y,z);}
unsigned bank_mock_prefix_hash(void)
{
    unsigned h=2166136261u,k;int i;
    for(i=0;i<138;i++)for(k=0;k<payload_sizes[i];k++)h=(h^payloads[i][k])*16777619u;
    return h;
}
unsigned bank_mock_palette_hash(void)
{
    unsigned h=2166136261u,k;int i;
    for(i=1;i<8;i++)for(k=0;k<255;k++)h=(h^all_palettes[i]->data[k])*16777619u;
    return h;
}

volatile unsigned short bank_mock_ptmr=2,bank_mock_edsr=2;
unsigned bank_mock_frees;
void jo_sprite_free_from(int id)
{
    int i;
    assert(bank_mock_ptmr==0 && (bank_mock_edsr&2));
    assert(id==138 && count>=id);bank_mock_frees++;
    for(i=id;i<count;i++){free(payloads[i]);payloads[i]=0;payload_sizes[i]=0;}
    count=id;
    cursor=__jo_sprite_def[id-1].adr*8+((__jo_sprite_def[id-1].width*__jo_sprite_def[id-1].height*(__jo_sprite_pic[id-1].color_mode==COL_256?1:2)+31)&~31);
}
