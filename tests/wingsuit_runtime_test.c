#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <jo/jo.h>
#include "wingsuit_runtime.h"
/* Exercise the real render routine without exposing test hooks in production. */
#include "wingsuit_audio_data.h"
#include "../src/wingsuit_runtime.c"
unsigned short ws_vdp1[262144],ws_a0[65536],ws_b0[65536],ws_scsp[262144];
unsigned short ws_ptmr=0,ws_edsr=2;
static unsigned short cram[2048];
static int last=254,reads,frees,resets,off,draws,fail,slots,fail_texture=-1;
static unsigned now;
static int vdp2_scheduled,state_step,spr_priority[8],rgb_mode,spr_window,pixel_window;
static int screen_dist=160,depth_level=1,far_z=32767,window_fail;
static unsigned rendered_types;
static void next_state(int step){assert(vdp2_scheduled && ws_ptmr==0 && step==state_step+1);state_step=step;}
void slSetSprTVMode(unsigned short mode){assert(mode==TV_320x240);state_step=0;next_state(1);}
void slCurWindow(unsigned char window){assert(window==winFar);next_state(2);}
void slFrameClipSize(short w,short h){assert(w==320 && h==240);next_state(3);}
int slWindow(short l,short t,short r,short b,short z,short x,short y){
    assert(l==0 && t==0 && r==319 && b==239 && z==1024 && x==160 && y==120);
    next_state(4);far_z=z;return !window_fail;
}
void slSetScreenDist(int dist){assert(dist==160*65536);next_state(5);screen_dist=dist/65536;}
void slZdspLevel(unsigned short level){assert(level==1);next_state(6);depth_level=level;}
void slSpriteColMode(unsigned short mode){assert(mode==SPR_PAL_RGB);next_state(7);rgb_mode=mode;}
void slSpriteWinMode(unsigned short mode){assert(mode==OFF);next_state(8);pixel_window=mode;}
void slScrWindowModeSPR(unsigned short mode){assert(mode==0);next_state(9);spr_window=mode;}
void test_sprite_priority(int slot,int priority){
    assert(slot>=0 && slot<8 && priority==4);next_state(10+slot);spr_priority[slot]=priority;
}
static int in_stage,cds,missing_dir,register_fail;
static const char *missing_asset,*short_asset;
static char diagnostic[1024];
static char screen[30][40];
int GFS_NameToId(Sint8 *raw)
{
    const char *name=(const char *)raw;
    /* Real profile has 264 root entries: every W asset sorts outside the
       pinned 256-entry table. The early directory remains reachable. */
    if(!in_stage)return !missing_dir && !strcmp(name,"ALEVEL2")?5:-1;
    if(missing_asset && !strcmp(name,missing_asset))return -1;
    return 3;
}
void jo_fs_cd(const char *name)
{
    ++cds;
    if(!strcmp(name,"ALEVEL2")){assert(!in_stage);in_stage=1;}
    else {assert(!strcmp(name,JO_PARENT_DIR));assert(in_stage);in_stage=0;}
}
char *jo_fs_read_file(const char *name,int *size)
{
    char path[128];FILE *f;void *data;
    assert(in_stage);++reads;if(fail)return NULL;
    if(fail_texture>=0 && strstr(name,"WDRONE"))return NULL;
    snprintf(path,sizeof(path),"assets/wingsuit/%s",name);f=fopen(path,"rb");assert(f);
    fseek(f,0,SEEK_END);*size=(int)ftell(f);rewind(f);data=malloc(*size);assert(data);
    assert(fread(data,1,*size,f)==(size_t)*size);fclose(f);if(short_asset && !strcmp(name,short_asset))--*size;return data;
}
static mf_ws_audio_diagnostic audio_diagnostic;
static int fail_audio_init;
const mf_ws_audio_diagnostic *mf_ws_audio_diagnostics(void){return &audio_diagnostic;}
int mf_ws_audio_load(mf_ws_audio_reader read,mf_ws_audio_progress progress){
    const char *n[]={"WDEATH.MAP","WDEATH.SEQ","WDEATH.TON"};int i;static const int size[]={MF_WS_MAP_BYTES,MF_WS_SEQ_BYTES,MF_WS_TON_BYTES};
    for(i=0;i<3;i++){char *p=read(n[i],size[i]);if(!p)return 0;jo_free(p);}
    if(fail_audio_init){audio_diagnostic=(mf_ws_audio_diagnostic){MF_WS_AUDIO_MAP_CHANGE,7,"MAP CHANGE",1,0,1};progress(&audio_diagnostic);return 0;}
    return 1;
}
static int audio_events,audio_pumps;
void mf_ws_audio_events(int n,unsigned shots){(void)shots;audio_events+=n;}
void mf_ws_audio_step(unsigned n,unsigned focus){(void)n;(void)focus;audio_pumps++;}
unsigned mf_ws_audio_fault(void){return 0;}
void jo_free(void *p){++frees;free(p);}
void jo_dma_copy(const void *a,void *b,unsigned n){memcpy(b,a,n);}
int jo_sprite_add(const jo_img *im){if(register_fail)return -1;assert(last<17);slots+=im->width*im->height*2;return ++last;}
void jo_sprite_free_all(void){++resets;last=-1;slots=0;}
int jo_get_last_sprite_id(void){return last;}
void slSoundOffWait(void){++off;}
void slScrDisp(unsigned a){assert(a==(NBG1OFF|NBG2OFF));}
void slCharNbg1(int a,int b){assert(a==COL_TYPE_256 && b==CHAR_SIZE_1x1);}
void slPageNbg1(void *a,void *b,int c){assert(a==ws_a0 && !b && c==(PNB_1WORD|CN_12BIT));}
void slPlaneNbg1(int a){assert(a==PL_SIZE_1x1);}
void slMapNbg1(void *a,void *b,void *c,void *d){assert(a==ws_b0 && a==b && b==c && c==d);}
void slZoomNbg1(int a,int b){assert(a==65536 && b==65536);}
void slScrPosNbg1(int a,int b){assert(a==0 && b<=0 && b>=-511*65536);}
void slScrWindow0(unsigned short a,unsigned short b,unsigned short c,unsigned short d){assert(a==48 && !b && c==271 && d==239);}
void slScrWindowModeNbg1(unsigned short a){assert(a==win0_IN);}
void slPriorityNbg1(int a){assert(a==1);next_state(18);}
void slPriorityNbg0(int a){assert(a==7);next_state(19);}
int slScrAutoDisp(unsigned a){
    int i;assert(a==(NBG0ON|NBG1ON|SPRON));vdp2_scheduled=1;
    /* Poison inherited state so successful draws require explicit setup. */
    for(i=0;i<8;i++)spr_priority[i]=0;
    rgb_mode=0;spr_window=7;pixel_window=1;screen_dist=400;depth_level=1;return 0;
}
static int beam_draws;
static int beam_y[2][MF_WS_BEAM_MAX_SEGMENTS],beam_h[2][MF_WS_BEAM_MAX_SEGMENTS],beam_n[2];
static void check_beam_coverage(int actor)
{
    int row,k,bottom=shooter.players[actor].y/256-MF_WS_BEAM_EMITTER;
    assert(beam_n[actor]>=1 && beam_n[actor]<=7);
    assert(beam_h[actor][0]==16 && beam_y[actor][0]+16==bottom && beam_y[actor][beam_n[actor]-1]<=0);
    for(k=1;k<beam_n[actor];k++)assert(beam_y[actor][k]+32==beam_y[actor][k-1]);
    for(row=0;row<bottom;row++){
        int covered=0;for(k=0;k<beam_n[actor];k++)covered+=row>=beam_y[actor][k] && row<beam_y[actor][k]+beam_h[actor][k];
        assert(covered==1); /* No gaps and no overlapping alpha seams. */
    }
}
void jo_sprite_disable_horizontal_flip(void){beam_draws=beam_n[0]=beam_n[1]=0;}
void jo_sprite_disable_vertical_flip(void){}
void jo_sprite_disable_half_transparency(void){}
void jo_sprite_disable_dark_filter(void){}
void jo_sprite_disable_gouraud_shading(void){}
void jo_sprite_restore_sprite_scale(void){}
void jo_sprite_disable_clipping(void){}
void jo_sprite_draw3D2(int id,int x,int y,int z){
    int i;
    if(id>=10){
        int actor=-1,j;
        for(j=0;j<2;j++)if(mf_ws_beam_active(&shooter,j) && id==(id<14?10:14)+(int)((shooter.ticks/3+j)&3))actor=j;
        assert(actor>=0 && x==shooter.players[actor].x/256-16 && beam_n[actor]<7);
        beam_h[actor][beam_n[actor]]=id<14?32:16;beam_y[actor][beam_n[actor]++]=y;++beam_draws;
    }
    assert(id>=0 && id<=last && z==100 && state_step==19 && ws_ptmr==2);
    assert(z>(screen_dist>>depth_level) && z<=far_z);
    assert(rgb_mode==SPR_PAL_RGB && !spr_window && !pixel_window);
    for(i=0;i<8;i++)assert(spr_priority[i]==4);
    rendered_types|=1u<<id;++draws;
}
void jo_clear_screen(void){diagnostic[0]=0;memset(screen,' ',sizeof(screen));}
void jo_print(int x,int y,const char *s){
    assert(x>=0 && x<40 && y>=0 && y<30);
    while(*s && x<40)screen[y][x++]=*s++;
}
void jo_printf(int x,int y,const char *s,...){
    assert(x>=0 && x<40 && y>=0 && y<30);
    {char text[128];va_list ap;va_start(ap,s);vsnprintf(text,sizeof(text),s,ap);va_end(ap);jo_print(x,y,text);}
    if(x==3){size_t n=strlen(diagnostic);va_list ap;va_start(ap,s);vsnprintf(diagnostic+n,sizeof(diagnostic)-n,s,ap);va_end(ap);}
}
static void frame(mf_input in[2],unsigned p[2]){mf_ws_runtime_frame(in,p,++now);}
int main(void)
{
    mf_input in[2]={{0}};unsigned p[2]={MF_START,MF_START};jo_palette palette={1,cram+256};int i,r;
    memset(ws_vdp1,0x55,sizeof(ws_vdp1));memset(ws_a0,0x55,sizeof(ws_a0));memset(ws_b0,0x55,sizeof(ws_b0));memset(ws_scsp,0x55,sizeof(ws_scsp));memset(cram,0x55,sizeof(cram));
    in[0].connected=in[1].connected=1;in[0].held=in[1].held=MF_A;
    assert(GFS_NameToId((Sint8 *)"WCELL.BIN")==-1);
    mf_ws_runtime_begin(1,&palette,now);
    /* Repeated callbacks without a new VBlank cannot release resources. */
    for(i=0;i<10;i++)mf_ws_runtime_frame(in,p,now);
    assert(!resets && !reads);frame(in,p);frame(in,p);assert(!resets);
    frame(in,p);assert(resets==1 && off==1 && last==17 && slots==28032);
    assert(ws_ptmr==2 && cds==2 && !in_stage);
    assert(reads==24 && frees==24 && !draws && !p[0] && !p[1]);
    assert(ws_vdp1[0]==0x5555 && ws_vdp1[0x10000/2]==0 && ws_vdp1[0x7fef8/2]==0x5555);
    assert(ws_a0[106496/2]==0x5555 && ws_b0[65536/2]==0x5555);
    assert(cram[0]==0x5555 && cram[255]==0x5555 && cram[2047]==0);
    for(i=0;i<262144;i++)assert(!ws_scsp[i]);
    for(i=0;i<120;i++)frame(in,p);
    assert(!draws);
    r=reads;for(i=0;i<1000;i++)frame(in,p);
    assert(draws && reads==r && resets==1); /* no per-frame I/O/texture registrations */
    /* Independently of gameplay stepping, each of the six real object paths
       must submit through the initialized renderer with unchanged sort Z. */
    mf_ws_init(&shooter,1);
    shooter.players[0].invulnerable=shooter.players[1].invulnerable=0;
    shooter.enemies[0]=(mf_ws_enemy){1,100*256,60*256,0,0};
    shooter.enemies[1]=(mf_ws_enemy){0,150*256,60*256,0,12};
    shooter.shots[0]=(mf_ws_shot){1,100*256,80*256,0,60,0};
    shooter.hostile[0]=(mf_ws_hostile_shot){1,150*256,80*256,0,60,0,768};
    rendered_types=0;render();assert(rendered_types==63u);
    /* The real HUD must erase the complete 19-character restart prompt. */
    shooter.game_over=1;render();assert(screen[16][28]=='T');
    p[0]=MF_START;mf_ws_step(&shooter,(unsigned[2]){0,0},p,3);p[0]=0;
    assert(!shooter.game_over);render();
    for(i=10;i<=28;i++)assert(screen[16][i]==' ');
    shooter.paused=1;render();
    for(i=10;i<=28;i++)assert(screen[16][i]==' ');
    assert(!memcmp(&screen[14][12],"PAUSED",6) && !memcmp(&screen[2][0],"BUCK",4));
    shooter.paused=0;
    /* Runtime selection is per player, uses actual motion, and stays visual. */
    mf_ws_init(&shooter,1);shooter.spawn=10000;phase=3;
    in[0].held=MF_LEFT;in[1].held=MF_RIGHT;frame(in,p);
    assert(player_bank[0]==WS_LEFT && player_bank[1]==WS_RIGHT);
    rendered_types=0;render();assert((rendered_types&((1u<<6)|(1u<<9)))==((1u<<6)|(1u<<9)));
    in[0].held=MF_RIGHT;in[1].held=MF_LEFT;frame(in,p);
    assert(player_bank[0]==WS_RIGHT && player_bank[1]==WS_LEFT);
    rendered_types=0;render();assert((rendered_types&((1u<<7)|(1u<<8)))==((1u<<7)|(1u<<8)));
    in[0].held=MF_UP;in[1].held=MF_LEFT|MF_RIGHT;frame(in,p);
    assert(player_bank[0]==WS_CENTER && player_bank[1]==WS_CENTER);
    shooter.players[0].x=64*256;in[0].held=MF_LEFT;frame(in,p);assert(player_bank[0]==WS_CENTER);
    in[0].held=MF_RIGHT|MF_UP|MF_A;frame(in,p);assert(player_bank[0]==WS_RIGHT);
    in[0].connected=0;frame(in,p);assert(player_bank[0]==WS_CENTER);in[0].connected=1;
    shooter.paused=1;frame(in,p);assert(player_bank[0]==WS_CENTER);shooter.paused=0;
    puts("PASS player pass 2: actual per-player movement selects all six poses; vertical/opposed/bounds/disconnect/pause center; complete restart field clears stray T while preserving HUD");
    puts("PASS VDP1 state: stopped PTMR restarts in auto mode; SGL state restored after VDP2 scheduling; all six render paths accepted independently of gameplay");
    mf_ws_init(&shooter,1);shooter.spawn=10000;
    shooter.players[0].shot_hold=shooter.players[1].shot_hold=MF_WS_FOCUS_TICKS-1;
    shooter.enemies[0]=(mf_ws_enemy){1,130*256,100*256,0,0};
    in[0].held=MF_A|MF_RIGHT;in[1].held=MF_A|MF_LEFT;phase=3;
    audio_events=audio_pumps=0;rendered_types=0;frame(in,p);
    check_beam_coverage(0);check_beam_coverage(1);
    assert(beam_draws==14 && audio_events==1 && audio_pumps==1);
    assert((rendered_types&((1u<<10)|(1u<<11)))!=0);
    render();render();assert(audio_events==1 && audio_pumps==1);
    in[0].held=in[1].held=0;frame(in,p);assert(!beam_draws && audio_events==1);
    {
        static const int ys[]={16,32,47,64,128,200,223};int n,f;
        for(n=0;n<7;n++)for(f=0;f<12;f++){
            mf_ws_init(&shooter,1);shooter.players[0].y=shooter.players[1].y=ys[n]*256;
            shooter.players[0].shot_hold=shooter.players[1].shot_hold=20;shooter.ticks=f;
            render();check_beam_coverage(0);check_beam_coverage(1);
            assert(beam_draws==2*(1+(ys[n]>31?(ys[n]-31+31)/32:0)));
        }
        /* Both beams plus every original pool at its simultaneous limit. */
        mf_ws_init(&shooter,1);shooter.players[0].y=shooter.players[1].y=223*256;
        shooter.players[0].invulnerable=shooter.players[1].invulnerable=0;
        shooter.players[0].shot_hold=shooter.players[1].shot_hold=20;
        for(n=0;n<MF_WS_ENEMIES;n++)shooter.enemies[n]=(mf_ws_enemy){1,100*256,60*256,0,0};
        for(n=0;n<MF_WS_SHOTS;n++)shooter.shots[n]=(mf_ws_shot){1,100*256,80*256,0,60,0};
        for(n=0;n<MF_WS_HOSTILE;n++)shooter.hostile[n]=(mf_ws_hostile_shot){1,150*256,80*256,0,60,0,768};
        r=draws;render();assert(beam_draws==14 && draws-r==72);
    }
    puts("PASS full-height renderer: seven player heights and all animation phases, contiguous row coverage, clean offscreen top, attached emitters; simultaneous two-player/all-pools maximum 72 commands");
    puts("PASS render integration: two attached animated beam draws through restored SGL; release removes draws; simulation deaths queued once, rendering never re-triggers audio");
    fail_audio_init=1;mf_ws_runtime_begin(0,&palette,now);frame(in,p);frame(in,p);frame(in,p);frame(in,p);
    assert(error==108 && strstr(diagnostic,"WDEATH BANK") && strstr(diagnostic,"MAP CHANGE") && strstr(diagnostic,"EXPECT 0 GOT 1"));
    fail_audio_init=0;
    window_fail=1;mf_ws_runtime_begin(0,&palette,now);frame(in,p);frame(in,p);frame(in,p);frame(in,p);
    assert(ws_ptmr==0 && strstr(diagnostic,"WINDOW") && error==107);window_fail=0;
    fail_texture=0;mf_ws_runtime_begin(0,&palette,now);frame(in,p);frame(in,p);frame(in,p);
    assert(last==-1 && resets==5);r=reads;i=draws;frame(in,p);assert(reads==r && draws==i);
    fail_texture=-1;fail=1;mf_ws_runtime_begin(0,&palette,now);frame(in,p);frame(in,p);frame(in,p);
    assert(last==-1);r=reads;frame(in,p);assert(reads==r);
    fail=0;ws_edsr=0;ws_ptmr=2;r=reads;i=resets;
    mf_ws_runtime_begin(0,&palette,now);frame(in,p);frame(in,p);frame(in,p);
    assert(ws_ptmr==0 && reads==r && resets==i);
    ws_edsr=2;fail=0;
    {
        const char *assets[]={"WCELL.BIN","WMAP.BIN","WPAL.BIN","WBUCK.BIN","WCHUCK.BIN","WDRONE.BIN","WSHOT.BIN","WHOST.BIN","WBOOM.BIN","WBUCKL.BIN","WBUCKR.BIN","WCHUCKL.BIN","WCHUCKR.BIN","WFL0.BIN","WFL1.BIN","WFL2.BIN","WFL3.BIN","WFO0.BIN","WFO1.BIN","WFO2.BIN","WFO3.BIN","WDEATH.MAP","WDEATH.SEQ","WDEATH.TON"};
        const int sizes[]={2752,8192,32,2048,2048,1152,128,128,2048,2048,2048,2048,2048,2048,2048,2048,2048,1024,1024,1024,1024,MF_WS_MAP_BYTES,MF_WS_SEQ_BYTES,MF_WS_TON_BYTES};
        char expected[64];int mode,a;
        for(mode=0;mode<2;mode++)for(a=0;a<24;a++){
            missing_asset=mode==0?assets[a]:NULL;short_asset=mode==1?assets[a]:NULL;
            cds=0;mf_ws_runtime_begin(0,&palette,now);frame(in,p);frame(in,p);frame(in,p);frame(in,p);
            assert(!in_stage && cds==2 && (a>=21 || last==-1));
            assert(strstr(diagnostic,assets[a]) && strstr(diagnostic,mode==0?"MISSING":"LENGTH"));
            snprintf(expected,sizeof(expected),"EXPECT %d GOT %d",sizes[a],mode==0?-1:sizes[a]-1);
            assert(strstr(diagnostic,expected));
            r=reads;i=draws;frame(in,p);assert(reads==r && draws==i);
        }
        missing_asset=short_asset=NULL;fail=1;
        mf_ws_runtime_begin(0,&palette,now);frame(in,p);frame(in,p);frame(in,p);frame(in,p);
        assert(strstr(diagnostic,"WCELL.BIN") && strstr(diagnostic,"READ/ALLOC") && !in_stage);
        fail=0;register_fail=1;
        mf_ws_runtime_begin(0,&palette,now);frame(in,p);frame(in,p);frame(in,p);frame(in,p);
        assert(strstr(diagnostic,"WBUCK.BIN") && strstr(diagnostic,"REGISTER") && last==-1 && !in_stage);
        register_fail=0;missing_dir=1;cds=0;r=reads;i=resets;
        mf_ws_runtime_begin(0,&palette,now);frame(in,p);frame(in,p);frame(in,p);frame(in,p);
        assert(strstr(diagnostic,"ALEVEL2") && strstr(diagnostic,"DIRECTORY"));
        assert(cds==0 && reads==r && resets==i);
    }
    puts("PASS filesystem: root table overflow reproduced; all twenty-four assets read in ALEVEL2; parent restored; per-asset missing/length/read/registration errors");
    puts("PASS actual Level 2 loader: real-VBlank drain, bank reset, 18 definitions/28032 bytes, arena bounds, CRAM/font isolation, SCSP release, no gameplay allocations/I/O, partial-load failure");
    return 0;
}
