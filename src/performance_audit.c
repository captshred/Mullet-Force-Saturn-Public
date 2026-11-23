#include "performance_audit.h"
#if MF_PERFORMANCE_AUDIT
#include <jo/jo.h>

#define FRC_HIGH (*(volatile unsigned char *)0xfffffe12)
#define FRC_LOW  (*(volatile unsigned char *)0xfffffe13)
#define FRT_TCR  (*(volatile unsigned char *)0xfffffe16)
/* BIOS clock mode word, SYS_GETSYSCK in SGL SEGA_SYS.H. */
#define SYS_CLOCK_MODE (*(volatile unsigned int *)0x06000324)
#define FRT_TCSR (*(volatile unsigned char *)0xfffffe11)

volatile mf_perf_sample mf_perf_latest __attribute__((used,externally_visible));
static volatile unsigned blank, accumulated, anchor, blank_ticks, edsr_blank, busy_blanks, timer_faults;
static unsigned divider, cpu_khz, field_rate, expected, ticks_per_tenth;
static unsigned start, previous_start, previous_blank;
static unsigned measuring, enabled, visible_last, y_last, next_overlay;
static unsigned missed, same_blank, last_busy_blanks;
static unsigned sums[MF_PERF_SECTIONS], peaks[MF_PERF_SECTIONS], count;
static mf_perf_sample frame;

static unsigned frc(void)
{
    /* The SH-2 latches low on a high-byte read. Repeat if high changed,
       including on emulators that implement the two bytes independently. */
    unsigned high,low;
    do {
        high=FRC_HIGH;
        low=FRC_LOW;
    } while(high!=FRC_HIGH);
    return (high<<8)|low;
}

void mf_perf_init(void)
{
    unsigned mode=FRT_TCR&3u;
    field_rate=(JO_VDP2_TVSTAT&1u)?50:60;
    cpu_khz=field_rate==50?(SYS_CLOCK_MODE?28438u:26656u):
        (SYS_CLOCK_MODE?28636u:26847u);
    divider=mode<3?8u<<(2u*mode):0;
    expected=divider?cpu_khz*1000u/(divider*field_rate):0;
    ticks_per_tenth=divider?cpu_khz/(10u*divider):0;
    anchor=frc();
}

void mf_perf_vblank(void)
{
    unsigned raw=frc(),mode=FRT_TCR&3u,delta=(unsigned short)(raw-anchor);
    unsigned status=JO_VDP1_EDSR;
    if(!expected || mode==3 || (8u<<(2u*mode))!=divider ||
       (FRT_TCSR&1u) || (blank && (delta<expected*3u/4u || delta>expected*5u/4u)))
        ++timer_faults;
    accumulated+=delta;
    blank_ticks=delta;
    anchor=raw;
    edsr_blank=status;
    if(!(status&2u))++busy_blanks;
    ++blank;
}

unsigned mf_perf_time(void)
{
    unsigned before, base, raw, last;
    do {
        before=blank;
        base=accumulated;
        last=anchor;
        raw=frc();
    } while(before!=blank);
    return base+(unsigned short)(raw-last);
}

void mf_perf_begin(void)
{
    unsigned current, i;
    do {
        current=blank;
        start=mf_perf_time();
        frame.edsr_start=JO_VDP1_EDSR;
        frame.edsr_blank=edsr_blank;
        frame.busy_blanks=busy_blanks;
        frame.blank_ticks=blank_ticks;
    } while(current!=blank);
    frame.blank=current;
    frame.gap=current-previous_blank;
    frame.gap_ticks=start-previous_start;
    frame.timer_faults=timer_faults;
    frame.bank_bytes=frame.tile_bytes=frame.map_bytes=frame.decoded_blocks=0;
    for(i=0;i<MF_PERF_SECTIONS;i++)frame.ticks[i]=0;
    measuring=1;
}

void mf_perf_add(unsigned section,unsigned stamp)
{
    if(measuring)frame.ticks[section]+=mf_perf_time()-stamp;
}

void mf_perf_bank(unsigned state,unsigned kind,unsigned bytes)
{
    frame.bank_state=state;
    frame.bank_kind=kind;
    frame.bank_bytes+=bytes;
}

void mf_perf_stream(unsigned tiles,unsigned map,unsigned blocks)
{
    frame.tile_bytes+=tiles;
    frame.map_bytes+=map;
    frame.decoded_blocks+=blocks;
}

void mf_perf_end(unsigned flags,unsigned camera,unsigned enemies,unsigned game_ticks)
{
    unsigned i;
    frame.edsr_end=JO_VDP1_EDSR;
    frame.ticks[MF_PERF_CPU]=mf_perf_time()-start;
    measuring=0;
    if(frame.sequence) {
        if(frame.gap>1)missed+=frame.gap-1;
        if(!frame.gap)++same_blank;
    } else frame.gap=frame.gap_ticks=0;
    previous_blank=frame.blank;
    previous_start=start;
    frame.missed=missed;
    frame.same_blank=same_blank;
    frame.clocks_per_tick=divider;
    frame.hz=field_rate;
    frame.flags=flags;
    frame.camera=camera;
    frame.enemies=enemies;
    frame.game_ticks=game_ticks;
    frame.timer_faults=timer_faults;
    ++frame.sequence;
    frame.publishing=1;
    mf_perf_latest.publishing=1;
    mf_perf_latest=frame;
    mf_perf_latest.publishing=0;
    if(!enabled)return;
    ++count;
    for(i=0;i<MF_PERF_SECTIONS;i++) {
        sums[i]+=frame.ticks[i];
        if(frame.ticks[i]>peaks[i])peaks[i]=frame.ticks[i];
    }
}

static unsigned tenth_ms(unsigned ticks)
{
    return ticks_per_tenth?ticks/ticks_per_tenth:0;
}

void mf_perf_overlay(int y_held,int visible)
{
    unsigned i;
    if(y_held && !y_last && visible) {
        enabled=!enabled;
        next_overlay=frame.blank;
        count=0;
        for(i=0;i<MF_PERF_SECTIONS;i++)sums[i]=peaks[i]=0;
        last_busy_blanks=frame.busy_blanks;
    }
    y_last=y_held;
    visible=visible && enabled;
    if(!visible && visible_last)
        for(i=24;i<=27;i++)jo_clear_screen_line(i);
    visible_last=visible;
    if(!visible) {
        count=0;
        for(i=0;i<MF_PERF_SECTIONS;i++)sums[i]=peaks[i]=0;
        return;
    }
    if(!count || (int)(frame.blank-next_overlay)<0)return;
    for(i=24;i<=27;i++)jo_clear_screen_line(i);
    jo_printf(1,24,"%uHZ GAP %u MISS %u CEF0 %u",frame.hz,frame.gap,missed,
        frame.busy_blanks-last_busy_blanks);
    jo_printf(1,25,"0.1MS CPU %u/%u L %u AI %u",tenth_ms(sums[MF_PERF_CPU]/count),
        tenth_ms(peaks[MF_PERF_CPU]),tenth_ms(peaks[MF_PERF_LOGIC]),tenth_ms(peaks[MF_PERF_AI]));
    jo_printf(1,26,"DRAW %u AUD %u BANK %u MAP %u",tenth_ms(peaks[MF_PERF_RENDER]),
        tenth_ms(peaks[MF_PERF_AUDIO]),tenth_ms(peaks[MF_PERF_BANK]),tenth_ms(peaks[MF_PERF_STREAM]));
    jo_printf(1,27,"BANK STATE %u TIMER FLAGS %u",frame.bank_state,frame.timer_faults);
    next_overlay=frame.blank+30;
    last_busy_blanks=frame.busy_blanks;
    count=0;
    for(i=0;i<MF_PERF_SECTIONS;i++)sums[i]=peaks[i]=0;
}
#endif
