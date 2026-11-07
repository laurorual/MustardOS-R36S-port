/* SPDX-License-Identifier: MIT */
#define _POSIX_C_SOURCE 200809L
#include "libretro.h"
#include <assert.h>
#include <dlfcn.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static const char *directory;static unsigned input_mask,frames,video_frames,audio_frames,max_abs,width_seen,height_seen;static uint64_t image_hash;static int pixel_format;static unsigned histogram[65536];
static void logger(enum retro_log_level level,const char *format,...) {(void)level;va_list a;va_start(a,format);vfprintf(stderr,format,a);va_end(a);}
static bool env(unsigned cmd,void *data){
 switch(cmd){
 case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:((struct retro_log_callback*)data)->log=logger;return true;
 case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:*(const char**)data=directory;return true;
 case RETRO_ENVIRONMENT_GET_CAN_DUPE:*(bool*)data=true;return true;
 case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:*(bool*)data=false;return true;
 case RETRO_ENVIRONMENT_GET_VARIABLE:((struct retro_variable*)data)->value=NULL;return false;
 case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:*(unsigned*)data=0;return true;
 case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS:return true;
 case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:pixel_format=*(enum retro_pixel_format*)data;assert(pixel_format==RETRO_PIXEL_FORMAT_RGB565);return true;
 case RETRO_ENVIRONMENT_SET_VARIABLES:case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:case RETRO_ENVIRONMENT_SET_SUPPORT_ACHIEVEMENTS:return true;
 default:return false;
 }
}
static void video(const void *data,unsigned w,unsigned h,size_t pitch){
 frames++;if(!data)return;
 assert(w==256 && (h==224||h==240) && pitch>=w*2);width_seen=w;height_seen=h;video_frames++;
 memset(histogram,0,sizeof(histogram));
 image_hash=UINT64_C(14695981039346656037);
 for(unsigned y=0;y<h;y++)for(unsigned x=0;x<w;x++){uint16_t color;memcpy(&color,(const unsigned char*)data+y*pitch+x*2,2);histogram[color]++;}
 for(unsigned y=0;y<h;y++)for(unsigned x=0;x<w*2;x++)image_hash=(image_hash^((const unsigned char*)data)[y*pitch+x])*UINT64_C(1099511628211);
}
static void sample(int16_t l,int16_t r){unsigned a=l<0?-(int)l:l,b=r<0?-(int)r:r;if(a>max_abs)max_abs=a;if(b>max_abs)max_abs=b;audio_frames++;}
static size_t audio(const int16_t *p,size_t n){for(size_t i=0;i<n;i++)sample(p[i*2],p[i*2+1]);return n;}
static void poll(void){}
static int16_t input(unsigned port,unsigned device,unsigned index,unsigned id){(void)device;(void)index;if(port)return 0;return id==RETRO_DEVICE_ID_JOYPAD_MASK?(int16_t)input_mask:(int16_t)((input_mask>>id)&1U);}
#define LOAD(ret,name,args) ret (*name) args;do{void *s=dlsym(handle,#name);assert(s);memcpy(&name,&s,sizeof(name));}while(0)
int main(int argc,char **argv){
 assert(argc==4);directory=argv[3];void *handle=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!handle){fprintf(stderr,"%s\n",dlerror());return 1;}
 LOAD(unsigned,retro_api_version,(void));LOAD(void,retro_set_environment,(retro_environment_t));LOAD(void,retro_set_video_refresh,(retro_video_refresh_t));LOAD(void,retro_set_audio_sample,(retro_audio_sample_t));LOAD(void,retro_set_audio_sample_batch,(retro_audio_sample_batch_t));LOAD(void,retro_set_input_poll,(retro_input_poll_t));LOAD(void,retro_set_input_state,(retro_input_state_t));LOAD(void,retro_init,(void));LOAD(void,retro_deinit,(void));LOAD(void,retro_get_system_info,(struct retro_system_info*));LOAD(void,retro_get_system_av_info,(struct retro_system_av_info*));LOAD(bool,retro_load_game,(const struct retro_game_info*));LOAD(void,retro_run,(void));LOAD(void,retro_reset,(void));LOAD(void,retro_unload_game,(void));LOAD(void*,retro_get_memory_data,(unsigned));LOAD(size_t,retro_get_memory_size,(unsigned));LOAD(size_t,retro_serialize_size,(void));LOAD(bool,retro_serialize,(void*,size_t));LOAD(bool,retro_unserialize,(const void*,size_t));
 assert(retro_api_version()==1);retro_set_environment(env);retro_set_video_refresh(video);retro_set_audio_sample(sample);retro_set_audio_sample_batch(audio);retro_set_input_poll(poll);retro_set_input_state(input);retro_init();
 struct retro_system_info info;retro_get_system_info(&info);assert(strstr(info.library_name,"FCEU"));
 FILE *file=fopen(argv[2],"rb");assert(file);assert(!fseek(file,0,SEEK_END));long length=ftell(file);assert(length==24592);rewind(file);void *rom=malloc((size_t)length);assert(rom&&fread(rom,1,(size_t)length,file)==(size_t)length);fclose(file);
 struct retro_game_info game={.path=argv[2],.data=rom,.size=(size_t)length};assert(retro_load_game(&game));
 struct retro_system_av_info av;retro_get_system_av_info(&av);assert(av.timing.fps>59&&av.timing.fps<61&&av.timing.sample_rate>=32000&&av.timing.sample_rate<=96000);
 assert(retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM)==2048);unsigned char *ram=retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);assert(ram);
 for(unsigned i=0;i<60;i++)retro_run();assert(ram[4]==0x47&&ram[5]==0xC3&&ram[0]==120&&ram[1]==112);uint64_t initial=image_hash;
 input_mask=1U<<RETRO_DEVICE_ID_JOYPAD_RIGHT;for(unsigned i=0;i<10;i++)retro_run();assert(ram[0]>120&&ram[1]==112&&image_hash!=initial);unsigned x=ram[0];
 input_mask=1U<<RETRO_DEVICE_ID_JOYPAD_DOWN;for(unsigned i=0;i<10;i++)retro_run();assert(ram[0]==x&&ram[1]>112);
 input_mask=0;size_t size=retro_serialize_size();assert(size&&size<2*1024*1024);void *state=malloc(size);assert(state&&retro_serialize(state,size));unsigned savedx=ram[0],savedy=ram[1];
 input_mask=1U<<RETRO_DEVICE_ID_JOYPAD_LEFT;for(unsigned i=0;i<10;i++)retro_run();assert(ram[0]<savedx);assert(retro_unserialize(state,size));assert(ram[0]==savedx&&ram[1]==savedy);free(state);
 input_mask=1U<<RETRO_DEVICE_ID_JOYPAD_UP;for(unsigned i=0;i<10;i++)retro_run();assert(ram[1]<savedy);
 input_mask=0;retro_reset();for(unsigned i=0;i<60;i++)retro_run();assert(ram[0]==120&&ram[1]==112&&ram[4]==0x47&&ram[5]==0xC3);
 unsigned colors=0,ship_colors=0,star_colors=0;
 for(unsigned i=0;i<65536;i++){if(histogram[i])colors++;if(histogram[i]==38)ship_colors++;if(histogram[i]==160)star_colors++;}
 printf("C47_ROM_PIXELS colors=%u ship38=%u stars160=%u\n",colors,ship_colors,star_colors);
 assert(colors==3&&ship_colors==1&&star_colors==1);
 assert(video_frames>100&&audio_frames>10000);printf("C47_NES_API_OK frames=%u video=%ux%u format=%d audio_frames=%u max_abs=%u rate=%.0f fps=%.6f RAM_input_reset_serialize=1\n",frames,width_seen,height_seen,pixel_format,audio_frames,max_abs,av.timing.sample_rate,av.timing.fps);
 retro_unload_game();retro_deinit();free(rom);assert(!dlclose(handle));return 0;
}
