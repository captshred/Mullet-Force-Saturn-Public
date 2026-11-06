/* Real Level 2 bank loader/startup with consumed-command driver semantics.
   Transport and SCSP registers are mocked; this is NOT a Saturn emulator. */
#define main existing_audio_regressions
#include "wingsuit_audio_test.c"
#undef main
static void consumed_poll(unsigned now)
{
    unsigned i;commands=0;clock_now=now;
    /* Model a poll immediately after command dispatch: pinned driver 2.10
       advances its exported history cursor and clears its interval timer. */
    assert(!submit(13));
    for(i=0;i<8;i++)if(ram[0x700+i*16]){
        if(ram[0x700+i*16]==8)memcpy(ram+0x500,ram+0xa000,40);
        word(0x41a,((sound_word(0x41a)&0x7f0)+16)&65535);
        word(0x8838,0);ram[0x700+i*16]=0;
    }
    mf_ws_audio_step(now,0);
}
int main(void)
{
    unsigned i;trace_n=0;
    assert(mf_ws_audio_load(read_exact,progress_event));
    for(i=0;i<=120 && mf_ws_audio_ready()==0;i++)consumed_poll(i);
    printf("consumed-command startup: ready=%d cause=%s expected=%d actual=%d timer=%u cursor=%u\n",
        mf_ws_audio_ready(),diagnostic.operation,diagnostic.expected,diagnostic.actual,sound_word(0x8838),sound_word(0x41a));
    fflush(stdout);assert(mf_ws_audio_ready()==1 && startup_done && !startup_failed);
    {const char *names[]={"WDEATH.MAP","WDEATH.SEQ","WDEATH.TON"};
     const unsigned sizes[]={MF_WS_MAP_BYTES,MF_WS_SEQ_BYTES,MF_WS_TON_BYTES};
     const unsigned addresses[]={0xa000,MF_WS_SEQ_ADDR,MF_WS_TON_ADDR};
     for(i=0;i<3;i++){char *data=read_exact(names[i],sizes[i]);assert(!memcmp(ram+addresses[i],data,sizes[i]));jo_free(data);}}
    /* An eagerly running 68K may consume all boot commands inside load().
       Sampling the cursor after submission would falsely time out here too. */
    consume_on_submit=1;trace_n=0;assert(mf_ws_audio_load(read_exact,progress_event));
    assert(commands_empty());
    for(i=0;i<=120 && mf_ws_audio_ready()==0;i++){commands=0;mf_ws_audio_step(500+i,0);}
    assert(mf_ws_audio_ready()==1);consume_on_submit=0;
    /* Empty RAM/queues alone are insufficient: no consumer progress must fail. */
    trace_n=0;assert(mf_ws_audio_load(read_exact,progress_event));
    memset(ram+0x700,0,128);
    for(i=0;i<=120;i++){commands=0;mf_ws_audio_step(1000+i,0);}
    assert(mf_ws_audio_ready()==-1 && diagnostic.stage==MF_WS_AUDIO_DRIVER_READY);
    /* A changing cursor with an unconsumed request must still fail. */
    trace_n=0;assert(mf_ws_audio_load(read_exact,progress_event));
    for(i=0;i<=120;i++){word(0x41a,(sound_word(0x41a)&0x7f0)+16);commands=0;mf_ws_audio_step(2000+i,0);}
    assert(mf_ws_audio_ready()==-1 && diagnostic.stage==MF_WS_AUDIO_DRIVER_READY);
    puts("PASS real loader readiness: consumed commands despite timer alias0, valid MAP/SEQ/TON uploads and full control preparation; dead/stuck consumers still rejected");
}
