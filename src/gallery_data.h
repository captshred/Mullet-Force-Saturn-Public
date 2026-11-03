/* Exact 88px study pieces: offsets in the original cropped raster. */
#ifndef MF_GALLERY_DATA_H
#define MF_GALLERY_DATA_H
#define MF_GALLERY_BYTES 10784u
typedef struct { const char *name; short x,y,width,height; } mf_gallery_piece;
static const short gallery_width[2]={79,82};
static const mf_gallery_piece gallery_parts[2][3]={
{{"GB0.TGA",21,0,40,20},{"GB1.TGA",9,20,64,56},{"GB2.TGA",0,76,80,12}},
{{"GC0.TGA",18,0,40,20},{"GC1.TGA",8,20,64,56},{"GC2.TGA",0,76,88,12}}
};
#endif
