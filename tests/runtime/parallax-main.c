#include <jo/jo.h>
#include "street.h"
#include "parallax.h"
static jo_palette test_palette;static int street[5];
static void draw(void){mf_parallax_update(0,0);mf_parallax_draw();}
void jo_main(void){
 jo_core_init(JO_COLOR_RGB(9,12,29));jo_create_palette(&test_palette);
 if(!mf_street_load(&test_palette,street) || !mf_parallax_load() || !mf_parallax_enter())jo_printf(1,1,"FAILED %d",mf_parallax_error());
 jo_core_add_callback(draw);jo_core_run();
}
