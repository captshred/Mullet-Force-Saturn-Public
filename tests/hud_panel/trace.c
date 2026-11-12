/* Reuse the immutable allocation/pixel/draw mock; additionally retain text. */
#define jo_print hud_ignored_print
#define jo_printf hud_ignored_printf
#define jo_clear_screen_line hud_ignored_clear
#include "../sprite_cleanup/trace.c"
#undef jo_print
#undef jo_printf
#undef jo_clear_screen_line
#include <stdarg.h>
void jo_clear_screen_line(int y){printf("CLEAR|%u|%d\n",cleanup_case,y);}
void jo_print(int x,int y,const char *s){printf("TEXT|%u|%d|%d|%s\n",cleanup_case,x,y,s);}
void jo_printf(int x,int y,const char *fmt,...){char b[256];va_list ap;va_start(ap,fmt);vsnprintf(b,sizeof b,fmt,ap);va_end(ap);jo_print(x,y,b);}
void jo_sprite_draw_4p_fixed(int id,const jo_pos2D_fixed *p,int z,bool centered)
{
    int i;assert(centered && id>=0 && id<count);
    printf("QUAD|%u|%d|%d|%d|%d",cleanup_case,id,z,flip,selected_palette);
    for(i=0;i<4;i++)printf("|%d|%d",p[i].x,p[i].y);
    putchar('\n');
}
