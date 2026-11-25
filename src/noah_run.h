#ifndef MF_NOAH_RUN_H
#define MF_NOAH_RUN_H

#if MF_NOAH_RUN
#include <string.h>
#include "noah_run_data.h"

/* One cache per actor, populated before gameplay. Each VDP1 pair holds the
   current pose and a spare upload target. The IDs and dimensions never move. */
static unsigned int noah_buck[4][MF_NOAH_BUCK_BYTES / 4];
static unsigned int noah_chuck[4][MF_NOAH_CHUCK_BYTES / 4];
static int noah_ids[2][2][MF_NOAH_PARTS];
static unsigned char noah_front[2], noah_cached[2][2];

static unsigned char *noah_source(int actor, int frame)
{
    return (unsigned char *)(actor ? noah_chuck[frame] : noah_buck[frame]);
}

static unsigned noah_band_bytes(int actor, int part)
{
    return (noah_bands[actor][part].width * noah_bands[actor][part].height * 2u + 31u) & ~31u;
}

static int noah_load(int *last)
{
    for (int actor = 0; actor < 2; ++actor) {
        unsigned expected = actor ? MF_NOAH_CHUCK_BYTES : MF_NOAH_BUCK_BYTES;
        for (int frame = 0; frame < 4; ++frame) {
            int size = 0;
            char *file = jo_fs_read_file_in_dir(noah_frames[actor][frame].name, "COMBAT", &size);
            if (!file) return 0;
            if ((unsigned)size == expected) memcpy(noah_source(actor, frame), file, expected);
            jo_free(file);
            if ((unsigned)size != expected) return 0;
        }
        for (int slot = 0; slot < 2; ++slot) {
            unsigned char *pixels = noah_source(actor, slot);
            for (int part = 0; part < MF_NOAH_PARTS; ++part) {
                jo_img image;
                image.width = noah_bands[actor][part].width;
                image.height = noah_bands[actor][part].height;
                image.data = (jo_color *)pixels;
                int id = jo_sprite_add(&image);
                if (id < 0) return 0;
                noah_ids[actor][slot][part] = *last = id;
                pixels += noah_band_bytes(actor, part);
            }
            noah_cached[actor][slot] = slot;
        }
    }
    slDMAWait();
    return 1;
}

static void noah_draw(int actor, int frame, int center, int ground, int direction, int depth)
{
    int slot = noah_front[actor];
    if (noah_cached[actor][slot] != frame) {
        int spare = 1 - slot;
        if (noah_cached[actor][spare] == frame) {
            slot = spare;
        } else {
            /* VDP1 may still read the previous list. Suspend automatic
               restarts and write only after the completed-draw fence. */
            JO_VDP1_PTMR = 0;
            if (JO_VDP1_EDSR & 2u) {
                unsigned char *pixels = noah_source(actor, frame);
                for (int part = 0; part < MF_NOAH_PARTS; ++part) {
                    int id = noah_ids[actor][spare][part];
                    unsigned bytes = noah_band_bytes(actor, part);
                    slDMACopy(pixels, jo_sprite_get_raw_data(id), bytes);
                    pixels += bytes;
                }
                slDMAWait();
                noah_cached[actor][spare] = frame;
                slot = spare;
            }
            JO_VDP1_PTMR = 2;
        }
    }
    noah_front[actor] = slot;
    frame = noah_cached[actor][slot];
    jo_sprite_restore_sprite_scale();
    jo_sprite_disable_horizontal_flip();
    if (direction < 0) jo_sprite_enable_horizontal_flip();
    for (int part = 0; part < MF_NOAH_PARTS; ++part) {
        int left = noah_frames[actor][frame].x[part] - MF_NOAH_ROOT_X;
        int x = direction > 0 ? center + left : center - left - noah_bands[actor][part].width;
        /* SGL centers RGB sprites on a half-pixel for even dimensions.
           Compensate at submission so adjacent bands share an exact seam. */
        int y = ground + noah_bands[actor][part].y - MF_NOAH_ROOT_Y;
        if (!(noah_bands[actor][part].height & 1)) --y;
        jo_sprite_draw3D2(noah_ids[actor][slot][part], x - 1, y, depth);
    }
    jo_sprite_disable_horizontal_flip();
}
#endif
#endif
