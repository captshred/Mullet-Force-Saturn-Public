/* Controller-only Level2 audio/combat capture; no emulated RAM writes. */
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
static unsigned skip_frame=3000;
static const char *scenario;static FILE *video_hash;static unsigned frame,pixel_format;static const char *outdir;static bool review_only;
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
 if(!video_hash){char path[512];snprintf(path,sizeof(path),"%s/video.csv",outdir);video_hash=fopen(path,"w");fprintf(video_hash,"frame,world_hash\n");}
 {unsigned hash=2166136261u;for(unsigned y=32;y<h && y<216;y++)for(unsigned x=0;x<w*(pixel_format==RETRO_PIXEL_FORMAT_XRGB8888?4:2);x++){hash^=bytes[y*pitch+x];hash*=16777619u;}fprintf(video_hash,"%u,%u\n",frame,hash);}

 if(review_only){if(frame!=299 && frame!=1000 && frame!=1250 && frame!=1500)return;}
 else if(frame!=2400 && frame!=8000 && frame!=15000 && frame!=16350 && frame!=18000 && frame!=18900 && frame!=2800 && frame!=3300 && frame!=4200 && frame!=6800 && frame!=350 && frame!=480 && frame!=600 && frame!=780 && frame!=1000 && frame!=1300 && frame!=1600 && frame!=6000 && frame!=14000)return;
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
 if(!strcmp(scenario,"pause-short") && !port){
  if(id==RETRO_DEVICE_ID_JOYPAD_START && ((frame>=1850 && frame<1854)||(frame>=1950 && frame<1954)||(frame>=2300 && frame<2304)||(frame>=2500 && frame<2504)||(frame>=2700 && frame<2704)||(frame>=2720 && frame<2724)||(frame>=2740 && frame<2744)||(frame>=2760 && frame<2764)))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_Y && frame>=skip_frame && frame<skip_frame+4)return 1;
 }

 if(!strcmp(scenario,"late-transition") && !port && id==RETRO_DEVICE_ID_JOYPAD_Y && frame>=17000 && frame<17004)return 1;
 if(!strcmp(scenario,"pause-loop") && !port){
  if(id==RETRO_DEVICE_ID_JOYPAD_START && ((frame>=1850 && frame<1854)||(frame>=1950 && frame<1954)||(frame>=2300 && frame<2304)||(frame>=16300 && frame<16304)||(frame>=16500 && frame<16504)||(frame>=16520 && frame<16524)||(frame>=16540 && frame<16544)||(frame>=16560 && frame<16564)))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_Y && frame>=17000 && frame<17004)return 1;
 }

 if(id==RETRO_DEVICE_ID_JOYPAD_START && ((!port && ((frame>=1100 && frame<1104)||(frame>=1800 && frame<1804))) || (port==1 && frame>=1900 && frame<1904 && strcmp(scenario,"music"))))return 1;
 if(!strncmp(scenario,"l2-",3)){
  if(!strcmp(scenario,"l2-restart") && !port && id==RETRO_DEVICE_ID_JOYPAD_START && frame>=6500 && frame<6504)return 1;
  if(!port && id==RETRO_DEVICE_ID_JOYPAD_Y && frame>=2200 && frame<2204)return 1;
  if(frame<2900 || !strcmp(scenario,"l2-music"))return 0;
  unsigned cycle=(frame-2900+port*11)%1200;
  if(id==RETRO_DEVICE_ID_JOYPAD_B){
   if(!strcmp(scenario,"l2-focus"))return 1;
   if(!strcmp(scenario,"l2-shot"))return frame%12<3;
   return cycle<400 ? frame%12<3 : cycle<950;
  }
  if(id==RETRO_DEVICE_ID_JOYPAD_LEFT)return cycle>=950 && cycle<1000;
  if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT)return cycle>=1100 && cycle<1150;
  return 0;
 }
 if(frame<2000 || !strcmp(scenario,"music"))return 0;
 if(!strcmp(scenario,"transition")){
  if(!port && id==RETRO_DEVICE_ID_JOYPAD_Y && frame>=2200 && frame<2204)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_B && frame>=3000 && frame<3800)return 1;
  return 0;
 }
 unsigned phase=(frame-2000+port*7)%120;
 if(id==RETRO_DEVICE_ID_JOYPAD_B && (phase<6 || (phase>=18 && phase<24) || (phase>=36 && phase<42) || (phase>=54 && phase<60) || (phase>=80 && phase<86)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && ((phase>=66 && phase<69)||(phase>=72 && phase<88)))return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_A && frame%360>=300 && frame%360<304)return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_UP && (frame/600)%4==1)return 1;
 if(id==RETRO_DEVICE_ID_JOYPAD_DOWN && (frame/600)%4==3)return 1;

 return 0;
}
#define LOAD(name) __typeof__(name) *p_##name=dlsym(lib,#name);if(!p_##name){fprintf(stderr,"Missing %s\n",#name);return 2;}
int main(int argc,char **argv)
{
 void *lib;unsigned frames;struct retro_game_info game={0};struct retro_system_info info;
 if(argc<5){fprintf(stderr,"core cue output-directory frames [controls]\n");return 2;}
 outdir=argv[3];frames=atoi(argv[4]);if(getenv("MF_UGH_SKIP_FRAME"))skip_frame=(unsigned)strtoul(getenv("MF_UGH_SKIP_FRAME"),NULL,10);scenario=argc>5?argv[5]:"combat";review_only=false;lib=dlopen(argv[1],RTLD_NOW);if(!lib){fprintf(stderr,"%s\n",dlerror());return 2;}

 LOAD(retro_set_environment);LOAD(retro_set_video_refresh);LOAD(retro_set_audio_sample);LOAD(retro_set_audio_sample_batch);LOAD(retro_set_input_poll);LOAD(retro_set_input_state);LOAD(retro_init);LOAD(retro_load_game);LOAD(retro_run);LOAD(retro_unload_game);LOAD(retro_deinit);LOAD(retro_get_system_info);LOAD(retro_set_controller_port_device);
 p_retro_set_environment(environment);p_retro_set_video_refresh(video);p_retro_set_audio_sample(audio);p_retro_set_audio_sample_batch(batch);p_retro_set_input_poll(poll);p_retro_set_input_state(input);p_retro_init();p_retro_set_controller_port_device(0,RETRO_DEVICE_JOYPAD);p_retro_set_controller_port_device(1,RETRO_DEVICE_JOYPAD);p_retro_get_system_info(&info);
 fprintf(stderr,"Core %s %s\n",info.library_name,info.library_version);game.path=argv[2];
 if(!p_retro_load_game(&game)){fprintf(stderr,"LOAD FAILED\n");return 1;}
 unsigned (*probe)(unsigned)=dlsym(lib,"retro_recovery_word");
 unsigned (*native)(unsigned,unsigned)=dlsym(lib,"retro_recovery_slot");if(!native)return 3;
 char path[512];snprintf(path,sizeof(path),"%s/slots.csv",outdir);FILE *csv=fopen(path,"w");if(!probe || !csv)return 3;
 fprintf(csv,"frame,slot,owner,key,eg,stamp,sa,phase,envelope,key_on,tl,output,ecnt\n");
 for(frame=0;frame<frames;frame++){
  void (*mark)(unsigned)=dlsym(lib,"retro_level1_frame");if(mark)mark(frame);
  p_retro_run();
  for(unsigned slot=0;slot<32;slot++){unsigned a=0x8000+64*slot;fprintf(csv,"%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%d,%u\n",frame,slot,probe(a+6),probe(a+2),probe(a+0x3a),probe(a+0x3e),native(slot,0),native(slot,1),native(slot,2),native(slot,3),native(slot,4),(int)native(slot,5),native(slot,6));}

 }

 fclose(csv);p_retro_unload_game();p_retro_deinit();return 0;
}
