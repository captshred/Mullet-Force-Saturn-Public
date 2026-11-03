/* Offline-generated fine-detail92px enemy bank. */
#ifndef MF_CORPORATE_REFINED_DATA_H
#define MF_CORPORATE_REFINED_DATA_H
#define MF_CP_TEXTURE_BYTES 11744u
#define MF_CP_RESOURCES 10
#define MF_CP_PARTS 4
typedef struct {const char *name;short width,height;} mf_cp_resource;
typedef struct {short resource,x,y,width;} mf_cp_piece;
static const mf_cp_resource cp_resources[]={
 {"CP00.TGA",40,22},
 {"CP01.TGA",56,30},
 {"CP02.TGA",48,24},
 {"CP03.TGA",64,16},
 {"CP04.TGA",56,30},
 {"CP05.TGA",56,30},
 {"CP06.TGA",40,24},
 {"CP07.TGA",48,16},
 {"CP08.TGA",40,24},
 {"CP09.TGA",56,16},
};
static const mf_cp_piece cp_poses[6][MF_CP_PARTS]={
 {{0,36,0,40},{1,27,22,56},{2,23,52,48},{3,16,76,64}},
 {{0,36,0,40},{4,27,22,56},{2,23,52,48},{3,16,76,64}},
 {{0,36,0,40},{5,27,22,56},{2,23,52,48},{3,16,76,64}},
 {{0,36,0,40},{1,27,22,56},{6,35,52,40},{7,30,76,48}},
 {{0,36,0,40},{1,27,22,56},{2,23,52,48},{3,16,76,64}},
 {{0,36,0,40},{1,27,22,56},{8,29,52,40},{9,24,76,56}},
};
#endif
