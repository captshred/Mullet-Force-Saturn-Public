#include "../../sound_mock/jo/jo.h"
/* Actual SGL command constants and variadic queue API from pinned SL_DEF.H. */
#define SND_SEQ_START 0x01
#define SND_SEQ_STOP 0x02
#define SND_SEQ_VOL 0x05
#define SND_MAP_CHG 0x08
#define SND_MIDI_CTRL_DIR 0x09
#define SND_DSP_STOP 0x0c
#define SND_CDDA_LEV 0x80
#define SND_TTL_VOL 0x82
int slSoundRequest(const char *,...);
