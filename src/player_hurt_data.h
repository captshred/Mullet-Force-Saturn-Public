#ifndef MF_PLAYER_HURT_DATA_H
#define MF_PLAYER_HURT_DATA_H
#define MF_PH_BYTES 31584u
#define MF_PH_NEW 10
#define MF_PH_REPLACED 5120u
static const mf_polish_resource ph_resources[MF_PH_NEW]={
{"PH00.TGA",80,42,3360u},
{"PH01.TGA",56,42,2368u},
{"PH02.TGA",56,38,2144u},
{"PH03.TGA",80,44,3520u},
{"PH04.TGA",80,40,3200u},
{"PH05.TGA",88,46,4064u},
{"PH06.TGA",64,48,3072u},
{"PH07.TGA",56,44,2464u},
{"PH08.TGA",88,44,3872u},
{"PH09.TGA",88,40,3520u},
};
static const mf_polish_piece ph_upper[2][3]={
{{0,25,7,80,42},{1,38,10,56,42},{2,41,14,56,38}},
{{5,22,2,88,46},{6,35,5,64,48},{7,39,8,56,44}},
};
static const mf_polish_piece ph_lower[2][2]={
{{3,25,48,80,44},{4,26,52,80,40}},
{{8,23,48,88,44},{9,23,52,88,40}},
};
#endif
