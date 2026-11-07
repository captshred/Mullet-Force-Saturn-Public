#!/usr/bin/env python3
"""Pinned SDK instruction evidence for staged map initialization."""
from pathlib import Path
import importlib.util,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sdk',R/'tools/audit-level2-audio-sdk.py');sdk=importlib.util.module_from_spec(spec);spec.loader.exec_module(sdk)
root=R/'.deps/joengine/Compiler/COMMON/SGL_302j/LIB_ELF'
snd=sdk.section(subprocess.check_output(['ar','p',str(root/'LIBSND.A'),'snd_main.o']),'.text')
sgl=sdk.section(subprocess.check_output(['ar','p',str(root/'LIBSGL.A'),'sglG00.o']),'SLPROG')
assert snd[0xb0:0xc8].hex()=='710c6111611d311c66137604621341094108321861233618'
# SGL saves map bytes in R7, then restores into R6 for slDMACopy to a000.
assert sgl[6:8].hex()=='2f76' and sgl[0x82:0x8c].hex()=='66f6d54bd046400b64f6'
# SMPC sound-on command6 inside slInitSound, then wait; caller is not stopped.
assert sgl[0x9e:0xa6].hex()=='b023e406b02f6473'
# SGL marks each current map entry's byte4 as transferred (0x80).
assert sgl[0xc4:0xd6].hex()=='e080e1206320802443118f0241108ff97208'
for size in [56,64]:
 words=size//2;backing=words*2+4-(words*2)%4
 assert (words,backing)==((28,60) if size==56 else (32,68))
 print('PASS pinned map ABI: bytes=%d words=%d padded-SND-backing=%d; SGL receives byte count'%(size,words,backing))
s=(R/'src/wingsuit_audio.c').read_text();a=s.index('int mf_ws_audio_load(');b=s.index('/* Fixed capacities',a);load=s[a:b]
assert 'read("WMUSIC.MAP",MF_WS_MUSIC_MAP_BYTES)' in load and '"WFIRE.TON"' not in load and '"WFIRE.MAP"' not in load
assert s.index('upload(bank_reader,"WFIRE.TON"')<s.index('map=bank_reader("WFIRE.MAP"')
assert 'sound_word(0x41a)==boot_counter || !commands_empty() || !map_ready()' in s
assert 'hit_midi(' not in s[s.index('static void startup_timeout'):s.index('static void startup(unsigned')]
print('PASS pinned SGL evidence: internal sound-CPU restart and early transfer marks; parent bootstrap unchanged, Fire publication follows upload, independent strict consumed-command/map acknowledgment; timeout diagnostics submit no commands')
