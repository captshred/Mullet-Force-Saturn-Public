#ifndef MF_SOUND_MOCK_H
#define MF_SOUND_MOCK_H
#include <stddef.h>
#include <stdlib.h>
typedef unsigned char Uint8;
typedef unsigned short Uint16;
#define JO_NULL NULL
char *jo_fs_read_file(const char *,int *);
void jo_free(void *);
void slSoundOffWait(void);
void slSoundOnWait(void);
void slDMACopy(void *,void *,unsigned int);
void slDMAWait(void);
void slInitSound(Uint8 *,unsigned int,Uint8 *,unsigned int);
int slDSPOff(void);
int slCDDAOff(void);
int slSndVolume(int);
void slSndFlush(void);
int slBGMOn(int,int,int,int);
int slSoundAllPause(void);
int slSoundAllCont(void);
int slSequenceOff(int);
unsigned char slSequenceOn(int,int,int,int);
#endif
