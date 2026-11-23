/* Controller-driven emulator replay with passive RAM/VDP1 sampling. */
#include <dlfcn.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "libretro.h"
#include "performance_audit.h"

static unsigned field;
static bool overlay_test,reverse_test,handoff_test;
static unsigned reverse_until;
static unsigned width, height, last_video_hash;

static void logger(enum retro_log_level level,const char *format,...)
{
    va_list args;
    (void)level;
    va_start(args,format);
    vfprintf(stderr,format,args);
    va_end(args);
}

static bool environment(unsigned command, void *data)
{
    switch(command) {
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
        *(const char **)data="build";
        return true;
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
        ((struct retro_log_callback *)data)->log=logger;
        return true;
    case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
        *(unsigned *)data=0;
        return true;
    case RETRO_ENVIRONMENT_GET_LANGUAGE:
        *(unsigned *)data=RETRO_LANGUAGE_ENGLISH;
        return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE: {
        struct retro_variable *v=data;
        v->value="disabled";
        if(!strcmp(v->key,"yabause_force_hle_bios"))v->value="enabled";
        if(!strcmp(v->key,"yabause_addon_cartridge"))v->value="none";
        if(!strcmp(v->key,"yabause_numthreads"))v->value="1";
        return true;
    }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
        *(bool *)data=false;
        return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE:
        *(bool *)data=true;
        return true;
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
    case RETRO_ENVIRONMENT_SET_VARIABLES:
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
    case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:
        return true;
    default:
        return false;
    }
}

static void video(const void *data,unsigned w,unsigned h,size_t pitch)
{
    const unsigned char *pixels=data;
    unsigned x,y,hash=2166136261u;
    if(!data || data==RETRO_HW_FRAME_BUFFER_VALID)return;
    width=w;height=h;
    /* Sample the text rows reserved by the diagnostic overlay. */
    for(y=192;y<h && y<224;y++)
        for(x=0;x<w*2;x++)hash=(hash^pixels[y*pitch+x])*16777619u;
    last_video_hash=hash;
}
static void audio(int16_t left,int16_t right){(void)left;(void)right;}
static size_t batch(const int16_t *data,size_t samples){(void)data;return samples;}
static void poll(void){}

static int16_t input(unsigned port,unsigned device,unsigned index,unsigned id)
{
    (void)index;
    if(port>1 || device!=RETRO_DEVICE_JOYPAD)return 0;
    if(id==RETRO_DEVICE_ID_JOYPAD_START)
        return port ? field>=1240 && field<1244 :
            (field>=1100 && field<1104) || (field>=1160 && field<1164);
    if(overlay_test && !port && id==RETRO_DEVICE_ID_JOYPAD_X)
        return (field>=1290 && field<1294) || (field>=1460 && field<1464);
    if(id==RETRO_DEVICE_ID_JOYPAD_B && field>=1290 && field<1560)
        return field%120<88;
    if(handoff_test && !port && id==RETRO_DEVICE_ID_JOYPAD_Y)
        return field>=1700 && field<1704;
    if(field>=1560 && id==RETRO_DEVICE_ID_JOYPAD_RIGHT)
        return field>=reverse_until;
    if(id==RETRO_DEVICE_ID_JOYPAD_LEFT && field<reverse_until)
        return 1;
    if(field>=1560 && id==RETRO_DEVICE_ID_JOYPAD_B)
        return (field+port*20)%138<103;
    return 0;
}

#define LOAD(name,type) type p_##name=dlsym(lib,#name); if(!p_##name){fprintf(stderr,"Missing %s\n",#name);return 2;}
#define RETRO(name) LOAD(name,__typeof__(name) *)
int main(int argc,char **argv)
{
    struct retro_game_info game={0};
    struct retro_system_av_info av;
    unsigned frames,address;
    void *lib;
    typedef unsigned (*read_word)(unsigned);
    typedef unsigned (*read_counter)(void);
    if(argc!=6 || (strcmp(argv[5],"walk") && strcmp(argv[5],"overlay") &&
       strcmp(argv[5],"reverse") && strcmp(argv[5],"handoff")))return 2;
    address=strtoul(argv[3],NULL,0);
    frames=strtoul(argv[4],NULL,10);
    overlay_test=!strcmp(argv[5],"overlay");
    reverse_test=!strcmp(argv[5],"reverse");
    handoff_test=!strcmp(argv[5],"handoff");
    game.path=argv[2];
    lib=dlopen(argv[1],RTLD_NOW);
    if(!lib){fprintf(stderr,"%s\n",dlerror());return 2;}
    RETRO(retro_set_environment);
    RETRO(retro_set_video_refresh);
    RETRO(retro_set_audio_sample);
    RETRO(retro_set_audio_sample_batch);
    RETRO(retro_set_input_poll);
    RETRO(retro_set_input_state);
    RETRO(retro_set_controller_port_device);
    RETRO(retro_init);
    RETRO(retro_load_game);
    RETRO(retro_get_system_av_info);
    RETRO(retro_run);
    RETRO(retro_unload_game);
    RETRO(retro_deinit);
    LOAD(retro_mf_perf_read,read_word);
    LOAD(retro_mf_perf_draws,read_counter);
    LOAD(retro_mf_perf_primitives,read_counter);
    p_retro_set_environment(environment);
    p_retro_set_video_refresh(video);
    p_retro_set_audio_sample(audio);
    p_retro_set_audio_sample_batch(batch);
    p_retro_set_input_poll(poll);
    p_retro_set_input_state(input);
    p_retro_init();
    p_retro_set_controller_port_device(0,RETRO_DEVICE_JOYPAD);
    p_retro_set_controller_port_device(1,RETRO_DEVICE_JOYPAD);
    if(!p_retro_load_game(&game))return 1;
    p_retro_get_system_av_info(&av);
    fprintf(stderr,"Libretro reported %.6f frames/s\n",av.timing.fps);
    puts("field,width,height,text_hash,draw_lists,primitives,publishing,sequence,blank,gap,missed,same_blank,gap_ticks,"
         "divider,hz,blank_ticks,timer_faults,edsr_start,edsr_end,edsr_blank,busy_blanks,flags,camera,enemies,"
         "game_ticks,bank_state,bank_kind,bank_bytes,tile_bytes,map_bytes,decoded_blocks,"
         "cpu,logic,ai,render,audio,bank,fence,install,stream,decode,tile_upload,lookup,copy,mark,prefetch,name_table");
    for(field=0;field<frames;field++) {
        unsigned draws=p_retro_mf_perf_draws(), primitives=p_retro_mf_perf_primitives();
        p_retro_run();
        printf("%u,%u,%u,%u,%u,%u",field,width,height,last_video_hash,
            p_retro_mf_perf_draws()-draws,p_retro_mf_perf_primitives()-primitives);
        for(unsigned i=0;i<sizeof(mf_perf_sample);i+=4)
            printf(",%u",address?p_retro_mf_perf_read(address+i):0);
        putchar('\n');
        if(reverse_test && !reverse_until && address &&
           !p_retro_mf_perf_read(address) &&
           p_retro_mf_perf_read(address+offsetof(mf_perf_sample,camera))>=1830)
            reverse_until=field+240;
    }
    p_retro_unload_game();
    p_retro_deinit();
    return 0;
}
