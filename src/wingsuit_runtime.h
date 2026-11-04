#ifndef MF_WINGSUIT_RUNTIME_H
#define MF_WINGSUIT_RUNTIME_H
#include <jo/jo.h>
#include "input.h"
/* One-way ownership transfer. Level 1 render/update must never run afterward. */
void mf_ws_runtime_begin(int coop,jo_palette *background,unsigned now);
void mf_ws_runtime_frame(const mf_input input[2],unsigned pressed[2],unsigned now);
#endif
