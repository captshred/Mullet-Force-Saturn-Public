#include "../sound_mock/SEGA_SND.H"
/* Extra declarations match the pinned SEGA_SND.H; Level 1 mock is untouched. */
int SND_CtrlDirMidi(int,int,int,int,int,int);
typedef struct {unsigned short mode;unsigned char stat;} SndSeqStat;
void SND_GetSeqStat(SndSeqStat *,int);
