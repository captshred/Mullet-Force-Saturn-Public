#!/usr/bin/env python3
"""Actual recovered transport with SDK/RAM mocks, UBSan and readiness mutations."""
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
s=(R/'tests/wingsuit_audio_test.c').read_text()
s=s.replace('"../src/wingsuit_audio.c"','"'+str(R/'src/wingsuit_audio.c')+'"').replace('"../src/wingsuit.c"','"'+str(R/'src/wingsuit.c')+'"')
s=s.replace('word(0x8838,sound_word(0x8838)+1);','word(0x8838,0);')
s=s.replace('MF_WS_MAP_BYTES','MF_WS_MUSIC_MAP_BYTES')
s=s.replace('map_size==20','map_size==28').replace('unsigned char snapshot[44]','unsigned char snapshot[60]').replace('!snapshot[40] && !snapshot[41] && !snapshot[42] && !snapshot[43]','!snapshot[56] && !snapshot[57] && !snapshot[58] && !snapshot[59]').replace('memcpy(ram+0x500,ram+0xa000,40)','memcpy(ram+0x500,ram+0xa000,56)')
s=s.replace('word(a+6,p<<9)','word(a+6,(p<2?1:p)<<9)')
s=s.replace('v==(p<2?MF_WS_FLAME_VOLUME:p<4?MF_WS_SHOT_VOLUME:MF_SFX_VOLUME)','v==(p==0?127:p==1?MF_WS_FLAME_VOLUME:p<4?MF_WS_SHOT_VOLUME:100)')
a=s.index('int SND_StartSeq(');b=s.index('int SND_StopSeq(',a)
s=s[:a]+'''static unsigned music_starts;
int SND_StartSeq(int p,int b,int song,int pr){assert(p==0 && b==1 && song==0 && pr==0);if(!accepted())return 1;music_starts++;return 0;}
'''+s[b:]
s=s.replace('assert(p>=0 && p<8 && !pr && channel==p);','assert(p>=1 && p<8 && !pr && channel==(p==1?channel:p));if(p==1){assert(channel<2);p=channel;}')
s=s.replace('    else {assert(p<2 && cmd==0 && !b && live[p]);','    else if(p>=2){assert(cmd==0 && a==60 && !b);stops[p]++;live[p]=0;driver_note(p,a,0);}\n    else {assert(cmd==0 && !b && live[p]);')
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
