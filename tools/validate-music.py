#!/usr/bin/env python3
"""Source/SEQ event equivalence, TON pointers/envelopes, MAP and memory checks."""
from pathlib import Path
import json,struct,hashlib
import midi,seq
ROOT=Path(__file__).resolve().parents[1]; out=ROOT/'assets/cd'
r=json.loads((ROOT/'assets/music/report.json').read_text()); cfg=json.loads((ROOT/'assets/music/config.json').read_text())
assert hashlib.sha256((ROOT/cfg['source']).read_bytes()).hexdigest()==r['source_sha256']
_,pp,tracks=midi.read(ROOT/cfg['source']); events=midi.merged(tracks); expected,*_=midi.notes(events)
expected=[(a,b,c,n,v) if c+1!=cfg['drum_channel'] else (a,b,cfg['drums'][str(n)]['channel']-1,60,v) for a,b,c,n,v in expected]
s=seq.decode((out/'STAGE.SEQ').read_bytes())
assert sorted(s['notes'])==expected and s['ppqn']==pp
assert s['loops']==[0,r['duration_ticks']] and s['end']==r['duration_ticks']
assert s['tempo_loop_offset']==8
source_tempos=midi.tempo_map(events); decoded_tempos=[]; clock=0
for duration,us in s['tempos']: decoded_tempos.append((clock,us)); clock+=duration
assert decoded_tempos==source_tempos and clock==r['duration_ticks']
expected_bends=[(e['tick'],e['status']&15,min(127,((e['data'][1]<<7|e['data'][0])+64)//128)) for e in events if e['status']&240==224]
# Source bends are preserved in order; explicit reset bends additionally appear
# once at time zero and once at the loop boundary on each melodic channel.
actual=list(s['bends'])
used_melodic={e['status']&15 for e in events if e['status']<240 and (e['status']&15)+1!=cfg['drum_channel']}
for c in sorted(used_melodic):
    actual.remove((0,c,64));actual.remove((r['duration_ticks'],c,64))
assert sorted(actual)==sorted(expected_bends)
assert len(expected)==r['notes']
for ch in sorted(used_melodic):
    route=cfg['channels'][str(ch+1)]
    pcs=[(t,p) for t,c,p in s['programs'] if c==ch]
    expected_pcs=[(e['tick'],route['programs'][str(e['data'][0])]) for e in events if e['status']==192+ch]
    assert pcs==expected_pcs,(ch,pcs)
    assert (r['duration_ticks'],ch,120,0) in s['controls']
# TON voices reference in-bank PCM and have finite releases, direct dry output.
for name,voice_count,bend in [('STAGE.TON',len(cfg['instruments']),cfg['bend_semitones']),('FX.TON',8,0)]:
    data=(out/name).read_bytes(); first=struct.unpack_from('>H',data)[0];assert (first-8)//2==voice_count
    assert data[first:first+18]==bytes(18)
    for i in range(voice_count):
        v=struct.unpack_from('>H',data,8+2*i)[0]
        assert data[v]==bend and data[v+2]==0
        l=v+4; sa=((data[l+3]&15)<<16)|struct.unpack_from('>H',data,l+4)[0]
        lsa,lea=struct.unpack_from('>HH',data,l+6)
        assert sa+2*lea<=len(data) and 0<=lsa<lea<=65535
        assert data[l+13]&31==31 and data[l+23]==0
        assert (data[l+3]&0x60)==(0x20 if (name=='STAGE.TON' and cfg['instruments'][i].get('loop',True)) or (name=='FX.TON' and i==4) else 0)
for i in range(3):
    fx=seq.decode((out/'FX.SEQ').read_bytes(),i)
    assert not fx['loops'] and fx['end']==240
    assert fx['notes']==[(0,240,0,60,110)] and fx['programs']==[(0,0,i)]
ignition=seq.decode((out/'FX.SEQ').read_bytes(),3);hiss=seq.decode((out/'FX.SEQ').read_bytes(),4)
assert ignition['notes']==[(0,96,0,60,110)] and not ignition['loops']
assert hiss['notes']==[(0,240,0,60,110)] and hiss['loops']==[0,240] and hiss['tempo_loop_offset']==8
assert r['physical_voice_bound']==r['release_peak']+6+4<=32
assert r['sfx_ports']==6 and r['torch_audio']['shared_hiss_bus']
assert 0<cfg['torch_audio']['hiss_gain']<cfg['torch_audio']['ignition_gain']<1
regions=r['sound_ram_regions']
for a,b in zip(regions,regions[1:]): assert a['end']<=b['start']
assert regions[-1]['end']<=524288
custom=(out/'CUSTOM.MAP').read_bytes(); assert custom[-8:]==bytes([255])*8
for p in range(0,len(custom)-8,8):
    entry=custom[p:p+8]; address=int.from_bytes(entry[1:4],'big'); size=int.from_bytes(entry[5:8],'big')
    assert any(x['start']==address and x['size']==size for x in regions)
for n,v in r['outputs'].items():
    payload=(out/n).read_bytes(); assert len(payload)==v['bytes'] and hashlib.sha256(payload).hexdigest()==v['sha256']
assert r['release_peak']<=cfg['music_voice_budget']<=24
mix=r['linear_mix']; settings=cfg['linear_mix']
assert mix['music_pcm']['multiplier']==settings['music_gain']*settings['master_headroom']
assert mix['sfx_pcm']['multiplier']==settings['sfx_gain']*settings['master_headroom']
assert mix['pcm_gain_ratio_before_instrument_boost']==settings['music_gain']/settings['sfx_gain']
assert abs(r['latest_relative_sfx_gain']-0.85)<1e-9
assert r['sfx_retrigger_ticks']==cfg['sfx_retrigger_ticks']
for i,v in enumerate(r['music_instrument_boost']):
    assert v['tl_after']>=0 and v['peak_after']<32768
    layer=struct.unpack_from('>H',(out/'STAGE.TON').read_bytes(),8+2*i)[0]+4
    assert (out/'STAGE.TON').read_bytes()[layer+15]==v['tl_after']
    if i<3: assert abs(v['actual_boost_db']-6)<1e-9
assert cfg['music_priority']>cfg['sfx_priority']
for group in ['music_pcm','sfx_pcm']:
    assert mix[group]['hard_clipped_samples']==0 and mix[group]['peak_after']<32768
assert r['percussion']['total_note_ons']==0 and r['percussion']['channel_zero_based']==9
assert all(not t['drum_note_on_counts'] and not t['drum_note_off_counts'] for t in r['percussion']['tracks'])
print('PASS: percussion raw-channel trace has zero events; linear mix gains and unclipped PCM validated.')
# Check the existing SDK's compiled DAT and TSK driver representations agree.
import re
sdk=ROOT/'.deps/joengine/Compiler/COMMON/SGL_302j/INC'
driver=bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})', (sdk/'SDDRVS.DAT').read_text()))
assert driver[:-1]==(sdk/'SDDRVS.TSK').read_bytes() and driver[-1]==255 # DAT has one trailing sentinel byte
print(f'PASS: all {len(expected)} note times/gates/velocities + {len(expected_bends)} rounded bends match source; tempo/duration/loop exact.')
print('PASS: 8 music/drum voices, 7 one-shot + 1 shared loop tone voices, dry TON pointers and sound-RAM map validated.')
print(f'PASS: {r["release_peak"]} conservatively budgeted music slots + 6 fixed SFX ports; sound RAM high water {r["sound_ram_high_water"]}/524288.')

for i,gate in enumerate(r['custom_gates']):
    sound=seq.decode((out/'FX.SEQ').read_bytes(),5+i)
    assert sound['notes']==[(0,gate,0,60,110)] and not sound['loops']
    assert sound['programs']==[(0,0,5+i)] and sound['end']==gate
    data=(out/'FX.TON').read_bytes();l=struct.unpack_from('>H',data,8+2*(5+i))[0]+4
    sa=((data[l+3]&15)<<16)|struct.unpack_from('>H',data,l+4)[0]
    frames=struct.unpack_from('>H',data,l+8)[0]
    values=struct.unpack_from('>'+str(frames)+'h',data,sa)
    assert values[0]==values[-1]==0 and max(map(abs,values))<32767
    assert frames==r['custom_combat'][i]['frames'] and gate/960>frames/44100
print('PASS: supplied custom combat samples, complete one-shot gates, silent sample boundaries and 32-slot bound.')
