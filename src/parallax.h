#ifndef MF_PARALLAX_H
#define MF_PARALLAX_H
/* Optional gallery-only demonstration. No simulation or CD access while moving. */
void mf_parallax_game_draw(int camera);
int mf_parallax_load(void);
int mf_parallax_enter(void);
void mf_parallax_leave(void);
int mf_parallax_active(void);
void mf_parallax_update(unsigned held,unsigned ticks);
void mf_parallax_draw(void);
void mf_parallax_labels(void);
int mf_parallax_error(void);
#endif
