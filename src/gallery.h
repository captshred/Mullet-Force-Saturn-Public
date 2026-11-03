#ifndef MF_GALLERY_H
#define MF_GALLERY_H
/* Optional renderer only. No game state or normal artwork is substituted. */
int mf_gallery_load(int last_rgb_sprite);
int mf_gallery_active(void);
int mf_gallery_update(unsigned pressed);
void mf_gallery_draw(const int street[5],int street_palette_id);
#endif
