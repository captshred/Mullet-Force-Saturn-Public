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

#if MF_NOAH_RUN
char *jo_fs_read_file_in_dir(const char *name, const char *dir, int *length)
{
    char path[128];
    snprintf(path,sizeof(path),"build/cd/%s/%s",dir,name);
    FILE *file=fopen(path,"rb");
    if(!file)return NULL;
    assert(fseek(file,0,SEEK_END)==0);
    *length=(int)ftell(file);
    rewind(file);
    char *data=malloc(*length);
    assert(data && fread(data,1,*length,file)==(size_t)*length);
    fclose(file);
    return data;
}

void slDMACopy(void *source, void *destination, unsigned size)
{
    assert(bank_mock_ptmr==0 && (bank_mock_edsr&2));
    for(int id=0;id<count;id++)if(__jo_sprite_pic[id].data==destination){
        assert(size==bytes[id] && payload_sizes[id]<=size);
        memcpy(payloads[id],source,payload_sizes[id]);
        return;
    }
    assert(!"unknown sprite DMA target");
}

void slDMAWait(void){}
#endif
