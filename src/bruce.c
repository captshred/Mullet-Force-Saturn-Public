#ifdef MF_BRUCE_SATURN
#include "build-info.h"
#endif
#include "bruce.h"

#if MF_BRUCE_RUNTIME
/* Phase 4A.2 open lot starts at 2758, and the doors are centered at 3095.
   Keep Bruce's center on the apron and leave the doorway itself free. */
enum {
    LOT_FIRST = 2758, LOT_RETURN = MF_BRUCE_LOT_RETURN,
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

/* Readability and balance controls for the first playtest, at 60 Hz. */
enum {
    BRUCE_HP = 60, PUNCH_DAMAGE = 24, CHARGE_DAMAGE = 18, SLAM_DAMAGE = 24,
    ENTRANCE_TICKS = 48, ENTRANCE_APEX = 62,
    PUNCH_WINDUP = 26, PUNCH_ACTIVE = 5, PUNCH_END = 53,
    CHARGE_WINDUP = 27, CHARGE_ACTIVE = 30, CHARGE_END = 82,
    SLAM_WINDUP = 18, SLAM_AIR = 32, SLAM_APEX = 44, SLAM_IMPACT = 8,
    SLAM_TOUCHDOWN = SLAM_WINDUP + SLAM_AIR, SLAM_END = SLAM_TOUCHDOWN + SLAM_IMPACT + 8
};
enum {
    POSE_PUNCH = 5, POSE_CHARGE = 8, POSE_SLAM = 11,
    POSE_HIT = 13, POSE_KD = 15, POSE_KNEEL = 18
};

static void enter(mf_bruce *bruce, int state)
{
    bruce->state = state;
    bruce->timer = 0;
    bruce->height = 0;
    bruce->moving = 0;
    bruce->animation = 0;
    bruce->hit_players = 0;
}

static void settle(mf_bruce *bruce, int cooldown)
{
    enter(bruce, MF_BRUCE_READY);
    bruce->cooldown = cooldown;
}

static void effect(mf_bruce *bruce)
{
    bruce->impact = 8;
}

static void entrance(mf_bruce *bruce, const mf_game *game)
{
    int land = game->camera + 248;
    if (land < LOT_FIRST + 80) land = LOT_FIRST + 80;
    if (land > BRUCE_SPAWN) land = BRUCE_SPAWN;
    bruce->land_x = land * Q;
    bruce->start_x = (game->camera + 384) * Q;
    if (bruce->start_x < bruce->land_x + 104 * Q)
        bruce->start_x = bruce->land_x + 104 * Q;
    bruce->x = bruce->start_x;
    bruce->y = BRUCE_SPAWN_LANE * Q;
    bruce->facing = -1;
    bruce->target = -1;
    bruce->active = 1;
    bruce->health = BRUCE_HP;
    enter(bruce, MF_BRUCE_ENTRANCE);
}

static int action_tick(mf_bruce *bruce)
{
    int t;
    if (bruce->state == MF_BRUCE_READY) return 0;
    if (bruce->state == MF_BRUCE_DEFEATED) return 1;
    t = ++bruce->timer;
    switch (bruce->state) {
    case MF_BRUCE_ENTRANCE:
        bruce->x = bruce->start_x + (bruce->land_x - bruce->start_x) * t / ENTRANCE_TICKS;
        bruce->height = 4 * ENTRANCE_APEX * t * (ENTRANCE_TICKS - t) / (ENTRANCE_TICKS * ENTRANCE_TICKS);
        if (t >= ENTRANCE_TICKS) {
            enter(bruce, MF_BRUCE_ENTRANCE_IMPACT);
            effect(bruce);
        }
        break;
    case MF_BRUCE_ENTRANCE_IMPACT:
        if (t >= 8) enter(bruce, MF_BRUCE_RECOVERY);
        break;
    case MF_BRUCE_RECOVERY:
        if (t >= 12) settle(bruce, 34);
        break;
    case MF_BRUCE_PUNCH:
        if (t >= PUNCH_END) settle(bruce, 26);
        break;
    case MF_BRUCE_CHARGE:
        if (t >= CHARGE_END) settle(bruce, 32);
        else if (t >= CHARGE_WINDUP && t < CHARGE_WINDUP + CHARGE_ACTIVE) {
            int next = bruce->x + bruce->facing * 896;
            if (next < LOT_FIRST * Q || next > BRUCE_RIGHT * Q)
                bruce->timer = CHARGE_WINDUP + CHARGE_ACTIVE;
            else
                bruce->x = next;
        }
        break;
    case MF_BRUCE_SLAM:
        if (t >= SLAM_WINDUP && t <= SLAM_TOUCHDOWN) {
            int air = t - SLAM_WINDUP;
            bruce->x = bruce->start_x + (bruce->land_x - bruce->start_x) * air / SLAM_AIR;
            bruce->y = bruce->slam_start_y + (bruce->slam_land_y - bruce->slam_start_y) * air / SLAM_AIR;
            bruce->height = 4 * SLAM_APEX * air * (SLAM_AIR - air) / (SLAM_AIR * SLAM_AIR);
            if (t == SLAM_TOUCHDOWN) effect(bruce);
        }
        if (t >= SLAM_END) settle(bruce, 38);
        break;
    case MF_BRUCE_HURT:
        if (bruce->height > 0) {
            /* Freeze the ground root and finish the interrupted arc safely. */
            bruce->height = bruce->height > 5 ? bruce->height - 5 : 0;
            bruce->timer = 0;
            if (!bruce->height && !bruce->health) enter(bruce, MF_BRUCE_FALL);
            break;
        }
        if (t >= 23) settle(bruce, 18);
        break;
    case MF_BRUCE_FALL: {
        int x = bruce->x + bruce->fall_direction * (14-t) * 24;
        if (x < LOT_FIRST * Q) x = LOT_FIRST * Q;
        if (x > BRUCE_RIGHT * Q) x = BRUCE_RIGHT * Q;
        bruce->x = x;
        bruce->height = t >= 6 ? 9 : 0;
        if (t >= 14) enter(bruce, bruce->health ? MF_BRUCE_DOWN : MF_BRUCE_DEFEATED);
        break;
    }
    case MF_BRUCE_DOWN:
        if (t >= 22) enter(bruce, MF_BRUCE_RISE);
        break;
    case MF_BRUCE_RISE:
        if (t >= 22) settle(bruce, 24);
        break;
    default:
        return 0;
    }
    return 1;
}

int mf_bruce_vulnerable(const mf_bruce *bruce)
{
    return bruce->ready && bruce->active && bruce->health > 0 &&
           !bruce->invulnerable && bruce->state >= MF_BRUCE_READY &&
           bruce->state != MF_BRUCE_FALL && bruce->state != MF_BRUCE_DOWN;
}

void mf_bruce_receive(mf_bruce *bruce, int damage, int bat, int direction)
{
    int armored;
    if (!mf_bruce_vulnerable(bruce)) return;
    bruce->health -= damage;
    if (bruce->health < 0) bruce->health = 0;
    bruce->invulnerable = 12;
    armored = (bruce->state == MF_BRUCE_PUNCH && bruce->timer < PUNCH_WINDUP + PUNCH_ACTIVE) ||
              (bruce->state == MF_BRUCE_CHARGE && bruce->timer < CHARGE_WINDUP + CHARGE_ACTIVE) ||
              (bruce->state == MF_BRUCE_SLAM && bruce->timer < SLAM_TOUCHDOWN + SLAM_IMPACT);
    /* Player contact resolves before Bruce advances his attack timer.
       Include the tick that would start moving the charge. At slam timer
       TOUCHDOWN-1, a connecting bat still wins over the pending impact. */
    if (bat && ((bruce->state == MF_BRUCE_CHARGE && bruce->timer >= CHARGE_WINDUP - 1 &&
                 bruce->timer < CHARGE_WINDUP + CHARGE_ACTIVE) ||
                (bruce->state == MF_BRUCE_SLAM && bruce->timer >= SLAM_WINDUP &&
                 bruce->timer < SLAM_TOUCHDOWN))) {
        int height = bruce->height;
        bruce->impact = 0;
        bruce->fall_direction = direction;
        enter(bruce, height || bruce->health ? MF_BRUCE_HURT : MF_BRUCE_FALL);
        bruce->height = height;
    } else if (!bruce->health || (bat && !armored)) {
        bruce->fall_direction = direction;
        enter(bruce, MF_BRUCE_FALL);
    }
    else if (!armored) enter(bruce, MF_BRUCE_HURT);
}

int mf_bruce_strike(const mf_bruce *bruce, const mf_player *player)
{
    int dx = (player->x - bruce->x) / Q;
    int dy = (player->y - bruce->y) / Q;
    int height = player->height / Q, t = bruce->timer;
    if (!living(player) || player->invulnerable) return 0;
    switch (bruce->state) {
    case MF_BRUCE_PUNCH:
        return t >= PUNCH_WINDUP && t < PUNCH_WINDUP + PUNCH_ACTIVE &&
               dx * bruce->facing >= 0 && dx * bruce->facing <= 76 && dy >= -12 && dy <= 12 &&
               height < 52 ? PUNCH_DAMAGE : 0;
    case MF_BRUCE_CHARGE:
        return t >= CHARGE_WINDUP && t < CHARGE_WINDUP + CHARGE_ACTIVE &&
               dx * bruce->facing >= -16 && dx * bruce->facing <= 52 && dy >= -12 && dy <= 12 &&
               height < 44 ? CHARGE_DAMAGE : 0;
    case MF_BRUCE_SLAM:
        return t == SLAM_TOUCHDOWN && dx * dx + 4 * dy * dy <= 52 * 52 &&
               height < 18 ? SLAM_DAMAGE : 0;
    default:
        return 0;
    }
}

static int nearest_player(const mf_bruce *bruce, const mf_game *game)
{
    int i, nearest = -1, best = 0;
    for (i = 0; i < MF_PLAYERS; ++i) {
        const mf_player *player = &game->players[i];
        int dx, dy, distance;
        if (!living(player)) continue;
        dx = (player->x - bruce->x) / Q;
        dy = (player->y - bruce->y) / Q;
        distance = dx * dx + dy * dy;
        if (nearest < 0 || distance < best) {
            nearest = i;
            best = distance;
        }
    }
    return nearest;
}

static int clamp_to_floor(int value, int low, int high)
{
    return value < low ? low : value > high ? high : value;
}

static int commit_slam(mf_bruce *bruce, const mf_game *game)
{
    int index = nearest_player(bruce, game), x, y, dx, dy;
    if (index < 0) return 0;
    x = clamp_to_floor(game->players[index].x, LOT_FIRST * Q, BRUCE_RIGHT * Q);
    y = clamp_to_floor(game->players[index].y, LANE_BACK * Q, LANE_FRONT * Q);
    dx = (x - bruce->x) / Q;
    dy = (y - bruce->y) / Q;
    if ((dx > -72 && dx < 72) || dx < -140 || dx > 140 || dy < -42 || dy > 42)
        return 0;
    bruce->target = index;
    bruce->retarget = 24;
    bruce->start_x = bruce->x;
    bruce->land_x = x;
    bruce->slam_start_y = bruce->y;
    bruce->slam_land_y = y;
    bruce->facing = dx > 0 ? 1 : -1;
    return 1;
}

static int choose_attack(mf_bruce *bruce, const mf_player *player, const mf_game *game)
{
    int i, dx = (player->x - bruce->x) / Q, dy = (player->y - bruce->y) / Q;
    int near = dx >= -76 && dx <= 76 && dy >= -12 && dy <= 12;
    int aligned = dx >= -152 && dx <= 152 && dy >= -12 && dy <= 12;
    for (i = 0; i < 3; ++i) {
        int pick = (bruce->attack_cycle + i) % 3;
        if ((pick == 0 && near) || (pick == 1 && aligned) || (pick == 2 && commit_slam(bruce, game))) {
            enter(bruce, MF_BRUCE_PUNCH + pick);
            bruce->attack_cycle = (pick + 1) % 3;
            return 1;
        }
    }
    return 0;
}

void mf_bruce_step(mf_bruce *bruce, const mf_game *game)
{
    int x, y, moving;
    const mf_player *target;
    if (!bruce->ready) return;
    if (!bruce->active) {
        entrance(bruce, game);
        return;
    }
    if (bruce->invulnerable) --bruce->invulnerable;
    if (bruce->impact) --bruce->impact;
    if (action_tick(bruce)) return;
    if (bruce->cooldown) --bruce->cooldown;
    if (bruce->target < 0 || !living(&game->players[bruce->target]) || --bruce->retarget <= 0) {
        bruce->target = nearest_player(bruce, game);
        bruce->retarget = 24;
    }
    x = bruce->x;
    y = bruce->y;
    if (bruce->target >= 0) {
        target = &game->players[bruce->target];
        if (target->x != x) bruce->facing = target->x > x ? 1 : -1;
        if (!bruce->cooldown && choose_attack(bruce, target, game)) return;
        x = advance(x, target->x, 42 * Q, 144);
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
    switch (bruce->state) {
    case MF_BRUCE_ENTRANCE: return bruce->timer < 12 ? POSE_SLAM : POSE_CHARGE + 1;
    case MF_BRUCE_ENTRANCE_IMPACT: return POSE_SLAM + 1;
    case MF_BRUCE_RECOVERY: return POSE_CHARGE;
    case MF_BRUCE_PUNCH:
        return POSE_PUNCH + (bruce->timer >= 14) + (bruce->timer >= PUNCH_WINDUP) -
               (bruce->timer >= PUNCH_WINDUP + PUNCH_ACTIVE);
    case MF_BRUCE_CHARGE:
        if (bruce->timer >= CHARGE_WINDUP + CHARGE_ACTIVE) return POSE_CHARGE;
        return POSE_CHARGE + (bruce->timer >= 15) + (bruce->timer >= CHARGE_WINDUP);
    case MF_BRUCE_SLAM:
        if (bruce->timer < SLAM_WINDUP) return POSE_SLAM;
        if (bruce->timer < SLAM_TOUCHDOWN) return POSE_CHARGE + 1;
        if (bruce->timer < SLAM_TOUCHDOWN + SLAM_IMPACT) return POSE_SLAM + 1;
        return POSE_CHARGE;
    case MF_BRUCE_HURT:
        return bruce->timer < 6 ? POSE_HIT : bruce->timer < 15 ? POSE_HIT + 1 : POSE_CHARGE;
    case MF_BRUCE_FALL: return POSE_KD + (bruce->timer >= 6);
    case MF_BRUCE_DOWN:
    case MF_BRUCE_DEFEATED: return POSE_KD + 2;
    case MF_BRUCE_RISE: return bruce->timer < 13 ? POSE_KNEEL : POSE_CHARGE;
    default: break;
    }
    if (!bruce->moving) return bruce->animation / 22;
    return 2 + (bruce->animation >= 12) + (bruce->animation >= 22);
}

#ifdef MF_BRUCE_SATURN
typedef struct {
    const char *name;
    short width, height, anchor_x, anchor_y, shared_boot;
} bruce_frame;
#include "bruce_bank_data.h"

static jo_palette *colors;
static unsigned short saved_colors[255];
static int ids[BRUCE_DEFS], boot_view, resident, palette_owned;

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
    boot_view = -1;
    for (i = 0; i < BRUCE_DEFS; ++i) ids[i] = -1;
}

static void bind_boot_view(void)
{
    int base = ids[0];
    __jo_sprite_def[boot_view] = __jo_sprite_def[base];
    __jo_sprite_def[boot_view].adr += BRUCE_BOOT_OFFSET / 8;
    __jo_sprite_def[boot_view].height = BRUCE_BOOT_HEIGHT;
    __jo_sprite_def[boot_view].size = (BRUCE_BOOT_WIDTH / 8 << 8) | BRUCE_BOOT_HEIGHT;
    __jo_sprite_pic[boot_view] = __jo_sprite_pic[base];
    __jo_sprite_pic[boot_view].index = boot_view;
    __jo_sprite_pic[boot_view].data = (char *)__jo_sprite_pic[base].data + BRUCE_BOOT_OFFSET;
}

static int install(jo_palette *shared)
{
    int i;
    if (shared || !colors || colors->id != 2 || !colors->data || palette_owned ||
        MF_ENEMY_PREFIX_BYTES + BRUCE_BYTES + 49152u > 458488u) return 0;
    jo_set_tga_default_palette(JO_NULL);
    for (i = 0; i < BRUCE_DEFS; ++i) {
        if (i == BRUCE_DEFS - 1) {
            jo_img_8bits empty = {.width=8,.height=0,.data=JO_NULL};
            boot_view = jo_sprite_add_8bits_image(&empty);
            if (boot_view < 0) return 0;
        }
        ids[i] = jo_sprite_add_tga("BRUCE", bruce_frames[i].name, 1);
        if (ids[i] < 0) return 0;
    }
    /* Jo appends after the previous definition. Keep the placeholder at the
       allocation cursor until the final real texture has been registered. */
    bind_boot_view();
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
    if (!resident || !palette_owned || boot_view != first + BRUCE_DEFS - 1 ||
        jo_sprite_get_height(boot_view) != BRUCE_BOOT_HEIGHT ||
        jo_sprite_get_width(boot_view) != BRUCE_BOOT_WIDTH ||
        (char *)jo_sprite_get_raw_data(boot_view) != (char *)jo_sprite_get_raw_data(ids[0]) + BRUCE_BOOT_OFFSET)
        return 0;
    for (i = 0; i < 255; ++i)
        if (colors->data[i] != bruce_colors[i]) return 0;
    for (i = 0; i < BRUCE_DEFS; ++i) {
        int id = ids[i];
        const bruce_frame *frame = &bruce_frames[i];
        if (id != first + i + (i == BRUCE_DEFS - 1) || jo_sprite_get_width(id) != frame->width ||
            jo_sprite_get_height(id) != frame->height || __jo_sprite_pic[id].color_mode != COL_256 ||
            (unsigned long)jo_sprite_get_raw_data(id) - JO_VDP1_VRAM != end) return 0;
        end += (frame->width * frame->height + 31u) & ~31u;
    }
    return end == 0x10000u + MF_ENEMY_PREFIX_BYTES + BRUCE_BYTES &&
           end + 49152u <= 0x10000u + 458488u;
}

const mf_enemy_bank_spec mf_bruce_bank_spec = {
    3, BRUCE_DEFS + 1, BRUCE_BYTES, install, invalidate, validate
};

/* Scale the texture rectangle about the same ground pivot for every pose.
   The endpoints stay in fixed point until SGL builds the VDP1 command. */
static void draw_sprite(int id, const bruce_frame *frame, int facing, int x, int ground, int depth)
{
    enum { SCALE = (90 * 65536 + 50) / 100 };
    int anchor_x = facing > 0 ? frame->anchor_x : frame->width - frame->anchor_x;
    jo_fixed left = jo_int2fixed(x - JO_TV_WIDTH_2) - anchor_x * SCALE;
    jo_fixed top = jo_int2fixed(ground - JO_TV_HEIGHT_2) - frame->anchor_y * SCALE;
    jo_fixed right = left + frame->width * SCALE;
    jo_fixed bottom = top + frame->height * SCALE;
    const jo_pos2D_fixed corners[4] = {
        {left, top}, {right, top}, {right, bottom}, {left, bottom}
    };

    jo_sprite_set_palette(colors->id);
    if (facing < 0) jo_sprite_enable_horizontal_flip();
    jo_sprite_draw_4p_fixed(id, corners, jo_int2fixed(depth), true);
    jo_sprite_disable_horizontal_flip();
}

void mf_bruce_draw(const mf_bruce *bruce, int x, int ground, int depth)
{
    static const bruce_frame boots = {
        0, BRUCE_BOOT_WIDTH, BRUCE_BOOT_HEIGHT, BRUCE_BOOT_X, BRUCE_BOOT_Y, 0
    };
    int pose;
    if (!resident || !bruce->active) return;
    pose = mf_bruce_pose(bruce);
    draw_sprite(ids[pose], &bruce_frames[pose], bruce->facing, x, ground - bruce->height, depth);
    if (bruce_frames[pose].shared_boot)
        draw_sprite(boot_view, &boots, bruce->facing, x, ground - bruce->height, depth);
}
#endif
#endif
