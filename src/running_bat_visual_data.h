#ifndef MF_RUNNING_BAT_VISUAL_DATA_H
#define MF_RUNNING_BAT_VISUAL_DATA_H
#define MF_RBV_NEW 10
#define MF_RBV_BYTES 8512u
static const mf_polish_resource rbv_resources[MF_RBV_NEW]={
{"RBV00.TGA",32,36,1152u},
{"RBV01.TGA",24,23,576u},
{"RBV02.TGA",48,31,1504u},
{"RBV03.TGA",56,9,512u},
{"RBV04.TGA",32,23,736u},
{"RBV05.TGA",32,21,672u},
{"RBV06.TGA",56,11,640u},
{"RBV07.TGA",24,23,576u},
{"RBV08.TGA",48,31,1504u},
{"RBV09.TGA",56,11,640u}};
static const short rbv_hands[2][4][2]={{{43, 43}, {41, 37}, {43, 43}, {37, 40}}, {{39, 43}, {41, 41}, {39, 37}, {40, 40}}};
static const short rbv_carry[3]={0,22,30};
static const short rbv_overlay[2][7][3]={{{-1,-31,-87},{1,-35,-42},{2,27,-47},{3,32,-56},{4,27,-86},{5,-36,-84},{6,-33,-69}},{{-1,-31,-87},{7,-35,-42},{8,27,-47},{3,32,-56},{4,27,-86},{5,-36,-84},{9,-33,-69}}};
#endif
