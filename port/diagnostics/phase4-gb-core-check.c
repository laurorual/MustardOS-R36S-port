/* SPDX-License-Identifier: MIT
 * Private-content API check. No screenshots, PCM dumps or ROM bytes in output.
 */
#define _POSIX_C_SOURCE 200809L
#include "libretro.h"
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static const char *directory;
static unsigned mask, frames, video_frames, audio_frames, nonzero, peak, polls, states;
static uint64_t image_hash;
static bool environment(unsigned cmd, void *data) {
    switch(cmd) {
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: *(const char **)data=directory; return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data=true; return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)data=false; return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE:
        ((struct retro_variable *)data)->value=NULL;
        if (!strcmp(((struct retro_variable *)data)->key,"gambatte_gb_bootloader")) {
            ((struct retro_variable *)data)->value="disabled"; return true;
        }
        return false;
    case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION: *(unsigned *)data=0; return true;
    case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS: return true;
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
        assert(*(enum retro_pixel_format *)data==RETRO_PIXEL_FORMAT_RGB565); return true;
    case RETRO_ENVIRONMENT_SET_VARIABLES:
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
    case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO: return true;
    default: return false;
    }
}
static void video(const void *data,unsigned w,unsigned h,size_t pitch) {
    frames++; if (!data) return;
    assert(w==160 && h==144 && pitch>=320); video_frames++;
    image_hash=UINT64_C(14695981039346656037);
    for (unsigned y=0;y<h;y++) for(unsigned x=0;x<320;x++)
        image_hash=(image_hash^((const unsigned char *)data)[y*pitch+x])*UINT64_C(1099511628211);
}
static void sample(int16_t l,int16_t r) {
    unsigned a=l<0?-(int)l:l,b=r<0?-(int)r:r;
    if(a>peak)peak=a;if(b>peak)peak=b;
    nonzero+=(l!=0 || r!=0);audio_frames++;
}
static size_t audio(const int16_t *data,size_t n) {
    assert(data && n<=65536);
    for(size_t i=0;i<n;i++)sample(data[i*2],data[i*2+1]);
    return n;
}
static void poll(void) { polls++; }
static int16_t input(unsigned port,unsigned device,unsigned index,unsigned id) {
    (void)device;(void)index;states++;if(port)return 0;
    return id==RETRO_DEVICE_ID_JOYPAD_MASK?(int16_t)mask:(int16_t)((mask>>id)&1U);
}
#define LOAD(ret,name,args) ret (*name) args;do{void *s=dlsym(handle,#name);assert(s);memcpy(&name,&s,sizeof(name));}while(0)
int main(int argc,char **argv) {
    assert(argc==4);directory=argv[3];
    void *handle=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);
    if(!handle){fprintf(stderr,"%s\n",dlerror());return 1;}
    LOAD(unsigned,retro_api_version,(void));LOAD(void,retro_set_environment,(retro_environment_t));
    LOAD(void,retro_set_video_refresh,(retro_video_refresh_t));LOAD(void,retro_set_audio_sample,(retro_audio_sample_t));
    LOAD(void,retro_set_audio_sample_batch,(retro_audio_sample_batch_t));LOAD(void,retro_set_input_poll,(retro_input_poll_t));
    LOAD(void,retro_set_input_state,(retro_input_state_t));LOAD(void,retro_init,(void));LOAD(void,retro_deinit,(void));
    LOAD(void,retro_get_system_info,(struct retro_system_info*));LOAD(void,retro_get_system_av_info,(struct retro_system_av_info*));
    LOAD(bool,retro_load_game,(const struct retro_game_info*));LOAD(void,retro_run,(void));LOAD(void,retro_reset,(void));
    LOAD(void,retro_unload_game,(void));LOAD(void*,retro_get_memory_data,(unsigned));LOAD(size_t,retro_get_memory_size,(unsigned));
    LOAD(size_t,retro_serialize_size,(void));LOAD(bool,retro_serialize,(void*,size_t));LOAD(bool,retro_unserialize,(const void*,size_t));
    assert(retro_api_version()==1);
    retro_set_environment(environment);retro_set_video_refresh(video);retro_set_audio_sample(sample);
    retro_set_audio_sample_batch(audio);retro_set_input_poll(poll);retro_set_input_state(input);retro_init();
    struct retro_system_info info;retro_get_system_info(&info);assert(strstr(info.library_name,"Gambatte"));
    FILE *f=fopen(argv[2],"rb");assert(f);assert(!fseek(f,0,SEEK_END));long length=ftell(f);assert(length==65536);rewind(f);
    unsigned char *rom=malloc((size_t)length);assert(rom && fread(rom,1,(size_t)length,f)==(size_t)length);fclose(f);
    unsigned char check=0;for(unsigned i=0x134;i<=0x14c;i++)check=(unsigned char)(check-rom[i]-1);
    assert(check==rom[0x14d]);
    struct retro_game_info game={.path=argv[2],.data=rom,.size=(size_t)length};assert(retro_load_game(&game));
    struct retro_system_av_info av;retro_get_system_av_info(&av);
    assert(av.timing.fps>59 && av.timing.fps<61 && av.timing.sample_rate>=32000 && av.timing.sample_rate<=96000);
    uint64_t initial=0;
    for(unsigned i=0;i<600;i++) {
        mask=i>=180 && i<185 ? 1U<<RETRO_DEVICE_ID_JOYPAD_START :
             i>=240 && i<300 ? 1U<<RETRO_DEVICE_ID_JOYPAD_RIGHT : 0;
        retro_run();if(i==120)initial=image_hash;
    }
    assert(video_frames>500 && initial!=image_hash && audio_frames>100000 && nonzero>1000 && peak>0);
    assert(polls>500 && states>500);
    size_t ram_size=retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM);
    assert(ram_size>0 && ram_size<=65536);
    void *saved_ram=malloc(ram_size);assert(saved_ram);
    size_t size=retro_serialize_size();assert(size && size<8*1024*1024);
    void *state=malloc(size);assert(state && retro_serialize(state,size));
    memcpy(saved_ram,retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM),ram_size);
    mask=0;for(unsigned i=0;i<10;i++)retro_run();
    assert(retro_unserialize(state,size));
    assert(!memcmp(saved_ram,retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM),ram_size));
    free(saved_ram);free(state);retro_reset();for(unsigned i=0;i<5;i++)retro_run();
    printf("C49_GB_API_OK frames=%u video=160x144 format=RGB565 audio_frames=%u nonzero_frames=%u peak=%u rate=%.0f fps=%.6f polls=%u states=%u reset_serialize_RAM=1\n",
           frames,audio_frames,nonzero,peak,av.timing.sample_rate,av.timing.fps,polls,states);
    retro_unload_game();retro_deinit();free(rom);assert(!dlclose(handle));return 0;
}
