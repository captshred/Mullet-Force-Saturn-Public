#!/usr/bin/env python3
"""Pinned request-gate evidence and before/after cold/reload regressions.

This is production SH-2 C with a byte-audited model of the 68000 request gate,
not Saturn/SCSP emulation. No third-party Python dependencies required.
"""
from pathlib import Path
import importlib.util,subprocess,tempfile,hashlib,io,tarfile
R=Path(__file__).resolve().parents[1]
BASE='0827a42ac863102102ea9dd693109f1483384bdb'
spec=importlib.util.spec_from_file_location('sdk',R/'tools/audit-level2-audio-sdk.py')
sdk=importlib.util.module_from_spec(spec);spec.loader.exec_module(sdk)
root=R/'.deps/joengine/Compiler/COMMON/SGL_302j'
b=(root/'INC/SDDRVS.TSK').read_bytes()
assert hashlib.sha256(b).hexdigest()=='68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6'
assert b[0x10da:0x10e2].hex()=='103804e06a00003e' # MOVE.B flag,D0; BPL skip queue.
assert b[0x1118:0x111e].hex()=='0238007f04e0' # Driver clears notification after scan.
assert b[0x1842:0x1856].hex()=='223c4e714e71103804e16b0841faf88a20c120c1'
# 1848 reads config; BMI retains gate, otherwise two longs become NOPs.
sgl=sdk.section(subprocess.check_output(['ar','p',str(root/'LIB_ELF/LIBSGL.A'),'sglG00.o']),'SLPROG')
assert sgl[0x98:0xc2].hex()=='d34ae0008031b023e406b02f6473e080803177c0e00c80707710e0008072e0088070e0808030b0216473'
snd=sdk.section(subprocess.check_output(['ar','p',str(root/'LIB_ELF/LIBSND.A'),'snd_main.o']),'.text')
assert snd[0x510:0x51e].hex()=='d10a6212910c2211e300a0042832' # StopDsp publishes word 0c00, no flag write.
print('PASS pinned bytes: SGL uses request bit7; driver may retain gate, clears bit7 after scanning; SND_StopDsp publishes queue word without notification',flush=True)
# Prove that clearing CONFIG (4e1) after boot cannot rewrite a retained gate.
for config in (0,0x80):
 gate=bytearray(b[0x10da:0x10e2])
 if not config&0x80:gate[:]=bytes.fromhex('4e714e714e714e71')
 config=0
 for host,expected in [(0,gate[:2]==bytes.fromhex('4e71')),(0x80,True)]:
  dispatch=gate[:2]==bytes.fromhex('4e71') or bool(host&0x80)
  assert dispatch==expected
print('PASS startup mode model: clearing 4e1 later leaves an already retained request gate; queued commands need a fresh 4e0 notification',flush=True)
s=(R/'tests/e008_startup_test.c').read_text()
s=s.replace('#include "../src/wingsuit_audio.c"','#include MF_E108_SOURCE')
# Model the REAL gate, including notification cleared after a scan, instead of
# the older tests' independent always-closed boolean gate.
s=s.replace('void slSndFlush(void){}','void slSndFlush(void){ram[0x4e0]=0;} /* earlier wake consumed before later SND submission */')
s=s.replace('&& !failflag && !gated)', '&& !failflag && (!gated || (ram[0x4e0]&0x80)))')
s=s.replace('n>=due[i])consume(i);}', 'n>=due[i])consume(i);ram[0x4e0]&=0x7f;}')
s=s.replace('int main(void){','int historical_cases(void){')
s+='''
int main(void){unsigned trial,ok=0;int r;gated=1;
 for(trial=0;trial<512;trial++){
  eager=0;ack_delay=trial%4;skipmap=failflag=injectfull=0;
  r=run(trial%12,trial%3,1,trial+1,0);
#if EXPECT_FIX
  assert(r==1);assert(mf_ws_startup_capture.notifications>0);
#else
  assert(r==-1 && diagnostic.expected==0 && diagnostic.actual==12 && boot==BOOT_CPU);
#endif
  ok++;r=run(trial%7,0,1,trial+1,1);
#if EXPECT_FIX
  assert(r==1);
#else
  assert(r==-1 && diagnostic.actual==12);
#endif
 }
 /* Driver absent/busy forever and map-ack failure must still fail closed. */
 failflag=1;assert(run(0,0,1,1,0)==-1 && diagnostic.actual==12);failflag=0;
 skipmap=1;assert(run(0,0,1,1,0)==-1);skipmap=0;
 eager=1;gated=0;ack_delay=0;assert(run(0,0,1,1,0)==1);
 printf("PASS request-gate production C: fixed=%d, %u cold and %u warm audio reloads; absent-driver/map failures retained; synchronous ack retained\\n",EXPECT_FIX,ok,ok);
 return 0;}
'''
with tempfile.TemporaryDirectory(prefix='e108-request-') as d:
 ref=Path(d)/'base';ref.mkdir()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 test=Path(d)/'test.c';test.write_text(s)
 for fixed,source in [(0,ref/'src/wingsuit_audio.c'),(1,R/'src/wingsuit_audio.c')]:
  exe=Path(d)/('test'+str(fixed))
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',
                  '-DEXPECT_FIX='+str(fixed),'-DMF_E108_SOURCE="'+str(source)+'"',
                  '-I'+str(R/'tests/wingsuit_audio_mock'),'-I'+str(R/'tests/sound_mock'),'-I'+str(source.parent),str(test),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],cwd=R,check=True)
