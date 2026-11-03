/* Offline-generated shared enemy artwork. No gameplay state. */
#ifndef MF_CORPORATE_DATA_H
#define MF_CORPORATE_DATA_H
#define MF_CP_TEXTURE_BYTES 14016u
#define MF_CP_RESOURCES 9
typedef struct {const char *name;short width,height;} mf_cp_resource;
typedef struct {short resource,x,y,width;} mf_cp_piece;
static const mf_cp_resource cp_resources[]={
 {"CP00.TGA",16,12},
 {"CP01.TGA",40,56},
 {"CP02.TGA",48,16},
 {"CP03.TGA",40,56},
 {"CP04.TGA",40,56},
 {"CP05.TGA",48,56},
 {"CP06.TGA",40,16},
 {"CP07.TGA",40,56},
 {"CP08.TGA",48,16},
};
static const mf_cp_piece cp_poses[6][3]={
 {{0,50,8,16},{1,30,20,40},{2,25,76,48}},
 {{0,50,8,16},{3,30,20,40},{2,25,76,48}},
 {{0,50,8,16},{4,30,20,40},{2,25,76,48}},
 {{0,50,8,16},{5,30,20,48},{6,32,76,40}},
 {{0,50,8,16},{1,30,20,40},{2,25,76,48}},
 {{0,50,8,16},{7,30,20,40},{8,27,76,48}},
};
#endif
