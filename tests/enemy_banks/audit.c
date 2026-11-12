#define mf_music_init audit_unused_music_init
#include "../sprite_audit/stubs.c"
#undef mf_music_init
volatile unsigned short bank_mock_ptmr=2,bank_mock_edsr=2;
static void bank_mock_init(void) __attribute__((constructor));
static void bank_mock_init(void){palette=0;}
int mf_music_init(void){return 1;}
void jo_sprite_free_from(int id)
{
    assert(bank_mock_ptmr==0 && (bank_mock_edsr&2));
    assert(id==138 && count>=id);count=id;
}
