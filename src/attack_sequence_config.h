#ifndef MF_ATTACK_SEQUENCE_CONFIG_H
#define MF_ATTACK_SEQUENCE_CONFIG_H
#include "jab_config.h"
#ifndef MF_ATTACK_SEQUENCE
#define MF_ATTACK_SEQUENCE 0
#endif
#if MF_ATTACK_SEQUENCE
/* Pure presentation selection. Active/recovery windows remain in game.c.
   weapon: -1 baked/none,0 approved carry,1 rear-horizontal,2 rear-down. */
static int mf_sequence_key(int attack,int bat,int phase,int *weapon)
{
    *weapon=-1;
#if MF_JAB_COHESION
    if(!bat)return attack<=10?0:attack<=16?-2:-1;
    if(attack>=18)return -1; /* Remove only the rejected final follow-through. */
#else
    if(!bat)return attack<=10?0:-1;
#endif
    if(attack<7){*weapon=attack<3?0:attack<5?1:2;return 4+phase;}
    if(attack<12)return 2;
    if(attack<18)return 1;
    return 3;
}
#endif
#endif
