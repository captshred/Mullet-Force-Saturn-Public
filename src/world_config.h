#ifndef MF_WORLD_CONFIG_H
#define MF_WORLD_CONFIG_H
#ifndef MF_LEVEL1_WORLD_FLOW
#define MF_LEVEL1_WORLD_FLOW (MF_RICKY_ENEMY && MF_LEVEL1_STAGE_CLEAR)
#endif
#if MF_LEVEL1_WORLD_FLOW
#ifndef MF_WORLD_WIDTH
#define MF_WORLD_WIDTH 3328
#endif
#define MF_WORLD_BEND_X 1920
#define MF_WORLD_SLOPE_END 2560
#define MF_WORLD_HEIGHT 368
#define MF_WORLD_LEFT 26
#define MF_WORLD_RIGHT (MF_WORLD_WIDTH-26)
#define MF_WORLD_CAMERA_MAX (MF_WORLD_WIDTH-320)
#define MF_WORLD_CAMERA_STEP 2
#ifndef MF_WORLD_CHECKPOINTS
#define MF_WORLD_CHECKPOINTS {0,320,640,960,1280}
#endif
#define MF_WORLD_PAIR_SPAN 240
#define MF_ENEMY_WORLD_LEFT (-96)
#define MF_ENEMY_WORLD_RIGHT (MF_WORLD_WIDTH+128)
/* Simulation Y is lane depth relative to the local curb. Keeping that
   coordinate for combat lets actors follow the road without changing reach. */
static inline int mf_world_road_drop(int x) {
    if (x <= MF_WORLD_BEND_X) return 0;
    if (x >= MF_WORLD_WIDTH) x = MF_WORLD_WIDTH;
    if (x >= MF_WORLD_SLOPE_END) x = MF_WORLD_SLOPE_END;
    return (x - MF_WORLD_BEND_X) / 5;
}
static inline int mf_world_camera_y(int camera) {
    /* Follow the leading edge so the near curb stays inside the viewport,
       including when the co-op tether is stretched across the bend. */
    return mf_world_road_drop(camera + 320);
}
static inline int mf_world_screen_y(int x, int lane, int camera) {
    return lane + mf_world_road_drop(x) - mf_world_camera_y(camera);
}
static inline int mf_world_checkpoint(int camera) {
 static const int marks[]=MF_WORLD_CHECKPOINTS;int floor=0;unsigned i;
 for(i=0;i<sizeof(marks)/sizeof(marks[0]);i++)if(marks[i]<=camera && marks[i]<=MF_WORLD_CAMERA_MAX)floor=marks[i];
 return floor;
}
/* Opening columns 0..79 are exact. Prototype continuation reuses only the
   blank-sign/window/brick end of VINYL, not a new storefront or new artwork. */
static inline int mf_world_source_column(int column) {
 return column<80?column:72+(column-80)%8;
}
#else
static inline int mf_world_screen_y(int x, int lane, int camera) {
    (void)x;
    (void)camera;
    return lane;
}
#define MF_WORLD_LEFT 26
#define MF_WORLD_RIGHT 614
#define MF_ENEMY_WORLD_LEFT 26
#define MF_ENEMY_WORLD_RIGHT 614
#endif
#endif
