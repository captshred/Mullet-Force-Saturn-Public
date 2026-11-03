#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <dlfcn.h>
#include "libretro.h"
static unsigned frame,pixel_format;static unsigned char street_rgb[640*240*3],sky_rgb[512*64*3];static unsigned positions;static unsigned long long checked_pixels;static unsigned char *high_ram;static unsigned camera_address;static const char *outdir;
static void logger(enum retro_log_level level,const char *fmt,...){va_list ap;(void)level;va_start(ap,fmt);vfprintf(stderr,fmt,ap);va_end(ap);}
static bool environment(unsigned cmd,void *data)
{
 switch(cmd){
 case RETRO_ENVIRONMENT_SET_MEMORY_MAPS:{struct retro_memory_map *m=data;
  for(unsigned i=0;i<m->num_descriptors;i++)if(m->descriptors[i].start==0x6000000)high_ram=m->descriptors[i].ptr;
  return true;}
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
static unsigned camera_at(unsigned i){return i<=7872?i:15744-i;}
static void video(const void *data,unsigned w,unsigned h,size_t pitch)
{
 char path[512];FILE *f;unsigned y,x;const unsigned char *bytes=data;
 if(!data || data==RETRO_HW_FRAME_BUFFER_VALID)return;
 if(frame<305 || (frame-300)%6!=5)return;
 unsigned camera=camera_at((frame-300)/6),errors=0;
 if(w!=320 || h!=240)exit(4);
 bool capture=camera==0 || camera==1 || camera==127 || camera==128 || camera==511 || camera==512 || camera==1023 || camera==1024 || camera==4095 || camera==7872;
 f=NULL;
 if(capture){snprintf(path,sizeof(path),"%s/frame-%04u.ppm",outdir,(frame-300)/6);f=fopen(path,"wb");if(!f)exit(3);fprintf(f,"P6\n%u %u\n255\n",w,h);}
 for(y=0;y<h;y++)for(x=0;x<w;x++){
  unsigned char c[3];
  if(pixel_format==RETRO_PIXEL_FORMAT_XRGB8888){uint32_t v=((const uint32_t*)(bytes+y*pitch))[x];c[0]=v>>16;c[1]=v>>8;c[2]=v;}
  else{uint16_t v=((const uint16_t*)(bytes+y*pitch))[x];unsigned g=pixel_format==RETRO_PIXEL_FORMAT_RGB565?6:5;
   unsigned r=(v>>(g+5))&31,gg=(v>>5)&((1u<<g)-1),b=v&31;c[0]=(r*255)/31;c[1]=(gg*255)/((1u<<g)-1);c[2]=(b*255)/31;}
  const unsigned char backdrop[3]={8,8,24};const unsigned char *expected;
  if(y==0 || (y>=56 && camera==0 && x==0))expected=backdrop;
  else if(y<56)expected=sky_rgb+((y*512+(camera/4+x)%512)*3);
  else expected=street_rgb+(((y-1)*640+(camera-1+x)%640)*3);
  if(memcmp(c,expected,3)){if(errors<3)fprintf(stderr,"Mismatch camera %u at %u,%u actual %u,%u,%u expected %u,%u,%u\n",camera,x,y,c[0],c[1],c[2],expected[0],expected[1],expected[2]);errors++;}
  checked_pixels++;
  if(f)fwrite(c,1,3,f);
 }
 if(f)fclose(f);
 if(errors){fprintf(stderr,"FAIL %u mismatches at camera %u\n",errors,camera);exit(1);}
 positions++;
 if(positions%1000==0)fprintf(stderr,"Verified %u positions, camera %u\n",positions,camera);
}
static void audio(int16_t l,int16_t r){(void)l;(void)r;}
static size_t batch(const int16_t *d,size_t n){(void)d;return n;}
static void poll(void){}
static int16_t input(unsigned p,unsigned d,unsigned i,unsigned id)
{(void)p;(void)d;(void)i;(void)id;return 0;}

#define LOAD(name) __typeof__(name) *p_##name=dlsym(lib,#name);if(!p_##name){fprintf(stderr,"Missing %s\n",#name);return 2;}
int main(int argc,char **argv)
{
 void *lib;unsigned frames;struct retro_game_info game={0};struct retro_system_info info;
 if(argc<6){fprintf(stderr,"core cue output-directory frames camera-address\n");return 2;}
 outdir=argv[3];frames=atoi(argv[4]);
 char sp[1024],kp[1024];snprintf(sp,sizeof(sp),"%s/street.rgb",outdir);snprintf(kp,sizeof(kp),"%s/sky.rgb",outdir);
 FILE *sf=fopen(sp,"rb"),*kf=fopen(kp,"rb");
 if(!sf || !kf || fread(street_rgb,1,sizeof(street_rgb),sf)!=sizeof(street_rgb) || fread(sky_rgb,1,sizeof(sky_rgb),kf)!=sizeof(sky_rgb))return 5;
 fclose(sf);fclose(kf);camera_address=(unsigned)strtoul(argv[5],NULL,16)-0x6000000;lib=dlopen(argv[1],RTLD_NOW);if(!lib){fprintf(stderr,"%s\n",dlerror());return 2;}
 LOAD(retro_set_environment);LOAD(retro_set_video_refresh);LOAD(retro_set_audio_sample);LOAD(retro_set_audio_sample_batch);LOAD(retro_set_input_poll);LOAD(retro_set_input_state);LOAD(retro_init);LOAD(retro_load_game);LOAD(retro_run);LOAD(retro_unload_game);LOAD(retro_deinit);LOAD(retro_get_system_info);LOAD(retro_set_controller_port_device);
 p_retro_set_environment(environment);p_retro_set_video_refresh(video);p_retro_set_audio_sample(audio);p_retro_set_audio_sample_batch(batch);p_retro_set_input_poll(poll);p_retro_set_input_state(input);p_retro_init();p_retro_set_controller_port_device(0,RETRO_DEVICE_JOYPAD);p_retro_set_controller_port_device(1,RETRO_DEVICE_JOYPAD);p_retro_get_system_info(&info);
 fprintf(stderr,"Core %s %s\n",info.library_name,info.library_version);game.path=argv[2];
 if(!p_retro_load_game(&game)){fprintf(stderr,"LOAD FAILED\n");return 1;}
 for(frame=0;frame<frames;frame++){
  if(frame>=300){unsigned camera=camera_at((frame-300)/6);unsigned swapped=(camera<<16)|(camera>>16);
   if(!high_ram || camera_address>=0x100000)return 4;
   memcpy(high_ram+camera_address,&swapped,4);}
  p_retro_run();
 }
 printf("Verified %u complete 320x240 positions; %llu pixels; zero mismatches.\n",positions,checked_pixels);p_retro_unload_game();p_retro_deinit();return 0;
}
