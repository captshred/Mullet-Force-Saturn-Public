#ifndef MF_JAB_VISUAL_H
#define MF_JAB_VISUAL_H
#include "jab_config.h"
#if MF_JAB_COHESION
/* Native assembly offsets: head+shoulder together, waist, hips, knees, boots.
   Y offsets never increase towards the feet, so joins overlap rather than gap. */
static const signed char jab_offsets[2][2][5][2]={
 {{{2,1},{1,1},{1,1},{1,0},{0,0}},{{3,2},{2,1},{1,1},{1,0},{0,0}}},
 {{{1,1},{1,1},{1,1},{1,0},{0,0}},{{2,1},{1,1},{1,1},{1,0},{0,0}}}
};
#endif
#endif
