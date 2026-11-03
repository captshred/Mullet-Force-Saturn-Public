#ifndef MF_CORPORATE_BANK_H
#define MF_CORPORATE_BANK_H
#if MF_CORPORATE_REFINED
#include "corporate_refined_data.h"
#else
#include "corporate_data.h"
#define MF_CP_PARTS 3
#endif
#if MF_CP_HQ_COMBAT
#include "corporate_hq_data.h"
#endif
#endif
