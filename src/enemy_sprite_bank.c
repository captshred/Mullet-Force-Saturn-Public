#include "build-info.h"
#include "enemy_sprite_bank.h"
#if MF_ENEMY_SPRITE_BANKS
static const mf_enemy_bank_spec *live,*pending;
static jo_palette *shared;
static unsigned palette_lock,prefix_lock,last_tick;
static mf_enemy_bank_info info;
static unsigned mix(unsigned h,unsigned v){return (h^v)*16777619u;}
static unsigned end_of(int id)
{
    unsigned bpp;
    if(id<0 || id>=JO_MAX_SPRITE)return 0;
    if(__jo_sprite_pic[id].color_mode==COL_256)bpp=1;
    else if(__jo_sprite_pic[id].color_mode==COL_32K)bpp=2;
    else return 0;
    return (unsigned)((unsigned long)jo_sprite_get_raw_data(id)-JO_VDP1_VRAM)+
        ((jo_sprite_get_width(id)*jo_sprite_get_height(id)*bpp+31u)&~31u);
}
static unsigned palette_hash(void)
{
    unsigned i,h=2166136261u;
    for(i=0;i<255;i++)h=mix(h,shared->data[i]);
    return h;
}
static unsigned prefix_hash(void)
{
    int i;unsigned h=2166136261u;
    for(i=0;i<MF_ENEMY_PREFIX_DEFS;i++) {
        const jo_texture_definition *d=&__jo_sprite_def[i];
        h=mix(h,d->width);h=mix(h,d->height);h=mix(h,d->adr);h=mix(h,d->size);
        h=mix(h,__jo_sprite_pic[i].index);h=mix(h,__jo_sprite_pic[i].color_mode);
        h=mix(h,(unsigned)((unsigned long)__jo_sprite_pic[i].data-JO_VDP1_VRAM));
    }
    return h;
}
static int failure(unsigned reason)
{
    if(live)live->invalidate();
    if(pending)pending->invalidate();
    live=0;info.error=reason;info.state=MF_BANK_FAILED;return 0;
}
static int valid_spec(const mf_enemy_bank_spec *b)
{return b && b->kind && b->definitions && b->bytes && b->install && b->invalidate && b->validate &&
 b->definitions<=JO_MAX_SPRITE-MF_ENEMY_PREFIX_DEFS && b->bytes<=458488u-MF_ENEMY_PREFIX_BYTES;}
static int install(const mf_enemy_bank_spec *b,int boot)
{
    int ok;unsigned used;
    info.state=MF_BANK_LOADING;b->invalidate();pending=b;
    ok=b->install(boot?shared:JO_NULL); /* Never reload palette 4 during a swap. */
    used=end_of(jo_get_last_sprite_id());
    if(used>=0x10000u && used-0x10000u>info.peak_bytes)info.peak_bytes=used-0x10000u;
    if(!ok || jo_get_last_sprite_id()!=MF_ENEMY_PREFIX_DEFS+(int)b->definitions-1 ||
       used!=0x10000u+MF_ENEMY_PREFIX_BYTES+b->bytes || !b->validate(MF_ENEMY_PREFIX_DEFS)) {
        JO_VDP1_PTMR=0; /* Boot has no submitted sprite consumers; swaps are already stopped. */
        b->invalidate();
        if(jo_get_last_sprite_id()>=MF_ENEMY_PREFIX_DEFS)jo_sprite_free_from(MF_ENEMY_PREFIX_DEFS);
        return failure(ok?MF_BANK_HANDLES:MF_BANK_LOAD);
    }
    if(prefix_hash()!=prefix_lock)return failure(MF_BANK_PREFIX);
    if(!boot && palette_hash()!=palette_lock)return failure(MF_BANK_PALETTE);
    palette_lock=palette_hash();live=b;pending=0;info.error=0;
    ++info.generation;info.state=MF_BANK_READY;return 1;
}
int mf_enemy_bank_boot(const mf_enemy_bank_spec *b,jo_palette *palette)
{
    if(info.state!=MF_BANK_COLD)return 0;
    if(jo_get_last_sprite_id()!=MF_ENEMY_PREFIX_DEFS-1 ||
       end_of(MF_ENEMY_PREFIX_DEFS-1)!=0x10000u+MF_ENEMY_PREFIX_BYTES)return failure(MF_BANK_PREFIX);
    if(!palette || palette->id!=4 || !palette->data)return failure(MF_BANK_PALETTE);
    if(!valid_spec(b))return failure(MF_BANK_CAPACITY);
    shared=palette;prefix_lock=prefix_hash();return install(b,1);
}
int mf_enemy_bank_prepare(const mf_enemy_bank_spec *b,const mf_game *g,unsigned now)
{
    int i;
    if(info.state!=MF_BANK_READY || !valid_spec(b) || !g)return 0;
    if(!g->started || g->paused || g->stage!=MF_STAGE_LEVEL1)return 0;
    for(i=0;i<MF_ENEMIES;i++)if(g->enemies[i].state!=MF_ENEMY_ABSENT)return 0;
    if(prefix_hash()!=prefix_lock)return failure(MF_BANK_PREFIX);
    if(palette_hash()!=palette_lock)return failure(MF_BANK_PALETTE);
    if(jo_get_last_sprite_id()!=MF_ENEMY_PREFIX_DEFS+(int)live->definitions-1 ||
       end_of(jo_get_last_sprite_id())!=0x10000u+MF_ENEMY_PREFIX_BYTES+live->bytes)return failure(MF_BANK_HANDLES);
    pending=b;live->invalidate();info.state=MF_BANK_DRAIN;info.drains=0;last_tick=now;
    return 1;
}
unsigned mf_enemy_bank_service(unsigned now)
{
    unsigned wait;const mf_enemy_bank_spec *next;
    if(info.state!=MF_BANK_DRAIN)return info.state;
    if(now==last_tick)return info.state;
    last_tick=now;
    if(++info.drains<3)return info.state;
    /* Called once/core callback after three sprite-free slSynch barriers.
       Stop auto restarts and confirm actual VDP1 completion before freeing. */
    JO_VDP1_PTMR=0;
    for(wait=0;wait<1000000u && !(JO_VDP1_EDSR&2u);++wait){}
    if(!(JO_VDP1_EDSR&2u)){failure(MF_BANK_VDP1);return info.state;}
    if(prefix_hash()!=prefix_lock || palette_hash()!=palette_lock){failure(MF_BANK_PREFIX);return info.state;}
    next=pending;
    jo_sprite_free_from(MF_ENEMY_PREFIX_DEFS);live=0;
    if(jo_get_last_sprite_id()!=MF_ENEMY_PREFIX_DEFS-1 ||
       end_of(MF_ENEMY_PREFIX_DEFS-1)!=0x10000u+MF_ENEMY_PREFIX_BYTES){failure(MF_BANK_PREFIX);return info.state;}
    if(install(next,0)) {
        ++info.swaps;
        /* Approved SGL automatic frame-change policy, not a sampled PTMR. */
        JO_VDP1_PTMR=2;
    }
    return info.state;
}
int mf_enemy_bank_ready(void){return info.state==MF_BANK_READY;}
const mf_enemy_bank_spec *mf_enemy_bank_current(void){return mf_enemy_bank_ready()?live:0;}
unsigned mf_enemy_bank_bytes(void){return live && info.state!=MF_BANK_RETIRED?live->bytes:0u;}
const mf_enemy_bank_info *mf_enemy_bank_diagnostics(void){return &info;}
void mf_enemy_bank_retire(void)
{
    if(live)live->invalidate();
    if(pending)pending->invalidate();
    live=pending=0;info.state=MF_BANK_RETIRED;
}
#endif
