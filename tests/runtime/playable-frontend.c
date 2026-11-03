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
static unsigned frame,pixel_format;static unsigned game_addr,idle_addr;static FILE *trace;static const char *outdir;static bool controls;static int diagnostic_mode;static bool review_only;
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
 else if(frame<320 || frame>1040 || (frame>520 && frame%5))return;
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
 (void)index;if(!controls || port>1 || device!=RETRO_DEVICE_JOYPAD)return 0;
 if(review_only){
  if(port)return 0;
  if(id==RETRO_DEVICE_ID_JOYPAD_DOWN && frame>=300 && frame<304)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_START && ((frame>=1200 && frame<1204)||(frame>=1220 && frame<1224)))return 1;
  return 0;
 }
 if(id==RETRO_DEVICE_ID_JOYPAD_START && ((!port && ((frame>=300 && frame<304)||(frame>=320 && frame<324)||(frame>=800 && frame<804)||(frame>=820 && frame<824))) || (port==1 && frame>=340 && frame<344)))return 1;
 if(!port){
  if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && ((frame>=360 && frame<420)||(frame>=750 && frame<754)||(frame>=762 && frame<766)||(frame>=910 && frame<970)))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_LEFT && ((frame>=420 && frame<450)||(frame>=850 && frame<910)))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_DOWN && frame>=420 && frame<450)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_UP && frame>=910 && frame<970)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_B && ((frame>=540 && frame<544)||(frame>=764 && frame<768)))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_A && frame>=530 && frame<534)return 1;
 }else{
  if(id==RETRO_DEVICE_ID_JOYPAD_LEFT && ((frame>=360 && frame<420)||(frame>=910 && frame<970)))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_UP && frame>=360 && frame<420)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && ((frame>=420 && frame<500)||(frame>=510 && frame<514)||(frame>=522 && frame<526)||(frame>=850 && frame<910)))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_DOWN && ((frame>=420 && frame<450)||(frame>=910 && frame<970)))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_B && ((frame>=522 && frame<526)||(frame>=530 && frame<534)||(frame>=580 && frame<710)))return 1;
 }
 return 0;
}
static unsigned read32(const unsigned char *p,unsigned at)
{ unsigned v;memcpy(&v,p+(at&0xfffff),4);return (v>>16)|(v<<16); }
static void snapshot(const unsigned char *state,size_t size)
{
 size_t pos=20;const unsigned char *ram=NULL,*vram=NULL;uint32_t hash=2166136261u,v;unsigned i;
 while(pos+12<size){unsigned len;memcpy(&len,state+pos+8,4);if(pos+12+len>size)break;
  if(!memcmp(state+pos,"OTHR",4))ram=state+pos+12+0x10000;
  if(!memcmp(state+pos,"VDP1",4))vram=state+pos+12+52;
  pos+=12+len;
 }
 if(!ram || !vram){fprintf(stderr,"Missing save-state memory chunks\n");exit(4);}
 fwrite(&frame,4,1,trace);
 for(i=0;i<offsetof(mf_game,dash);i+=4){v=read32(ram,game_addr+i);fwrite(&v,4,1,trace);}
 for(i=0;i<2;i++){v=idle_addr?read32(ram,idle_addr+4*i):0;fwrite(&v,4,1,trace);}
 if(review_only && (frame==299 || frame==1000 || frame==1500)){
  char path[512];FILE *dump;snprintf(path,sizeof(path),"%s/frame-%04u.wram",outdir,frame);dump=fopen(path,"wb");if(!dump)exit(3);fwrite(ram,0x100000,1,dump);fclose(dump);
 }
 for(i=0x10000;i<0x7fef8;i++)hash=(hash^vram[i])*16777619u;
 fwrite(&hash,4,1,trace);
}

#define LOAD(name) __typeof__(name) *p_##name=dlsym(lib,#name);if(!p_##name){fprintf(stderr,"Missing %s\n",#name);return 2;}
int main(int argc,char **argv)
{
 void *lib;unsigned frames;struct retro_game_info game={0};struct retro_system_info info;
 if(argc<8){fprintf(stderr,"core cue output-directory frames [controls]\n");return 2;}
 outdir=argv[3];frames=atoi(argv[4]);controls=argc>5;review_only=!strcmp(argv[5],"review");diagnostic_mode=argc>5 && !strcmp(argv[5],"diagnostics");lib=dlopen(argv[1],RTLD_NOW);if(!lib){fprintf(stderr,"%s\n",dlerror());return 2;}
 LOAD(retro_serialize_size);LOAD(retro_serialize);
 LOAD(retro_set_environment);LOAD(retro_set_video_refresh);LOAD(retro_set_audio_sample);LOAD(retro_set_audio_sample_batch);LOAD(retro_set_input_poll);LOAD(retro_set_input_state);LOAD(retro_init);LOAD(retro_load_game);LOAD(retro_run);LOAD(retro_unload_game);LOAD(retro_deinit);LOAD(retro_get_system_info);LOAD(retro_set_controller_port_device);
 p_retro_set_environment(environment);p_retro_set_video_refresh(video);p_retro_set_audio_sample(audio);p_retro_set_audio_sample_batch(batch);p_retro_set_input_poll(poll);p_retro_set_input_state(input);p_retro_init();p_retro_set_controller_port_device(0,RETRO_DEVICE_JOYPAD);p_retro_set_controller_port_device(1,RETRO_DEVICE_JOYPAD);p_retro_get_system_info(&info);
 fprintf(stderr,"Core %s %s\n",info.library_name,info.library_version);game.path=argv[2];
 if(!p_retro_load_game(&game)){fprintf(stderr,"LOAD FAILED\n");return 1;}
 game_addr=(unsigned)strtoul(argv[6],NULL,16);idle_addr=(unsigned)strtoul(argv[7],NULL,16);
 {char path[512];snprintf(path,sizeof(path),"%s/trace.bin",outdir);trace=fopen(path,"wb");if(!trace)return 3;}
 for(frame=0;frame<frames;frame++){
  p_retro_run();
  if(frame>=295){size_t n=p_retro_serialize_size();unsigned char *state=malloc(n);if(!state || !p_retro_serialize(state,n))return 4;snapshot(state,n);free(state);}
 }
 fclose(trace);
 p_retro_unload_game();p_retro_deinit();return 0;
}
