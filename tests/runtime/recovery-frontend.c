/* Controller-only Level 2 background/audio smoke capture; no RAM writes. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <dlfcn.h>
#include "libretro.h"
#include "game.h"
#include <stddef.h>
static unsigned frame,pixel_format;static const char *outdir;static bool review_only;
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
 if(review_only){if(frame!=299 && frame!=1000 && frame!=1250 && frame!=1500)return;}
 else if(frame!=350 && frame!=480 && frame!=600 && frame!=780 && frame!=1000 && frame!=1300 && frame!=1600)return;
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
static size_t batch(const int16_t *d,size_t n){static FILE *f;char path[512];if(!f){snprintf(path,sizeof(path),"%s/audio.pcm",outdir);f=fopen(path,"wb");}fwrite(d,4,n,f);return n;}
static void poll(void){}
static int16_t input(unsigned port,unsigned device,unsigned index,unsigned id)
{
 (void)index;if(port>1 || device!=RETRO_DEVICE_JOYPAD)return 0;
 if(id==RETRO_DEVICE_ID_JOYPAD_START && ((!port && ((frame>=600 && frame<604)||(frame>=660 && frame<664))) || (port==1 && frame>=1120 && frame<1124)))return 1;
 if(!port && id==RETRO_DEVICE_ID_JOYPAD_Y && frame>=740 && frame<744)return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_B && frame>=1150 && frame<1800)return 1;
 if(!port && id==RETRO_DEVICE_ID_JOYPAD_LEFT && frame>=1000 && frame<1050)return 1;
 if(!port && id==RETRO_DEVICE_ID_JOYPAD_RIGHT && frame>=1250 && frame<1350)return 1;
 return 0;
}
#define LOAD(name) __typeof__(name) *p_##name=dlsym(lib,#name);if(!p_##name){fprintf(stderr,"Missing %s\n",#name);return 2;}
int main(int argc,char **argv)
{
 void *lib;unsigned frames;struct retro_game_info game={0};struct retro_system_info info;
 if(argc<5){fprintf(stderr,"core cue output-directory frames [controls]\n");return 2;}
 outdir=argv[3];frames=atoi(argv[4]);review_only=false;lib=dlopen(argv[1],RTLD_NOW);if(!lib){fprintf(stderr,"%s\n",dlerror());return 2;}

 LOAD(retro_set_environment);LOAD(retro_set_video_refresh);LOAD(retro_set_audio_sample);LOAD(retro_set_audio_sample_batch);LOAD(retro_set_input_poll);LOAD(retro_set_input_state);LOAD(retro_init);LOAD(retro_load_game);LOAD(retro_run);LOAD(retro_unload_game);LOAD(retro_deinit);LOAD(retro_get_system_info);LOAD(retro_set_controller_port_device);
 p_retro_set_environment(environment);p_retro_set_video_refresh(video);p_retro_set_audio_sample(audio);p_retro_set_audio_sample_batch(batch);p_retro_set_input_poll(poll);p_retro_set_input_state(input);p_retro_init();p_retro_set_controller_port_device(0,RETRO_DEVICE_JOYPAD);p_retro_set_controller_port_device(1,RETRO_DEVICE_JOYPAD);p_retro_get_system_info(&info);
 fprintf(stderr,"Core %s %s\n",info.library_name,info.library_version);game.path=argv[2];
 if(!p_retro_load_game(&game)){fprintf(stderr,"LOAD FAILED\n");return 1;}
 unsigned (*probe)(unsigned)=dlsym(lib,"retro_recovery_word");
 unsigned (*native)(unsigned,unsigned)=dlsym(lib,"retro_recovery_slot");if(!native)return 3;
 char path[512];snprintf(path,sizeof(path),"%s/slots.csv",outdir);FILE *csv=fopen(path,"w");if(!probe || !csv)return 3;
 fprintf(csv,"frame,slot,owner,key,eg,stamp,sa,phase,envelope,key_on,tl,output\n");
 for(frame=0;frame<frames;frame++){
  p_retro_run();
  for(unsigned slot=0;slot<32;slot++){unsigned a=0x8000+64*slot;fprintf(csv,"%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%d\n",frame,slot,probe(a+6),probe(a+2),probe(a+0x3a),probe(a+0x3e),native(slot,0),native(slot,1),native(slot,2),native(slot,3),native(slot,4),(int)native(slot,5));}

 }

 fclose(csv);p_retro_unload_game();p_retro_deinit();return 0;
}
