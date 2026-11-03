#ifndef MF_SEGA_SOUND_MOCK
#define MF_SEGA_SOUND_MOCK
#include <jo/jo.h>
typedef struct {Uint16 *program,*map; unsigned int program_size,map_size;} SndIniDt;
#define SND_INI_PRG_ADR(x) ((x).program)
#define SND_INI_PRG_SZ(x) ((x).program_size)
#define SND_INI_ARA_ADR(x) ((x).map)
#define SND_INI_ARA_SZ(x) ((x).map_size)
#define SND_RET_SET 0
int SND_StopDsp(void);
int SND_SetCdDaLev(int,int);
int SND_SetTlVl(int);
int SND_SetSeqVl(int,int,int);
int SND_StartSeq(int,int,int,int);
int SND_StopSeq(int);
int SND_PauseSeq(int);
int SND_ContSeq(int);
void SND_Init(SndIniDt *);
int SND_ChgMap(int);
#endif
