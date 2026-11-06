/* Actual simulation/transport with SDK commands and SCSP RAM mocked. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
static unsigned char ram[524288];
static unsigned short slot_regs[32*16];
#define MF_WS_SLOT_REGS slot_regs
#define MF_WS_SOUND_BASE ram
#include "../src/wingsuit_audio.c"
#include "../src/wingsuit.c"
char sddrvstsk[MF_SOUND_DRIVER_BYTES];
static int stopped=1,inflight,reads,frees,accept=1,initializations,commands;
static unsigned clock_now;
static int starts[8],stops[8],notes[2],offs[2],bank[8],program[8],live[8];
static const char *fail_name;
static unsigned fail_stage,trace[32],trace_n;
static int init_status=1,driver_frozen,command_frozen;
static unsigned one_until[8],note_stamp;
static int defer_note;
static int attack_live[2],loop_live[2],loop_notes[2],attack_offs[2],loop_offs[2];
static int submit(unsigned cmd)
{
    unsigned i;for(i=0;i<8;i++)if(!ram[0x700+i*16]){ram[0x700+i*16]=cmd;return 0;}
    return 1;
}
static void progress_event(const mf_ws_audio_diagnostic *d){assert(trace_n<32);trace[trace_n++]=d->stage;assert(!d->has_status);}
char *jo_fs_read_file(const char *n,int *size){(void)n;(void)size;assert(0);return NULL;}
static char *read_exact(const char *name,int expected)
{
    char path[128],*b;FILE *f;int n;
    reads++;if(fail_name && !strcmp(fail_name,name))return NULL;
    snprintf(path,sizeof(path),"assets/wingsuit/%s",name);f=fopen(path,"rb");assert(f);
    fseek(f,0,SEEK_END);n=(int)ftell(f);rewind(f);assert(n==expected);
    b=malloc(n);assert(b && fread(b,1,n,f)==(size_t)n);fclose(f);return b;
}
void jo_free(void *p){assert(!inflight);frees++;free(p);}
void slSoundOffWait(void){stopped=1;}
void slSoundOnWait(void){assert(stopped && !ram[0x4e1] && diagnostic.stage==MF_WS_AUDIO_CPU_RESTART);stopped=0;}
void slDMACopy(void *s,void *d,unsigned n){assert(stopped && !inflight && (unsigned char *)d>=ram && (unsigned char *)d+n<=ram+sizeof(ram));memcpy(d,s,n);inflight=1;}
void slDMAWait(void){inflight=0;}
void slSndFlush(void){assert(diagnostic.stage==MF_WS_AUDIO_FLUSH && !ready && !stopped);}
void slInitSound(Uint8 *p,unsigned s,Uint8 *m,unsigned n){assert(stopped && p==(Uint8 *)sddrvstsk && s==MF_SOUND_DRIVER_BYTES && m && n==MF_WS_MAP_BYTES);inflight=1;ram[0x4e1]=0x80;memcpy(ram+0xa000,m,n);memset(ram+0x700,0,128);ram[0x8838]=ram[0x8839]=0;commands=0;memset(attack_live,0,sizeof(attack_live));memset(loop_live,0,sizeof(loop_live));memset(live,0,sizeof(live));memset(bank,0,sizeof(bank));memset(program,0,sizeof(program));memset(ram+0x8000,0,0x800);ram[0x67ec]=ram[0x67ed]=0;note_stamp=0;}
void SND_Init(SndIniDt *p){assert(stopped && p->program==(Uint16 *)sddrvstsk && p->program_size==MF_SOUND_DRIVER_BYTES && p->map_size==20); /* Pinned binary doubles words; not an invented byte mock. */
    {unsigned char snapshot[44];memcpy(snapshot,p->map,sizeof(snapshot));assert(!snapshot[40] && !snapshot[41] && !snapshot[42] && !snapshot[43]);}
    assert(diagnostic.stage==MF_WS_AUDIO_SND_INIT);memset(ram+0x700,0,128);initializations++;}
int SND_ChgMap(int n){assert(!n && (diagnostic.stage==MF_WS_AUDIO_MAP_CHANGE || diagnostic.stage==MF_WS_AUDIO_MAP_READY));return fail_stage==MF_WS_AUDIO_MAP_CHANGE?init_status:submit(8);}
int SND_StopDsp(void){assert(diagnostic.stage==MF_WS_AUDIO_DSP_STOP && !stopped);return fail_stage==MF_WS_AUDIO_DSP_STOP?init_status:submit(12);}
int SND_SetCdDaLev(int l,int r){assert(!l && !r && diagnostic.stage==MF_WS_AUDIO_CDDA_LEVEL);return fail_stage==MF_WS_AUDIO_CDDA_LEVEL?init_status:submit(128);}
int SND_SetTlVl(int v){assert(v==15 && diagnostic.stage==MF_WS_AUDIO_TOTAL_VOLUME);return fail_stage==MF_WS_AUDIO_TOTAL_VOLUME?init_status:submit(130);}
static void word(unsigned a,unsigned value){ram[a]=value>>8;ram[a+1]=value;}
static void driver_note(unsigned p,unsigned note,int alive)
{
    unsigned loop=p<2 && note==MF_WS_FLAME_LOOP_NOTE,slot=p<2?p*2+loop:p+2,a=0x8000+slot*64;
    unsigned pcm=p<2?(loop?MF_WS_FLAME_LOOP_PCM_ADDR:MF_WS_FLAME_ATTACK_PCM_ADDR):p<4?180832:149152;
    unsigned layer=p<2?(loop?MF_WS_FLAME_LOOP_LAYER_ADDR:MF_WS_FLAME_ATTACK_LAYER_ADDR):p<4?149046:149010;
    unsigned short *r=slot_regs+slot*16;
    word(a+2,(p<<8)|note);word(a+6,p<<9);word(a+8,layer>>16);word(a+10,layer&65535);
    word(a+0x3a,alive?0x0a:8);if(alive){word(a+0x3e,++note_stamp);word(0x67ec,note_stamp);}
    r[0]=0x0800|(loop<<5)|(pcm>>16);r[1]=pcm&65535;r[2]=0;r[3]=loop?MF_WS_FLAME_LOOP_FRAMES:MF_WS_FLAME_ATTACK_FRAMES;
}
static void driver_flame(unsigned p,int alive){driver_note(p,loop_live[p]?MF_WS_FLAME_LOOP_NOTE:MF_WS_FLAME_ATTACK_NOTE,alive);}
static int accepted(void){if(!accept)return 0;assert(++commands<=8);assert(!submit(9));return 1;}
int SND_SetSeqVl(int p,int v,int f){assert(!stopped && p>=0 && p<8 && v==(p<2?MF_WS_FLAME_VOLUME:p<4?MF_WS_SHOT_VOLUME:MF_SFX_VOLUME) && !f);return accepted()?0:1;}
int SND_StartSeq(int p,int b,int song,int pr){(void)p;(void)b;(void)song;(void)pr;assert(!"No Level 2 sequence starts");return 1;}
int SND_StopSeq(int p){(void)p;assert(!"No Level 2 sequence stops");return 1;}
int SND_CtrlDirMidi(int p,int pr,int cmd,int channel,int a,int b)
{
    assert(p>=0 && p<8 && !pr && channel==p);
    if(!accepted())return 1;
    if(cmd==3){assert(a==32 && !b);bank[p]=1;}
    else if(cmd==4){assert((p<2?(a==MF_WS_FLAME_ATTACK_PROGRAM || a==MF_WS_FLAME_LOOP_PROGRAM):a==(p<4?1:0)) && !b && bank[p]);program[p]=a;}
    else if(cmd==1){assert(startup_done && b==110 && bank[p]);
        if(p>=2){assert(a==60 && !live[p] && program[p]==(p<4?1:0));starts[p]++;one_until[p]=clock_now+(p<4?31:44);}
        else if(a==MF_WS_FLAME_ATTACK_NOTE){assert(program[p]==MF_WS_FLAME_ATTACK_PROGRAM && !attack_live[p] && !loop_live[p]);attack_live[p]=1;notes[p]++;}
        else {assert(a==MF_WS_FLAME_LOOP_NOTE && program[p]==MF_WS_FLAME_LOOP_PROGRAM && !loop_live[p]);loop_live[p]=1;loop_notes[p]++;}
        live[p]=1;if(defer_note && p==2)word(0x8000+4*64+0x3a,0xa);else driver_note(p,a,1);}
    else {assert(p<2 && cmd==0 && !b && live[p]);
        if(a==MF_WS_FLAME_LOOP_NOTE){assert(loop_live[p]);loop_live[p]=0;loop_offs[p]++;offs[p]++;}
        else {assert(a==MF_WS_FLAME_ATTACK_NOTE && attack_live[p]);attack_live[p]=0;attack_offs[p]++;if(!loop_live[p])offs[p]++;}
        live[p]=attack_live[p]||loop_live[p];driver_note(p,a,0);}
    return 0;
}
int slSoundRequest(const char *format,...){(void)format;assert(!"SGL command path must not be used by the repair");return 0x25a00700;}
void SND_GetSeqStat(SndSeqStat *s,int p){(void)s;(void)p;assert(!"No sequence-status runtime dependency");}
static void pump(unsigned now,unsigned focus)
{
    unsigned i;clock_now=now;commands=0;
    if(!stopped && !driver_frozen){
        word(0x8838,sound_word(0x8838)+1);
        for(i=0;i<8;i++){
            if(command_frozen)continue;
            if(ram[0x700+i*16]==8)memcpy(ram+0x500,ram+0xa000,40);
            ram[0x700+i*16]=0;
        }
    }
    for(i=2;i<8;i++)if(live[i] && (int)(now-one_until[i])>=0){live[i]=0;driver_note(i,60,0);}
    mf_ws_audio_step(now,focus);
}
static void load(unsigned now)
{
    fail_name=NULL;accept=1;trace_n=0;assert(mf_ws_audio_load(read_exact,progress_event));
    assert(diagnostic.completed==0xfff && !strcmp(diagnostic.operation,"TOTAL VOLUME"));
    assert(trace_n==12);{unsigned j;for(j=0;j<12;j++)assert(trace[j]==j+1);}
    assert(!mf_ws_audio_ready());
    {unsigned j;for(j=0;j<32;j++)pump(now-32+j,0);}
    pump(now,0);pump(now+1,0);pump(now+2,0);assert(mf_ws_audio_ready()==1 && diagnostic.completed==0x7fff && flame[0].prep==3 && flame[1].prep==3);
}
static void reset_counts(void){memset(starts,0,sizeof(starts));memset(stops,0,sizeof(stops));memset(notes,0,sizeof(notes));memset(offs,0,sizeof(offs));memset(loop_notes,0,sizeof(loop_notes));memset(attack_offs,0,sizeof(attack_offs));memset(loop_offs,0,sizeof(loop_offs));}
static void sim(mf_wingsuit *g,unsigned a,unsigned b,unsigned press)
{
    unsigned held[2]={a,b},edge[2]={press,0},focus=0;int i;
    mf_ws_step(g,held,edge,3);mf_ws_audio_events(g->deaths,g->shots_fired);
    if(!g->paused)for(i=0;i<2;i++)if(mf_ws_beam_active(g,i))focus|=1u<<i;
    pump(clock_now+1,focus);
}
int main(void)
{
    int i,n,r;mf_wingsuit g;const char *names[]={"WDEATH.MAP","WDEATH.SEQ","WDEATH.TON"};
    memset(ram,0x55,sizeof(ram));load(0);assert(reads==3 && frees==3 && initializations==1 && !stopped);
    assert(ram[MF_WS_TON_ADDR+MF_WS_TON_BYTES]==0x55);
    for(i=0;i<2;i++){
        const char *name=i?"WDEATH.TON":"WDEATH.SEQ";int size=i?MF_WS_TON_BYTES:MF_WS_SEQ_BYTES;
        char *b=read_exact(name,size);assert(!memcmp(b,ram+(i?MF_WS_TON_ADDR:MF_WS_SEQ_ADDR),size));jo_free(b);
    }
    r=reads;reset_counts();mf_ws_init(&g,1);g.spawn=10000;
    g.players[0].invulnerable=g.players[1].invulnerable=10000; /* Isolate sustained transport from new ground fire. */
    sim(&g,MF_A,0,0);assert(g.shots_fired==1 && starts[2]==1 && !notes[0]);
    for(i=2;i<=19;i++){sim(&g,MF_A,0,0);assert(!notes[0]);}
    sim(&g,MF_A,0,0);assert(g.players[0].shot_hold==20 && notes[0]==1 && live[0]);
    for(i=0;i<1000;i++)sim(&g,MF_A,0,0);
    assert(notes[0]==1 && live[0]);
    for(i=0;i<20;i++){sim(&g,MF_A,MF_A,0);if(i<19)assert(!notes[1]);}
    assert(notes[0]==1 && notes[1]==1 && live[0] && live[1]);
    sim(&g,0,MF_A,0);assert(!live[0] && live[1] && offs[0]==1 && !offs[1]);
    sim(&g,0,MF_A,MF_START);assert(g.paused && !live[1] && offs[1]==1);
    for(i=0;i<10;i++)sim(&g,0,MF_A,0);
    sim(&g,0,MF_A,MF_START);assert(!g.paused && notes[1]==2 && live[1]);
    g.players[1].invulnerable=0;g.hostile[0]=(mf_ws_hostile_shot){1,g.players[1].x,g.players[1].y-768,0,60,0,768};
    sim(&g,0,MF_A,0);assert(g.players[1].respawn && !live[1] && offs[1]==2);
    n=starts[4]+starts[5]+starts[6]+starts[7];assert(n==1);
    for(i=0;i<20;i++)sim(&g,0,MF_A,0);
    assert(starts[4]+starts[5]+starts[6]+starts[7]==n && !live[1]);assert(reads==r);
    load(1700);reset_counts();mf_ws_init(&g,1);g.spawn=10000;
    g.players[0].shot_hold=19;g.enemies[0]=(mf_ws_enemy){1,130*256,100*256,0,0,0,0,0,0,0};
    sim(&g,MF_A,0,0);assert(g.deaths==1 && starts[4]==1);
    for(i=0;i<20;i++)sim(&g,MF_A,0,0);
    assert(starts[4]+starts[5]+starts[6]+starts[7]==1 && notes[0]==1);
    load(1800);reset_counts();mf_ws_init(&g,1);g.spawn=10000;
    for(i=0;i<32;i++)g.shots[i]=(mf_ws_shot){1,160*256,100*256,1,90,0};
    sim(&g,MF_A,0,0);assert(!g.shots_fired && !starts[2] && !starts[3]);
    g.shots[5].active=0;g.players[0].shot_hold=0;
    sim(&g,MF_A,0,0);assert(g.shots_fired==1 && starts[2]==1);
    assert(g.shots[5].x==g.players[0].x && !g.shots[5].vx);
    load(2000);reset_counts();mf_ws_audio_events(1,2);pump(2003,1);
    assert(live[0] && live[2] && live[4] && notes[0]==1);
    mf_ws_audio_events(1,0);pump(2004,3);assert(live[0] && live[1] && live[4] && live[5] && notes[0]==1 && notes[1]==1);
    load(2100);reset_counts();mf_ws_audio_events(1,3);pump(2103,0);
    assert(live[2] && live[3] && live[4] && starts[2]==1 && starts[3]==1);
    mf_ws_audio_events(0,1);pump(2104,0);assert(!stops[2] && !stops[3] && live[2] && live[4]);
    pump(2104,0);assert(starts[2]==1);pump(2105,0);assert(starts[2]==1 && live[3] && live[4]);
    pump(2136,0);assert(starts[2]==1);pump(2137,0);assert(starts[2]==2 && !stops[2]);
    load(2200);reset_counts();mf_ws_audio_events(10,0);pump(2203,3);
    /* Direct MIDI: two Flame starts + four Explosion starts fit one batch. */
    assert(mixer.flame==2 && mixer.explosion==4 && mixer.total==6 && mixer.dropped_explosions==2);
    for(i=2204;i<=2303;i++)pump((unsigned)i,3);
    assert(starts[4]+starts[5]+starts[6]+starts[7]==8 && !pending_explosions);
    assert(notes[0]==1 && notes[1]==1 && !offs[0] && !offs[1]);
    load(3000);reset_counts();accept=0;mf_ws_audio_events(1,1);pump(3003,1);
    assert(!notes[0] && !starts[4] && !starts[2]);accept=1;pump(3004,1);assert(notes[0]==1 && starts[4]==1 && starts[2]==1);
    accept=0;pump(3005,0);assert(live[0]);accept=1;pump(3006,1);assert(!live[0] && offs[0]==1);
    pump(3007,1);assert(notes[0]==2);pump(3008,1);assert(!mf_ws_audio_fault());
    for(i=0;i<3;i++){
        fail_name=names[i];trace_n=0;assert(!mf_ws_audio_load(read_exact,progress_event));assert(!ready);
        n=starts[4];mf_ws_audio_events(1,3);pump(3100,3);assert(starts[4]==n);
    }
    fail_name=NULL;
    {static const unsigned failures[]={MF_WS_AUDIO_MAP_CHANGE,MF_WS_AUDIO_DSP_STOP,MF_WS_AUDIO_CDDA_LEVEL,MF_WS_AUDIO_TOTAL_VOLUME};unsigned k;
     for(init_status=1;init_status<=7;init_status+=6)for(k=0;k<4;k++){
        fail_stage=failures[k];trace_n=0;assert(!mf_ws_audio_load(read_exact,progress_event));
        assert(!ready && diagnostic.stage==fail_stage && diagnostic.has_status && diagnostic.expected==SND_RET_SET && diagnostic.actual==init_status);
        assert(!(diagnostic.completed&(1u<<(fail_stage-1))));
        assert(trace[trace_n-1]==fail_stage);
     }
    }
    fail_stage=0;
    load(4000);reset_counts();pump(4003,3);
    assert(mf_ws_audio_flame_diagnostics(0)->state==MF_WS_FLAME_REQUESTED);
    assert(mf_ws_audio_flame_diagnostics(1)->state==MF_WS_FLAME_REQUESTED);
    pump(4015,3);assert(mf_ws_audio_flame_diagnostics(0)->state==MF_WS_FLAME_ATTACK);
    pump(4042,3);pump(4054,3);assert(mf_ws_audio_flame_diagnostics(0)->state==MF_WS_FLAME_SUSTAIN);
    pump(4603,3);assert(notes[0]==1 && notes[1]==1);
    assert(mf_ws_audio_flame_diagnostics(0)->active_slots==2);
    assert(mf_ws_audio_flame_diagnostics(1)->active_slots==8);
    /* Simulate real driver EG becoming inactive, with note intent still on. */
    driver_flame(0,0);pump(4604,3);pump(4615,3);
    assert(mf_ws_audio_flame_diagnostics(0)->state==MF_WS_FLAME_REQUESTED);
    pump(4616,3);assert(mf_ws_audio_flame_diagnostics(0)->state==MF_WS_FLAME_STOPPED);
    assert(mf_ws_audio_flame_diagnostics(1)->state==MF_WS_FLAME_SUSTAIN);
    assert(notes[0]==1 && notes[1]==1); /* No speculative automatic retrigger. */
    driver_flame(0,1);slot_regs[16]&=~0x60;pump(4617,3);
    assert(mf_ws_audio_flame_diagnostics(0)->state==MF_WS_FLAME_MISMATCH);
    driver_flame(0,1);pump(4618,3);
    assert(mf_ws_audio_flame_diagnostics(0)->state==MF_WS_FLAME_SUSTAIN);
    pump(4619,2);assert(mf_ws_audio_flame_diagnostics(0)->state==MF_WS_FLAME_OFF);
    assert(mf_ws_audio_flame_diagnostics(1)->state==MF_WS_FLAME_SUSTAIN && !mf_ws_audio_flame_diagnostics(2));
    load(5000);reset_counts();pump(5003,3);
    assert(notes[0]==1 && notes[1]==1 && !loop_notes[0] && !loop_notes[1]);
    pump(5040,3);assert(!loop_notes[0] && !loop_notes[1]);
    pump(5041,3);assert(loop_notes[0]==1 && loop_notes[1]==1 && attack_live[0] && loop_live[0]);
    pump(5041,3);assert(loop_notes[0]==1 && loop_notes[1]==1); /* no catch-up duplicate */
    pump(5042,3);assert(!attack_live[0] && !attack_live[1] && attack_offs[0]==1 && attack_offs[1]==1);
    for(i=5043;i<5642;i++){mf_ws_audio_events(1,3);pump(i,3);}
    assert(notes[0]==1 && notes[1]==1 && loop_notes[0]==1 && loop_notes[1]==1 && !loop_offs[0] && !loop_offs[1]);
    pump(5642,2);assert(loop_offs[0]==1 && loop_live[1] && !loop_offs[1]);
    pump(5643,3);assert(notes[0]==2 && notes[1]==1);
    load(5700);reset_counts();pump(5703,1);pump(5740,1);
    accept=0;pump(5741,1);assert(!loop_notes[0] && notes[0]==1);
    accept=1;pump(5742,1);assert(loop_notes[0]==1 && notes[0]==1);
    pump(5743,0);assert(!live[0] && loop_offs[0]==1);
    load(5800);reset_counts();pump(5803,1);pump(5840,1);pump(5841,0);
    assert(notes[0]==1 && !loop_notes[0] && !live[0]); /* release wins at handoff */
    /* Startup observes real driver progress and actual consumption, not time. */
    trace_n=0;assert(mf_ws_audio_load(read_exact,progress_event));reset_counts();driver_frozen=1;
    for(i=0;i<5;i++)pump(5900+i,0);
    assert(!mf_ws_audio_ready() && !ready && !notes[0] && !starts[2]);driver_frozen=0;
    for(i=5905;i<5950 && !mf_ws_audio_ready();i++)pump(i,0);
    assert(mf_ws_audio_ready()==1 && i<5950);mf_ws_audio_events(1,1);pump(i,1);
    assert(notes[0]==1 && starts[2]==1 && starts[4]==1); /* first valid use */
    /* A running heartbeat cannot stand in for a consumed map command. */
    trace_n=0;assert(mf_ws_audio_load(read_exact,progress_event));pump(5960,0);pump(5961,0);
    assert(boot==BOOT_MAP_ACK);command_frozen=1;pump(6079,0);assert(!mf_ws_audio_ready());pump(6080,0);
    assert(mf_ws_audio_ready()==-1 && !strcmp(diagnostic.operation,"MAP ACK") && diagnostic.expected==0 && diagnostic.actual==8);
    command_frozen=0;
    /* A consumer that does not run cannot silently enable gameplay. */
    driver_frozen=1;trace_n=0;assert(mf_ws_audio_load(read_exact,progress_event));
    pump(6000,0);pump(6119,0);assert(!mf_ws_audio_ready());pump(6120,0);
    assert(mf_ws_audio_ready()==-1 && !strcmp(diagnostic.operation,"DRIVER READY"));
    driver_frozen=0;
    load(~0u-24);reset_counts();pump(~0u-20,1);pump(~0u-19,1);pump(16,1);
    assert(!loop_notes[0]);pump(17,1);assert(loop_notes[0]==1 && notes[0]==1);
    load(~0u-3);reset_counts();mf_ws_audio_events(1,0);pump(~0u,1);
    pump(0,1);assert(notes[0]==1 && starts[4]==1);pump(48,1);assert(notes[0]==1);
    mf_ws_audio_events(1,0);pump(49,1);assert(starts[4]==2);
    /* Ten seconds of mixed playback: both flames receive one Attack/Loop.
       Retiring finite Attack keys is allowed; no persistent Loop Note Off. */
    load(7000);reset_counts();pump(7003,3);
    for(i=7004;i<=7603;i++){
        if(i%12==0)mf_ws_audio_events(1,3);
        pump(i,3);
        assert(mixer.total<=10 && !mixer.losses && !mixer.replacements);
    }
    assert(notes[0]==1 && notes[1]==1 && loop_notes[0]==1 && loop_notes[1]==1);
    assert(attack_offs[0]==1 && attack_offs[1]==1 && !loop_offs[0] && !loop_offs[1]);
    for(i=2;i<8;i++)assert(starts[i]>0 && !stops[i]);
    /* Exactly ten principal physical voices during both handoffs. */
    load(8000);reset_counts();pump(8003,3);pump(8004,3);mf_ws_audio_events(4,3);pump(8041,3);
    assert(mixer.flame==4 && mixer.shot==2 && mixer.explosion==4 && mixer.total==10);
    for(i=0;i<10;i++)assert(mixer.owner[i]==(unsigned)(i<4?i/2:i-2));
    for(i=8042;i<8072;i++)pump(i,3);
    assert(live[2] && live[3] && live[4] && !mixer.losses);
    pump(8072,3);assert(!live[2] && live[4]); /* LEA, no Note Off. */
    pump(8085,3);assert(!live[4] && !mixer.losses);
    /* Read-only diagnostics capture premature inactivity after cache grace. */
    load(9000);reset_counts();mf_ws_audio_events(1,1);pump(9003,1);
    driver_note(4,60,0);pump(9004,1);pump(9016,1);
    assert(mixer.losses==1 && !mixer.replacements && mixer.lost_kind==MF_WS_SFX_EXPLOSION && mixer.lost_control==4);
    assert(mixer.lost_age==1 && mixer.free_at_loss==29 && mf_ws_audio_fault());
    /* A different owner in a previously live physical slot is replacement
       evidence; record the concurrent Note On mask without repairing/restarting. */
    load(10000);reset_counts();pump(10003,1);
    word(0x8006,4<<9);mf_ws_audio_events(1,0);pump(10004,1);
    assert(mixer.losses==1 && mixer.replacements==1 && mixer.lost_control==0 && mixer.other_note_on==(1u<<4));
    assert(notes[0]==1 && !offs[0]);
    /* Asynchronous Note On acceptance with stale EG from the previous
       naturally ended note must not produce a false replacement alarm. */
    load(11000);reset_counts();mf_ws_audio_events(0,1);pump(11003,0);
    assert(watch[4].seen);mf_ws_audio_events(0,1);defer_note=1;pump(11037,0);
    assert(!watch[4].seen && !mixer.losses);defer_note=0;driver_note(2,60,1);pump(11038,0);
    assert(watch[4].seen && !mixer.losses && starts[2]==2);
    puts("PASS direct-MIDI one-shots: 4 independent explosions, 2 shots, preserved gains/programs/channels, natural LEA, bounded overflow without stealing, rejection retries, 600-VBlank mixed hold, maximum 10 physical cached-live slots; fault-only ownership/loss diagnostics");
    puts("PASS split Flame and E108: exact handoff, independent release/pause/death, no Loop restarts/offs during mixes, loader DMA once, readiness/consumer watchdog and clock-wrap regressions");
}
