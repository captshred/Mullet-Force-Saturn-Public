#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <dlfcn.h>
#include "libretro.h"
static unsigned frame,pixel_format;static const char *outdir;static bool controls;static int diagnostic_mode;
static void logger(enum retro_log_level level,const char *fmt,...){va_list ap;(void)level;va_start(ap,fmt);vfprintf(stderr,fmt,ap);va_end(ap);}
static bool environment(unsigned cmd,void *data)
{
 switch(cmd){
 case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:*(const char **)data=outdir;return true;
 case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:((struct retro_log_callback*)data)->log=logger;return true;
 case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:pixel_format=*(unsigned*)data;return true;
 case RETRO_ENVIRONMENT_GET_VARIABLE:{struct retro_variable *v=data;v->value="disabled";
  if(!strcmp(v->key,"yabause_force_hle_bios"))v->value="enabled";
  if(!strcmp(v->key,"yabause_addon_cartridge"))v->value="none";
  if(!strcmp(v->key,"yabause_numthreads"))v->value="1";
  return true;}
 case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:*(bool*)data=false;return true;
 case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:*(unsigned*)data=0;return true;
 case RETRO_ENVIRONMENT_GET_LANGUAGE:*(unsigned*)data=RETRO_LANGUAGE_ENGLISH;return true;
 case RETRO_ENVIRONMENT_GET_CAN_DUPE:*(bool*)data=true;return true;
 case RETRO_ENVIRONMENT_SET_VARIABLES:case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME:return true;
 default:return false;
 }
}
static void video(const void *data,unsigned w,unsigned h,size_t pitch)
{
 char path[512];FILE *f;unsigned y,x;const unsigned char *bytes=data;
 if(!data || data==RETRO_HW_FRAME_BUFFER_VALID)return;
 if((frame<1120 || frame>1160) && (frame<1470 || frame>1640) && frame!=299 && frame!=359 && frame!=389 && frame!=409 && frame!=429 && frame!=449 && frame!=469 && frame!=489 && frame!=509 && frame!=529 && frame!=549 && frame!=569 && frame!=589 && frame!=609 && frame!=629 && frame!=649 && frame!=669 && frame!=689 && frame!=709 && frame!=729 && frame!=749 && frame!=769 && frame!=789 && frame!=809 && frame!=829 && frame!=849 && frame!=869 && frame!=889 && frame!=909 && frame!=929 && frame!=949 && frame!=969 && frame!=989 && frame!=1009 && frame!=1029 && frame!=1049 && frame!=1069 && frame!=1119 && frame!=1199 && frame!=1249 && frame!=1289 && frame!=1399 && frame!=1459 && frame!=1499 && frame!=1599 && frame!=1759 && frame!=1999)return;
 snprintf(path,sizeof(path),"%s/frame-%04u.ppm",outdir,frame);f=fopen(path,"wb");if(!f)exit(3);
 fprintf(f,"P6\n%u %u\n255\n",w,h);
 for(y=0;y<h;y++)for(x=0;x<w;x++){
  unsigned char c[3];
  if(pixel_format==RETRO_PIXEL_FORMAT_XRGB8888){uint32_t v=((const uint32_t*)(bytes+y*pitch))[x];c[0]=v>>16;c[1]=v>>8;c[2]=v;}
  else{uint16_t v=((const uint16_t*)(bytes+y*pitch))[x];unsigned g=pixel_format==RETRO_PIXEL_FORMAT_RGB565?6:5;
   unsigned r=(v>>(g+5))&31,gg=(v>>5)&((1u<<g)-1),b=v&31;c[0]=(r*255)/31;c[1]=(gg*255)/((1u<<g)-1);c[2]=(b*255)/31;}
  fwrite(c,1,3,f);
 }
 fclose(f);fprintf(stderr,"Captured frame %u %ux%u\n",frame,w,h);
}
static void audio(int16_t l,int16_t r){(void)l;(void)r;}
static size_t batch(const int16_t *d,size_t n){(void)d;return n;}
static void poll(void){}
static int16_t input(unsigned port,unsigned device,unsigned index,unsigned id)
{
 (void)index;if(!controls || port || device!=RETRO_DEVICE_JOYPAD)return 0;
 if(id==RETRO_DEVICE_ID_JOYPAD_DOWN && ((frame>=330 && frame<334)||(frame>=1220 && frame<1224)||(frame>=1420 && frame<1424)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_UP && ((frame>=540 && frame<544)||(frame>=1020 && frame<1024)||(frame>=1080 && frame<1084)||(frame>=1120 && frame<1124)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_B && ((frame>=460 && frame<464)||(frame>=660 && frame<664)||(frame>=900 && frame<904)||(frame>=1040 && frame<1044)||(frame>=780 && frame<784)||(frame>=1060 && frame<1064)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_A && ((frame>=350 && frame<354)||(frame>=780 && frame<784)||(frame>=1060 && frame<1064)||(frame>=1100 && frame<1104)||(frame>=1150 && frame<1154)||(frame>=1260 && frame<1264)||(frame>=1440 && frame<1444)||(frame>=1460 && frame<1464)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_R && ((frame>=1160 && frame<1164)||(frame>=1180 && frame<1184)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_LEFT && ((frame>=680 && frame<684)||(frame>=700 && frame<704)||(frame>=720 && frame<724)||(frame>=740 && frame<744)||(frame>=760 && frame<764)||(frame>=920 && frame<924)||(frame>=940 && frame<944)||(frame>=960 && frame<964)||(frame>=980 && frame<984)||(frame>=1000 && frame<1004)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && ((frame>=380 && frame<384)||(frame>=400 && frame<404)||(frame>=420 && frame<424)||(frame>=440 && frame<444)||(frame>=480 && frame<484)||(frame>=500 && frame<504)||(frame>=520 && frame<524)||(frame>=560 && frame<564)||(frame>=580 && frame<584)||(frame>=600 && frame<604)||(frame>=620 && frame<624)||(frame>=640 && frame<644)||(frame>=800 && frame<804)||(frame>=820 && frame<824)||(frame>=840 && frame<844)||(frame>=860 && frame<864)||(frame>=880 && frame<884)||(frame>=1300 && frame<1380)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_START && ((frame>=1740 && frame<1744)||(frame>=1800 && frame<1804)))return 1;

 return 0;
}
#define LOAD(name) __typeof__(name) *p_##name=dlsym(lib,#name);if(!p_##name){fprintf(stderr,"Missing %s\n",#name);return 2;}
int main(int argc,char **argv)
{
 void *lib;unsigned frames;struct retro_game_info game={0};struct retro_system_info info;
 if(argc<5){fprintf(stderr,"core cue output-directory frames [controls]\n");return 2;}
 outdir=argv[3];frames=atoi(argv[4]);controls=argc>5;diagnostic_mode=argc>5 && !strcmp(argv[5],"diagnostics");lib=dlopen(argv[1],RTLD_NOW);if(!lib){fprintf(stderr,"%s\n",dlerror());return 2;}
 LOAD(retro_set_environment);LOAD(retro_set_video_refresh);LOAD(retro_set_audio_sample);LOAD(retro_set_audio_sample_batch);LOAD(retro_set_input_poll);LOAD(retro_set_input_state);LOAD(retro_init);LOAD(retro_load_game);LOAD(retro_run);LOAD(retro_unload_game);LOAD(retro_deinit);LOAD(retro_get_system_info);LOAD(retro_set_controller_port_device);
 p_retro_set_environment(environment);p_retro_set_video_refresh(video);p_retro_set_audio_sample(audio);p_retro_set_audio_sample_batch(batch);p_retro_set_input_poll(poll);p_retro_set_input_state(input);p_retro_init();p_retro_set_controller_port_device(0,RETRO_DEVICE_JOYPAD);p_retro_set_controller_port_device(1,RETRO_DEVICE_JOYPAD);p_retro_get_system_info(&info);
 fprintf(stderr,"Core %s %s\n",info.library_name,info.library_version);game.path=argv[2];
 if(!p_retro_load_game(&game)){fprintf(stderr,"LOAD FAILED\n");return 1;}
 for(frame=0;frame<frames;frame++)p_retro_run();
 p_retro_unload_game();p_retro_deinit();return 0;
}
