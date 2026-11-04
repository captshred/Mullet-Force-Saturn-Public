#ifndef MF_STREET_H
#define MF_STREET_H
#include <jo/jo.h>
typedef struct {
    int code,step,palette_id,root_executable,root_street;
    int file_id[3],length[3],read_mask,auto_result;
    unsigned long bitmap,cells,map;
} mf_street_diagnostic;
const mf_street_diagnostic *mf_street_diagnostics(void);
void mf_street_diagnostic_draw(int line);
void mf_street_animate(unsigned vblank);
int mf_street_load(jo_palette *palette,int sprites[5]);
void mf_street_draw(const int sprites[5],int palette_id,int camera);
#endif
