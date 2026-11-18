/* Controller-driven Saturn startup and read-only CPU, RAM and PCM observations. */
#include <dlfcn.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libretro.h"

static const char *system_directory;
static const char *save_directory;
static unsigned frame, skip_frame, pause_frame, resume_frame;
static unsigned starts[2] = {1000, 1020}, join_frame = 1040;
static unsigned gameplay_frame = 0;
static unsigned long long pcm_frames;
static unsigned pcm_peak;

static void log_message(enum retro_log_level level, const char *format, ...)
{
    va_list args;
    if (level < RETRO_LOG_WARN)
        return;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
}

static bool environment(unsigned command, void *data)
{
    switch (command) {
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
        *(const char **)data = system_directory ? system_directory : save_directory;
        return true;
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
        ((struct retro_log_callback *)data)->log = log_message;
        return true;
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
        *(const char **)data = save_directory;
        return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE: {
        struct retro_variable *option = data;
        option->value = "disabled";
        if (!strcmp(option->key, "yabause_force_hle_bios") && !system_directory)
            option->value = "enabled";
        if (!strcmp(option->key, "yabause_addon_cartridge"))
            option->value = "none";
        if (!strcmp(option->key, "yabause_numthreads"))
            option->value = "1";
        return true;
    }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
        *(bool *)data = false;
        return true;
    case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
        *(unsigned *)data = 0;
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

static void video(const void *data, unsigned width, unsigned height, size_t pitch)
{
    (void)data; (void)width; (void)height; (void)pitch;
}

static void audio(int16_t left, int16_t right)
{
    unsigned peak = (unsigned)abs(left);
    if ((unsigned)abs(right) > peak)
        peak = (unsigned)abs(right);
    if (peak > pcm_peak)
        pcm_peak = peak;
    ++pcm_frames;
}

static size_t audio_batch(const int16_t *samples, size_t count)
{
    for (size_t i = 0; i < count; ++i)
        audio(samples[i * 2], samples[i * 2 + 1]);
    return count;
}

static void poll(void) {}

static bool press(unsigned at)
{
    return at && frame >= at && frame - at < 4;
}

static int16_t input(unsigned port, unsigned device, unsigned index, unsigned id)
{
    (void)index;
    if (port > 1 || device != RETRO_DEVICE_JOYPAD)
        return 0;
    if (id == RETRO_DEVICE_ID_JOYPAD_START) {
        if (port)
            return press(join_frame);
        return press(starts[0]) || press(starts[1]) || press(pause_frame) || press(resume_frame);
    }
    if (id == RETRO_DEVICE_ID_JOYPAD_Y)
        return !port && press(skip_frame); /* Saturn X. */
    if (gameplay_frame && frame - gameplay_frame >= 12 && id == RETRO_DEVICE_ID_JOYPAD_B) {
        unsigned elapsed = frame - gameplay_frame;
        return (elapsed + port * 7) % 240 < 100 || elapsed % 14 < 4; /* Saturn A. */
    }
    if (gameplay_frame && id == (port ? RETRO_DEVICE_ID_JOYPAD_LEFT : RETRO_DEVICE_ID_JOYPAD_RIGHT))
        return (frame - gameplay_frame) % 210 < 30;
    return 0;
}

#define LOAD(name) \
    __typeof__(name) *call_##name = dlsym(core, #name); \
    if (!call_##name) { fprintf(stderr, "Missing %s\n", #name); return 2; }

static unsigned arg(const char *text)
{
    return (unsigned)strtoul(text, NULL, 0);
}

int main(int argc, char **argv)
{
    if (argc != 15) {
        fprintf(stderr, "core cue save-dir bios-dir-or-dash phase error game-started trace skip pause resume frames warm stress\n");
        return 2;
    }
    setvbuf(stdout, NULL, _IOLBF, 0);
    save_directory = argv[3];
    system_directory = strcmp(argv[4], "-") ? argv[4] : NULL;
    unsigned phase_address = arg(argv[5]), error_address = arg(argv[6]);
    unsigned started_address = arg(argv[7]), trace_address = arg(argv[8]);
    skip_frame = arg(argv[9]); pause_frame = arg(argv[10]); resume_frame = arg(argv[11]);
    unsigned frames = arg(argv[12]), warm = arg(argv[13]), stress = arg(argv[14]);
    const char *first_start = getenv("MF_E108_START_FRAME");
    if (first_start) {
        starts[0] = arg(first_start);
        starts[1] = starts[0] + 20;
        join_frame = starts[0] + 40;
    }
    void *core = dlopen(argv[1], RTLD_NOW);
    if (!core) {
        fprintf(stderr, "%s\n", dlerror());
        return 2;
    }
    LOAD(retro_set_environment); LOAD(retro_set_video_refresh);
    LOAD(retro_set_audio_sample); LOAD(retro_set_audio_sample_batch);
    LOAD(retro_set_input_poll); LOAD(retro_set_input_state);
    LOAD(retro_init); LOAD(retro_deinit); LOAD(retro_load_game);
    LOAD(retro_unload_game); LOAD(retro_run); LOAD(retro_reset);
    LOAD(retro_set_controller_port_device);
    unsigned (*ram)(unsigned) = dlsym(core, "retro_mf_high_ram");
    unsigned (*sound)(unsigned) = dlsym(core, "retro_mf_sound_ram");
    void (*cpu)(unsigned *) = dlsym(core, "retro_mf_cpu");
    void (*scsp)(unsigned *) = dlsym(core, "retro_mf_scsp_state");
    if (!ram || !sound || !cpu || !scsp) {
        fprintf(stderr, "Missing startup probes\n");
        return 2;
    }

    call_retro_set_environment(environment);
    call_retro_set_video_refresh(video);
    call_retro_set_audio_sample(audio);
    call_retro_set_audio_sample_batch(audio_batch);
    call_retro_set_input_poll(poll);
    call_retro_set_input_state(input);
    call_retro_init();
    for (unsigned port = 0; port < 2; ++port)
        call_retro_set_controller_port_device(port, RETRO_DEVICE_JOYPAD);
    struct retro_game_info game = {.path = argv[2]};
    if (!call_retro_load_game(&game)) {
        fprintf(stderr, "CUE load failed\n");
        return 2;
    }

    int result = 0;
    puts("round,frame,phase,error,level1,trace_count,68k_pc,68k_sr,68k_sp,sh2_pc,sh2_sp,sh2_sr,cursor,flags,timer,history,gate,driver_error,driver_status,queue,68k_running,scsp_key,scsp_envelope,scsp_unreleased,scsp_zero_rr,scsp_stale_monitor");
    for (unsigned round = 0; round <= warm; ++round) {
        if (round)
            call_retro_reset();
        unsigned phase = 0, error = 0, level1 = 0, first_level1 = 0, previous = 0;
        gameplay_frame = 0; pcm_peak = 0; pcm_frames = 0;
        for (frame = 0; frame < frames; ++frame) {
            call_retro_run();
            phase = ram(phase_address);
            error = ram(error_address);
            level1 = ram(started_address);
            if (level1 == 1 && !first_level1)
                first_level1 = frame;
            if (phase == 3 && !gameplay_frame) {
                gameplay_frame = frame;
                pcm_peak = 0; pcm_frames = 0;
            }
            if (phase != previous || phase == 1 || phase == 2 || error ||
                (phase == 3 && (frame - gameplay_frame) % 30 == 0)) {
                unsigned regs[6];
                cpu(regs);
                printf("%u,%u,%u,%u,%u,%u,%06x,%04x,%06x,%08x,%08x,%08x,%04x,%04x,%04x,%04x,%04x,%04x,%04x,",
                       round, frame, phase, error, level1, ram(trace_address),
                       regs[0], regs[1], regs[2], regs[3], regs[4], regs[5],
                       sound(0x041a), sound(0x04e0), sound(0x8838), sound(0x883a),
                       sound(0x10da), sound(0x0416), sound(0x0420));
                for (unsigned i = 0; i < 8; ++i)
                    printf("%02x", sound(0x0700 + i * 16) >> 8);
                unsigned slots[6];
                scsp(slots);
                printf(",%u,%08x,%08x,%08x,%08x,%08x\n",
                       slots[0], slots[1], slots[2], slots[3], slots[4], slots[5]);
            }
            previous = phase;
            if (phase == 4 || error || (gameplay_frame && frame - gameplay_frame >= stress))
                break;
        }
        printf("RESULT,%u,%u,%u,%u,%u,%u,%llu,%u\n",
               round, frame, phase, error, first_level1, gameplay_frame, pcm_frames, pcm_peak);
        fflush(stdout);
        if (error || phase != 3 || !first_level1 || !gameplay_frame ||
            (stress && (!pcm_peak || frame - gameplay_frame < stress))) {
            result = error ? 10 : 11;
            char path[4096];
            snprintf(path, sizeof(path), "%s/failure-memory.txt", save_directory);
            FILE *dump = fopen(path, "w");
            if (dump) {
                for (unsigned i = 0; i < 4756; i += 4)
                    fprintf(dump, "trace %04x %08x\n", i, ram(trace_address + i));
                for (unsigned i = 0; i < 0x10000; i += 2)
                    fprintf(dump, "sound %04x %04x\n", i, sound(i));
                fclose(dump);
            }
        }
    }
    call_retro_unload_game();
    call_retro_deinit();
    return result;
}
