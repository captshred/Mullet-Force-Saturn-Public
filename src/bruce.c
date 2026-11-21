#ifdef MF_BRUCE_SATURN
#include "build-info.h"
#endif
#include "bruce.h"

#if MF_BRUCE_RUNTIME
/* Phase 4A.2 open lot starts at 2758, and the doors are centered at 3095.
   Keep Bruce's center on the apron and leave the doorway itself free. */
enum {
    LOT_FIRST = 2758, LOT_RETURN = MF_WORLD_SLOPE_END + 80,
    ARCADE_DOORS = 3095, BRUCE_SPAWN = ARCADE_DOORS - 80, BRUCE_RIGHT = ARCADE_DOORS - 46,
    LANE_BACK = 168, LANE_FRONT = 229, BRUCE_SPAWN_LANE = 203,
    Q = 256
};

static int living(const mf_player *player)
{
    return player->active && player->health > 0;
}

int mf_bruce_approach(mf_bruce *bruce, const mf_game *game)
{
    int first = MF_WORLD_RIGHT, last = MF_WORLD_LEFT, i;
    for (i = 0; i < MF_PLAYERS; ++i) {
        const mf_player *player = &game->players[i];
        if (!living(player)) continue;
        if (player->x / Q < first) first = player->x / Q;
        if (player->x / Q > last) last = player->x / Q;
    }
    if (first < LOT_RETURN) bruce->approach = 0;
    else if (last >= LOT_FIRST) bruce->approach = 1;
    return bruce->approach;
}

static int advance(int position, int goal, int allowance, int speed)
{
    int delta = goal - position;
    if (delta > allowance) return position + (delta - allowance < speed ? delta - allowance : speed);
    if (delta < -allowance) return position - (-delta - allowance < speed ? -delta - allowance : speed);
    return position;
}

void mf_bruce_step(mf_bruce *bruce, const mf_game *game)
{
    int x, y, moving, i;
    const mf_player *target;
    if (!bruce->active) {
        bruce->x = BRUCE_SPAWN * Q;
        bruce->y = BRUCE_SPAWN_LANE * Q;
        bruce->facing = -1;
        bruce->target = -1;
        bruce->active = 1;
        return;
    }
    if (bruce->target < 0 || !living(&game->players[bruce->target]) || --bruce->retarget <= 0) {
        int best_distance = 0;
        bruce->target = -1;
        for (i = 0; i < MF_PLAYERS; ++i) {
            const mf_player *player = &game->players[i];
            int dx, dy, distance;
            if (!living(player)) continue;
            dx = (player->x - bruce->x) / Q;
            dy = (player->y - bruce->y) / Q;
            distance = dx * dx + dy * dy;
            if (bruce->target < 0 || distance < best_distance) {
                best_distance = distance;
                bruce->target = i;
            }
        }
        bruce->retarget = 24;
    }
    x = bruce->x;
    y = bruce->y;
    if (bruce->target >= 0) {
        target = &game->players[bruce->target];
        if (target->x != x) bruce->facing = target->x > x ? 1 : -1;
        x = advance(x, target->x, 56 * Q, 144);
        y = advance(y, target->y, 7 * Q, 96);
        if (x < LOT_FIRST * Q) x = LOT_FIRST * Q;
        if (x > BRUCE_RIGHT * Q) x = BRUCE_RIGHT * Q;
        if (y < LANE_BACK * Q) y = LANE_BACK * Q;
        if (y > LANE_FRONT * Q) y = LANE_FRONT * Q;
    }
    moving = x != bruce->x || y != bruce->y;
    bruce->animation = moving == bruce->moving ? bruce->animation + 1 : 0;
    /* Approved hold times rounded to NTSC ticks: walk 12/10/13, idle 22/22. */
    if (bruce->animation >= (moving ? 35 : 44)) bruce->animation = 0;
    bruce->moving = moving;
    bruce->x = x;
    bruce->y = y;
}

int mf_bruce_pose(const mf_bruce *bruce)
{
    if (!bruce->moving) return bruce->animation / 22;
    return 2 + (bruce->animation >= 12) + (bruce->animation >= 22);
}

#ifdef MF_BRUCE_SATURN
typedef struct {
    const char *name;
    short width, height, anchor_x, anchor_y;
} bruce_frame;
#include "bruce_bank_data.h"

static jo_palette *colors;
static unsigned short saved_colors[255];
static int ids[BRUCE_DEFS], resident, palette_owned;

void mf_bruce_use_palette(jo_palette *palette)
{
    colors = palette;
}

void mf_bruce_restore_palette(void)
{
    int i;
    if (!palette_owned) return;
    for (i = 0; i < 255; ++i) colors->data[i] = saved_colors[i];
    palette_owned = 0;
}

static void invalidate(void)
{
    int i;
    resident = 0;
    for (i = 0; i < BRUCE_DEFS; ++i) ids[i] = -1;
}

static int install(jo_palette *shared)
{
    int i;
    if (shared || !colors || colors->id != 2 || !colors->data || palette_owned ||
        MF_ENEMY_PREFIX_BYTES + BRUCE_BYTES + 49152u > 458488u) return 0;
    jo_set_tga_default_palette(JO_NULL);
    for (i = 0; i < BRUCE_DEFS; ++i) {
        ids[i] = jo_sprite_add_tga("BRUCE", bruce_frames[i].name, 1);
        if (ids[i] < 0) return 0;
    }
    for (i = 0; i < 255; ++i) {
        saved_colors[i] = colors->data[i];
        colors->data[i] = bruce_colors[i];
    }
    palette_owned = 1;
    resident = 1;
    return 1;
}

static int validate(int first)
{
    int i;
    unsigned end = 0x10000u + MF_ENEMY_PREFIX_BYTES;
    if (!resident || !palette_owned) return 0;
    for (i = 0; i < 255; ++i)
        if (colors->data[i] != bruce_colors[i]) return 0;
    for (i = 0; i < BRUCE_DEFS; ++i) {
        int id = ids[i];
        const bruce_frame *frame = &bruce_frames[i];
        if (id != first + i || jo_sprite_get_width(id) != frame->width ||
            jo_sprite_get_height(id) != frame->height || __jo_sprite_pic[id].color_mode != COL_256 ||
            (unsigned long)jo_sprite_get_raw_data(id) - JO_VDP1_VRAM != end) return 0;
        end += (frame->width * frame->height + 31u) & ~31u;
    }
    return end == 0x10000u + MF_ENEMY_PREFIX_BYTES + BRUCE_BYTES &&
           end + 49152u <= 0x10000u + 458488u;
}

const mf_enemy_bank_spec mf_bruce_bank_spec = {
    3, BRUCE_DEFS, BRUCE_BYTES, install, invalidate, validate
};

void mf_bruce_draw(const mf_bruce *bruce, int x, int ground, int depth)
{
    int pose = mf_bruce_pose(bruce);
    const bruce_frame *frame = &bruce_frames[pose];
    if (!resident || !bruce->active) return;
    jo_sprite_set_palette(colors->id);
    if (bruce->facing < 0) jo_sprite_enable_horizontal_flip();
    jo_sprite_draw3D2(ids[pose], x - (bruce->facing > 0 ? frame->anchor_x : frame->width - frame->anchor_x),
                     ground - frame->anchor_y, depth);
    jo_sprite_disable_horizontal_flip();
}
#endif
#endif
