#!/usr/bin/env python3
"""Actual recovered transport with SDK/RAM mocks, UBSan and readiness mutations."""
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
s=(R/'tests/wingsuit_audio_test.c').read_text()
s=s.replace('"../src/wingsuit_audio.c"','"'+str(R/'src/wingsuit_audio.c')+'"').replace('"../src/wingsuit.c"','"'+str(R/'src/wingsuit.c')+'"')
s=s.replace('word(0x8838,sound_word(0x8838)+1);','word(0x8838,0);')
s=s.replace('static unsigned clock_now;','static int reject_shot_on;static unsigned clock_now,attack_n,attack_tick[20000],attack_port[20000];')
s=s.replace('    if(!accepted())return 1;','    if(p>=2 && p<4 && cmd==1 && reject_shot_on){--reject_shot_on;return 1;}\n    if(!accepted())return 1;')
s=s.replace('starts[p]++;','assert(attack_n<20000);attack_tick[attack_n]=clock_now;attack_port[attack_n++]=p;starts[p]++;')
s=s.replace('MF_WS_MAP_BYTES','MF_WS_MUSIC_MAP_BYTES')
s=s.replace('map_size==20','map_size==32').replace('unsigned char snapshot[44]','unsigned char snapshot[68]').replace('!snapshot[40] && !snapshot[41] && !snapshot[42] && !snapshot[43]','!snapshot[64] && !snapshot[65] && !snapshot[66] && !snapshot[67]').replace('memcpy(ram+0x500,ram+0xa000,40)','memcpy(ram+0x500,ram+0xa000,64)')
s=s.replace('word(a+6,p<<9)','word(a+6,(p<2?1:p)<<9)')
s=s.replace('v==(p<2?MF_WS_FLAME_VOLUME:p<4?MF_WS_SHOT_VOLUME:MF_SFX_VOLUME)','v==(p==0?127:p==1?MF_WS_FLAME_VOLUME:p<4?MF_WS_SHOT_VOLUME:100)')
a=s.index('int SND_StartSeq(');b=s.index('int SND_StopSeq(',a)
s=s[:a]+'''static unsigned music_starts;
int SND_StartSeq(int p,int b,int song,int pr){assert(p==0 && b==1 && song==0 && pr==0);if(!accepted())return 1;music_starts++;return 0;}
'''+s[b:]
s=s.replace('assert(p>=0 && p<8 && !pr && channel==p);','assert(p>=1 && p<8 && !pr && channel==(p==1?channel:p));if(p==1){assert(channel<2);p=channel;}')
s=s.replace('    else {assert(p<2 && cmd==0 && !b && live[p]);','    else if(p>=2){assert(cmd==0 && a==60 && !b);if(p>=4)assert((int)(clock_now-one_until[p])>=0);stops[p]++;live[p]=0;driver_note(p,a,0);}\n    else {assert(cmd==0 && !b && live[p]);')
# Model a separate channel context for Hit even though its gain control is2.
s=s.replace('[8]','[9]').replace('for(i=2;i<8;i++)','for(i=2;i<9;i++)')
s=s.replace('channel==(p==1?channel:p)','(p==1?channel<2:(p==2?channel==2 || channel==8:channel==p))')
s=s.replace('if(p==1){assert(channel<2);p=channel;}','if(p==1){assert(channel<2);p=channel;}else if(channel==8)p=8;')
s=s.replace('assert(a==32 && !b);bank[p]=1;','assert(a==32 && b==(p==2 || p==3?2:0));bank[p]=b+1;')
s=s.replace('a==(p<4?1:0)','a==(p==8?1:0)').replace('program[p]==(p<4?1:0)','program[p]==(p==8?1:0)')
s=s.replace('word(a+6,(p<2?1:p)<<9)','word(a+6,(p<2?1:p==8?2:p)<<9)')
s=s.replace('if(p>=4)assert((int)(clock_now-one_until[p])>=0);','if(p>=4 && p<8)assert((int)(clock_now-one_until[p])>=0);')
s=s.replace('(p<4?31:44)','(p==8?31:p<4?27:44)')
s=s.replace('int main(void)','int legacy_main(void)')
s+='''
int main(void){
 unsigned t,p;load(1000);reset_counts();assert(!music_starts && startup_done);
 mf_ws_audio_events(0,0);pump(1003,3);assert(music_starts==1);
 for(t=1004;t<7003;t++){
  if(t%12==0)mf_ws_audio_events(2,3);
  pump(t,3);
  assert(!mixer.losses && !mixer.replacements && music_starts==1);
 }
 assert(notes[0]==1 && notes[1]==1 && loop_notes[0]==1 && loop_notes[1]==1);
 assert(!loop_offs[0] && !loop_offs[1]);
 for(p=2;p<8;p++)assert(starts[p]>10 && stops[p]>10);
 accept=0;pump(7100,3);for(p=2;p<8;p++)if(shot[0].state || explosion[0].state)break;
 accept=1;for(t=7101;t<7150;t++)pump(t,3);
 pump(7150,2);assert(loop_offs[0]==1 && !loop_offs[1] && loop_live[1]);
 pump(7151,3);assert(notes[0]==2 && notes[1]==1);
 puts("PASS recovered audio: control0 music/gain127, control1 independent Flame channels, original handoff/sustain/release, 6000-tick mix, all six one-shot controls retired, no global stop/reset");
 /* Readiness must also succeed when commands finish during submission. */
 consume_on_submit=1;load(8000);consume_on_submit=0;
 assert(startup_done && music_prep==1);
 /* A frozen consumer must fail the unchanged watchdog. */
 trace_n=0;assert(mf_ws_audio_load(read_exact,progress_event));driver_frozen=1;
 for(t=9000;t<=9120;t++)pump(t,0);
 assert(mf_ws_audio_ready()==-1 && !strcmp(diagnostic.operation,"DRIVER READY"));driver_frozen=0;
 /* Retry retirement without freeing or truncating any active PCM. */
 load(10000);mf_ws_audio_events(1,1);pump(10003,3);
 accept=0;pump(10060,3);assert(shot[0].state==PLAYING && explosion[0].state==PLAYING);
 accept=1;pump(10061,3);assert(shot[0].state==FREE && explosion[0].state==FREE);
 puts("PASS recovery readiness: synchronous command consumption, frozen-consumer E108 watchdog, rejected retirement retry");
 /* Spaced starts, overlapping tails, and bounded newest-event overflow. */
 load(90);reset_counts();attack_n=0;mf_ws_audio_events(3,0);
 for(t=100;t<=110;t++)pump(t,0);
 assert(attack_n==3 && attack_tick[0]==100 && attack_tick[1]==105 && attack_tick[2]==110);
 assert(live[4] && live[5] && live[6] && !stops[4] && !stops[5] && !stops[6]);
 load(90);reset_counts();attack_n=0;mf_ws_audio_events(1,0);pump(100,0);mf_ws_audio_events(1,0);pump(106,0);
 assert(attack_n==2 && attack_tick[1]==106);
 load(11000);reset_counts();attack_n=0;mf_ws_audio_events(0,1);pump(11003,0);mf_ws_audio_events(0,1);pump(11004,0);
 mf_ws_audio_events(0,1);pump(11005,0);mf_ws_audio_events(0,1);pump(11006,0);
 assert(attack_n==4 && attack_port[0]==2 && attack_port[1]==3 && attack_port[2]==2 && attack_port[3]==3);
 /* A free younger Shot wins over stealing the older active Shot. */
 shot[1].until=11007;one_until[3]=11007;mf_ws_audio_events(0,1);pump(11007,0);assert(attack_port[4]==3 && stops[2]==1);
 /* Actual successful allocation count equals attacks; a full pool is silent. */
 {mf_wingsuit g;unsigned n=0;load(12000);reset_counts();mf_ws_init(&g,1);g.spawn=10000;
 for(t=0;t<300;t++){
  unsigned held[2]={t%2?0:MF_A,t%2?0:MF_A},edge[2]={0,0};
  if(t==100)for(p=0;p<MF_WS_SHOTS;p++)g.shots[p]=(mf_ws_shot){1,160*256,180*256,0,120,0};
  mf_ws_step(&g,held,edge,3);n+=!!(g.shots_fired&1)+!!(g.shots_fired&2);
  mf_ws_audio_events(g.deaths,g.shots_fired);pump(12003+t,0);
  assert((unsigned)(starts[2]+starts[3])==n && !pending_shots && !mixer.dropped_shots);
 }assert(n>20);}
 load(13000);reset_counts();attack_n=0;mf_ws_audio_events(100,0);
 assert(pending_explosions==8 && mixer.dropped_explosions==92);
 for(t=13003;t<13203;t++)pump(t,0);
 assert(attack_n==8 && !pending_explosions);
 for(p=1;p<attack_n;p++)assert(attack_tick[p]-attack_tick[p-1]>=5);
 /* Retirement remains after the 49 tick lease, never at a spacing deadline. */
 assert(stops[4]==2 && stops[5]==2 && stops[6]==2 && stops[7]==2);
 load(14000);reset_counts();attack_n=0;
 {unsigned before=music_starts,last=0;
 for(t=14003;t<14603;t++){
  mf_ws_audio_events(2,3);pump(t,3);assert(starts[2]+starts[3]==(int)(2*(t-14002)) && !mixer.losses);
 }
 assert(music_starts==before+1 && notes[0]==1 && notes[1]==1 && loop_notes[0]==1 && loop_notes[1]==1 && !loop_offs[0] && !loop_offs[1]);
 for(p=0;p<attack_n;p++)if(attack_port[p]>=4){if(last)assert(attack_tick[p]-last>=5);last=attack_tick[p];}
 }
 load(~0u-12);reset_counts();attack_n=0;mf_ws_audio_events(3,0);
 pump(~0u-2,0);pump(1,0);assert(attack_n==1);pump(2,0);pump(7,0);assert(attack_n==3);
 load(15000);reset_counts();mf_ws_audio_events(0,3);pump(15003,0);
 reject_shot_on=1;mf_ws_audio_events(0,1);pump(15004,0);
 assert(shot[0].state==RESTARTING && pending_shots==1 && stops[2]==1);
 pump(15005,0);assert(shot[0].state==PLAYING && !pending_shots && stops[2]==1 && starts[2]==2);
 /* Hit follows actual surviving projectile damage, never Flame/death/miss. */
 {mf_wingsuit g;unsigned hold[2]={0,0},edge[2]={0,0};int j;
 mf_ws_init(&g,1);g.spawn=10000;g.scroll=300;step_turrets(&g);
 for(j=0;j<4;j++){
  mf_ws_turret *a=&g.turrets[0];g.shots[0]=(mf_ws_shot){1,a->x,a->y+7*256,0,40,0};
  mf_ws_step(&g,hold,edge,3);assert(g.hits==(unsigned)(j<3) && g.deaths==(j==3));
 }
 mf_ws_step(&g,hold,edge,3);assert(!g.hits);
 g.shots[0]=(mf_ws_shot){1,g.turrets[0].x,g.turrets[0].y+7*256,0,40,0};
 mf_ws_step(&g,hold,edge,3);assert(!g.hits && !g.deaths);
 mf_ws_init(&g,1);g.spawn=10000;g.scroll=300;g.shots[0]=(mf_ws_shot){1,16*256,200*256,0,40,0};
 mf_ws_step(&g,hold,edge,3);assert(!g.hits && !g.deaths && g.shots[0].active);
 }
 load(16000);reset_counts();attack_n=0;
 {unsigned music_before=music_starts;
 for(t=16003;t<16603;t++){
  mf_ws_audio_events(2,3);mf_ws_audio_hits(1);pump(t,3);
  assert(starts[2]+starts[3]==(int)(2*(t-16002)) && !mixer.losses);
 }
 assert(starts[8]>500 && stops[8]>500 && notes[0]==1 && notes[1]==1 && loop_notes[0]==1 && loop_notes[1]==1 && !loop_offs[0] && !loop_offs[1] && music_starts==music_before+1);
 }
 puts("PASS Fire/Hit: bank2 new Fire on controls2/3; old Shot bank0/program1 on control2/channel8; surviving projectile damage only; lethal/miss/dead silence; mixed isolation and fresh Hit retriggers");
 puts("PASS SFX timing: allocation/attack equality, free-first/oldest rotation, 100/105/110 and 100/106, overlapping tails, eight-event drop-newest bound, retirement, dual-Flame/music/Shot stress and clock wrap");
 return 0;
}
'''
source=(R/'src/wingsuit_audio.c').read_text()
mutants=[('fixed',source),
 ('timer-alias',source.replace('boot_counter=sound_word(0x41a);','boot_counter=sound_word(0x8838);').replace('if(sound_word(0x41a)==boot_counter','if(sound_word(0x8838)==boot_counter')),
 ('late-snapshot',source.replace('    boot_counter=sound_word(0x41a);','').replace('    boot=BOOT_CPU;return 1;','    boot_counter=sound_word(0x41a);boot=BOOT_CPU;return 1;'))]
import resource
def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with tempfile.TemporaryDirectory() as d:
 for name,transport in mutants:
  audio=Path(d)/'transport.c';audio.write_text(transport)
  test=Path(d)/'audio.c';test.write_text(s.replace(str(R/'src/wingsuit_audio.c'),str(audio)));exe=Path(d)/'test'
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(R/'tests/wingsuit_audio_mock'),'-I'+str(R/'tests/sound_mock'),'-I'+str(R/'src'),str(test),'-o',str(exe)],check=True)
  result=subprocess.run([str(exe)],cwd=R,text=True,capture_output=True,preexec_fn=no_core)
  if name=='fixed':
   assert result.returncode==0,(result.stdout,result.stderr)
   print(result.stdout,end='')
  else:
   assert result.returncode!=0 and 'Assertion' in result.stderr,(name,result.stdout,result.stderr)
   print('PASS recovered readiness mutation rejected:',name)
