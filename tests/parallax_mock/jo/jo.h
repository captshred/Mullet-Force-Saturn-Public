#include "../../street_mock/jo/jo.h"
#define JO_FAST_ALLOCATION 0
#define NBG2ON 4
#define NBG2OFF (4ul<<16)
#define PL_SIZE_1x1 0
#define win1_IN 12
void *jo_malloc_with_behaviour(unsigned,int);
typedef void *GfsHn;
typedef int Sint32;
GfsHn GFS_Open(int);
void GFS_GetFileSize(GfsHn,Sint32 *,Sint32 *,Sint32 *);
void GFS_Close(GfsHn);
char *jo_fs_read_file_ptr(const char *,void *,int *);
void slCharNbg2(int,int);
void slPageNbg2(void *,void *,int);
void slPlaneNbg2(int);
void slMapNbg2(void *,void *,void *,void *);
void slPriorityNbg2(int);
void slScrWindow1(unsigned short,unsigned short,unsigned short,unsigned short);
void slScrWindowModeNbg2(unsigned short);
void slScrPosNbg2(int,int);
void slScrDisp(unsigned long);
void jo_print(int,int,const char *);

void jo_clear_screen_line(int);
