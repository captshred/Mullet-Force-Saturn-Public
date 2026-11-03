#!/usr/bin/env python3
"""MIDI normalization + original PCM bank + pinned mid2seq converter pipeline.
No full-song audio rendering; TON samples are individual instruments only.
"""
from pathlib import Path
import sys,struct,json,math,random,subprocess,hashlib
import midi
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'third_party/mid2seq'))
import saturn_kit as kit
OUT=ROOT/'assets/cd'

def normalize(source,dest,cfg):
    fmt,ppqn,tracks=midi.read(source); events=midi.merged(tracks)
    # This score puts its first chord before tick-zero program/RPN setup.
    # Resolve same-tick initialization before note-ons, without moving any tick.
    events.sort(key=lambda e:(e['tick'],2 if e['status']&240==144 and e['data'][1] else 0 if e['status']&240==128 else 1))
    ns,overlap,stray,unclosed=midi.notes(events)
    if overlap or stray or unclosed: raise ValueError('Unpaired or overlapping same-key notes; fix source/mapping, never truncate silently')
    if any(b<=a for a,b,*_ in ns): raise ValueError('Zero/negative gate unsupported')
    end=max(e['tick'] for e in events); output=[]; rpn={}; unsupported=[]
    used=set(); source_programs={}
    def add(t,*b): output.append((t,bytes(b)))
    tempos=midi.tempo_map(events)
    assert len(tempos)<=255, "Too many tempo segments for the pinned converter"
    for t,us in tempos: output.append((t,b'\xff\x51\x03'+us.to_bytes(3,'big')))
    melodic_used={e['status']&15 for e in events if e['status']<240 and (e['status']&15)+1!=cfg['drum_channel']}
    for ch,route in cfg['channels'].items():
        c=int(ch)-1
        if c not in melodic_used: continue
        add(0,176+c,7,route['volume']); add(0,176+c,10,route['pan']); add(0,176+c,11,127); add(0,224+c,0,64)
    for e in events:
        t=e['tick']; s=e['status']; typ=s&240; c=s&15; d=e['data']
        if s>=240:
            if s!=255: unsupported.append({'tick':t,'type':'SysEx omitted'})
            continue # tempo/meter/names handled as data; SEQ has no meter notation
        if c+1==cfg['drum_channel']:
            if typ in (128,144):
                route=cfg['drums'].get(str(d[0])); assert route,('Unmapped drum',d[0])
                out=route['channel']-1; used.add(out)
                if typ==144 and d[1]:
                    add(t,192+out,route['voice']); add(t,144+out,60,d[1])
                else: add(t,128+out,60,0)
            elif typ!=192: unsupported.append({'tick':t,'type':'drum controller omitted','status':s,'data':list(d)})
            continue
        route=cfg['channels'].get(str(c+1))
        if route is None: raise ValueError(('Unmapped melodic channel',c+1))
        used.add(c)
        if typ==192:
            voice=route['programs'].get(str(d[0])); assert voice is not None,('Unmapped program',c+1,d[0])
            source_programs[c]=d[0]; add(t,s,voice)
        elif typ==176:
            cc,val=d
            if cc in (101,100): rpn[c,cc]=val
            elif cc in (6,38) and rpn.get((c,101))==0 and rpn.get((c,100))==0:
                expected=cfg['bend_semitones'] if cc==6 else 0
                assert val==expected,('Unsupported bend-range change',t,c+1,val)
            elif cc in (7,10,11,64,120,121,123):
                if cc==64 and val>=64: raise ValueError('Sustain needs gate baking; source must be pre-baked')
                add(t,s,*d)
            else: unsupported.append({'tick':t,'type':'CC omitted','channel':c+1,'controller':cc,'value':val})
        elif typ in (128,144,224):
            if typ in (128,144) and c not in source_programs: raise ValueError('Explicit initial program required')
            add(t,s,*d)
        else: unsupported.append({'tick':t,'type':'pressure omitted','status':s})
    # Reset every used channel at exact source end. Native loop includes these
    # cleanup events and all initial bank/program/volume/bend setup on each pass.
    for c in sorted(used):
        add(end,176+c,123,0); add(end,176+c,120,0); add(end,224+c,0,64)
    output.sort(key=lambda x:x[0]) # stable merge preserves program/CC before notes
    midi.write_format0(dest,ppqn,output,end)
    _,_,tt=midi.read(dest); _,ov,st,uc=midi.notes(midi.merged(tt))
    assert not(ov or st or uc), 'Drum routes create same-key overlap; assign a distinct route'
    return unsupported

def waveform(kind,n):
    result=[]
    for i in range(n):
        p=2*math.pi*i/n
        if kind=='crunch': v=math.tanh(2.7*(math.sin(p)+.4*math.sin(2*p)+.22*math.sin(3*p)+.1*math.sin(5*p)))
        elif kind=='lead': v=.65*math.sin(p)+.24*math.sin(2*p)+.18*math.sin(3*p)+.09*math.sin(5*p)
        else: v=.85*math.sin(p)+.28*math.sin(2*p)+.12*math.sin(3*p)
        result.append(v*.75)
    return result

def drum(kind,rate):
    duration={'kick':.11,'snare':.14,'closed':.04,'open':.16,'cymbal':.32}[kind]
    n=int(rate*duration); rng=random.Random(739+list(['kick','snare','closed','open','cymbal']).index(kind)); phase=0; result=[]; prev=0
    for i in range(n):
        t=i/rate; noise=rng.uniform(-1,1)
        if kind=='kick':
            phase+=2*math.pi*(48+100*math.exp(-t*45))/rate
            value=math.sin(phase)*math.exp(-t*34)+noise*.15*math.exp(-t*280)
        elif kind=='snare': value=(noise*.65+math.sin(2*math.pi*175*t)*.3)*math.exp(-t*30)
        else:
            metal=sum(math.sin(2*math.pi*f*t) for f in [3931,5077,6181,8293])/4
            value=((noise-prev)*.3+metal*.5)*math.exp(-t*({'closed':85,'open':24,'cymbal':13}[kind]))
        prev=noise
        result.append(value*.75*min(1,i/12)*min(1,(n-1-i)/64))
    return result

def register():
    kit.SAMPLE_RATE=44100 # Match TON unity-pitch clock; upstream defaults to 22050.
    for kind in ['crunch','lead','bass']: kit.WAVEFORM_GENERATORS['mf_'+kind]=lambda n,k=kind:waveform(k,n)
    for kind in ['kick','snare','closed','open','cymbal']: kit.WAVEFORM_GENERATORS['mf_'+kind]=lambda rate,k=kind:drum(k,rate)

def patch_ton(data,bend=6):
    data=bytearray(data); first=struct.unpack_from('>H',data)[0]; voices=(first-8)//2
    mixer=first; data[mixer:mixer+18]=bytes(18) # dry mix only; no DSP output
    for i in range(voices):
        v=struct.unpack_from('>H',data,8+2*i)[0]; data[v]=bend
        assert data[v+2]==0 # one PCM slot per note, never two-op FM
        data[v+4+0x17]=0 # disable DSP sends
    return bytes(data)

def apply_linear_gain(data,gain):
    """Scale sample payload only; leave TON addressing, tuning and gates intact."""
    data=bytearray(data); count=(struct.unpack_from('>H',data)[0]-8)//2
    pcm_start=max(struct.unpack_from('>H',data,8+2*i)[0]+36 for i in range(count))
    peak_before=peak_after=0
    for offset in range(pcm_start,len(data),2):
        value=struct.unpack_from('>h',data,offset)[0];scaled=round(value*gain)
        if not -32768<=scaled<=32767: raise ValueError('Mix clips PCM; lower shared master_headroom')
        peak_before=max(peak_before,abs(value));peak_after=max(peak_after,abs(scaled))
        struct.pack_into('>h',data,offset,scaled)
    return bytes(data),{'multiplier':gain,'peak_before':peak_before,'peak_after':peak_after,'hard_clipped_samples':0}

def boost_music_bank(data,db):
    """SCSP TL is attenuation in 0.375 dB steps, zero is loudest.
    Use available TL before PCM gain; never wrap/clamp at TL=0 or saturate PCM.
    Preserve envelope, velocity, pan and channel/expression/sequence dynamics.
    """
    assert 0<=db<=24, 'Music attenuation boost outside supported tuning range'
    data=bytearray(data);count=(struct.unpack_from('>H',data)[0]-8)//2;report=[]
    for i in range(count):
        layer=struct.unpack_from('>H',data,8+2*i)[0]+4
        old=data[layer+15];steps=min(old,int(db/.375));data[layer+15]=old-steps
        sa=((data[layer+3]&15)<<16)|struct.unpack_from('>H',data,layer+4)[0]
        n=struct.unpack_from('>H',data,layer+8)[0]
        values=struct.unpack_from('>'+str(n)+'h',data,sa)
        gain=10**((db-steps*.375)/20)
        safe=all(-32768<=round(v*gain)<=32767 for v in values)
        if not safe:gain=1.0 # Explicitly report a smaller boost, never clip.
        if gain!=1:
            for j,v in enumerate(values):struct.pack_into('>h',data,sa+j*2,round(v*gain))
        report.append(dict(voice=i,tl_before=old,tl_after=old-steps,pcm_multiplier=gain,
                           actual_boost_db=steps*.375+20*math.log10(gain),residual_pcm_boost_safe=safe,
                           peak_after=max(abs(round(v*gain)) for v in values)))
    return bytes(data),report

def inspect_percussion(tracks,drum_channel):
    details=[]; counts={}; raw_channel=drum_channel-1
    for index,track in enumerate(tracks):
        ons={};offs={}; channels=sorted({e['status']&15 for e in track if e['status']<240})
        for e in track:
            if (e['status']&15)!=raw_channel or e['status']>=240: continue
            typ=e['status']&240;d=e['data']
            if typ==144 and d[1]: ons[str(d[0])]=ons.get(str(d[0]),0)+1
            elif typ==128 or typ==144: offs[str(d[0])]=offs.get(str(d[0]),0)+1
        for note,n in ons.items(): counts[note]=counts.get(note,0)+n
        details.append({'track':index,'channels_zero_based':channels,'drum_note_on_counts':ons,'drum_note_off_counts':offs})
    return {'channel_human':drum_channel,'channel_zero_based':raw_channel,'note_on_counts':counts,'total_note_ons':sum(counts.values()),'tracks':details,
            'diagnosis':'No source percussion events; no replacement part generated' if not counts else 'Source percussion mapped independently by note'}

def fx_sequence():
    # Original three one-shots unchanged; ignition=3 and shared hiss loop=4.
    songs=[]
    for i in range(5):
        gate=96 if i==3 else 240
        stream=(bytes([0x82,0]) if i==4 else b'')
        stream+=bytes([0xb0,32,0,0,0xc0,i,0,0,60,110,gate,0,0xb0,123,0,gate])
        if i==4:stream+=bytes([0x82,0])
        stream+=bytes([0x83])
        song=struct.pack('>HHHHII',480,1,16,8 if i==4 else 0,gate,500000)+stream
        songs.append(song+bytes((-len(song))%4))
    ptr=(2+4*len(songs)+3)&~3;out=bytearray(struct.pack('>H',len(songs)))
    for song in songs:out+=struct.pack('>I',ptr);ptr+=len(song)
    out+=bytes((-len(out))%4)
    return bytes(out)+b''.join(songs)

def torch_wave(kind,rate,gain):
    n=int(rate*(.08 if kind=='ignite' else .06));rng=random.Random(1597 if kind=='ignite' else 927)
    data=[];previous=0
    for i in range(n):
        t=i/rate;noise=rng.uniform(-1,1)
        if kind=='ignite':v=(noise*.45+math.sin(2*math.pi*130*t)*.25)*(1-i/n)**2
        else:v=(noise-previous)*.22
        previous=noise;edge=min(1,i/64,(n-1-i)/64)
        data.append(v*gain*max(0,edge))
    return data

def build():
    cfg=json.loads((ROOT/'assets/music/config.json').read_text()); register(); OUT.mkdir(exist_ok=True)
    work=ROOT/'build/music'; work.mkdir(parents=True,exist_ok=True)
    source=ROOT/cfg['source']; report=midi.inspect(source)
    (ROOT/'assets/music/midi-report.json').write_text(json.dumps(report,indent=2)+'\n')
    unsupported=normalize(source,work/'normalized.mid',cfg)
    cc=['cc','-std=c99','-O2','-Wall','-Wextra','third_party/mid2seq/mid2seq.c','-o',str(work/'mid2seq')]
    subprocess.run(cc,cwd=ROOT,check=True)
    subprocess.run([str(work/'mid2seq'),str(work/'normalized.mid'),str(OUT/'STAGE.SEQ'),'--loop'],check=True)
    instruments=kit.load_config(str(ROOT/'assets/music/config.json'))
    assert all(i.rr==31 for i in instruments), 'Rebudget release tails before changing RR=31'
    mix=cfg['linear_mix']
    stage,stage_gain=apply_linear_gain(patch_ton(kit.build_ton(instruments),cfg['bend_semitones']),mix['music_gain']*mix['master_headroom'])
    stage,bank_boost=boost_music_bank(stage,mix['music_boost_db'])
    (OUT/'STAGE.TON').write_bytes(stage)
    effects=[]
    for i,name in enumerate(['PUNCH','JUMP','IMPACT']):
        raw=(OUT/(name+'.PCM')).read_bytes()
        values=[(b if b<128 else b-256)/128 for b in raw for _ in range(4)]
        kit.WAVEFORM_GENERATORS['fx_'+name]=lambda rate,v=values:v
        effects.append(kit.InstrumentDef(name,i,'fx_'+name,is_drum=True,drum_note=60,loop=False,rr=31,tl=0))
    for i,kind in [(3,'ignite'),(4,'hiss')]:
        gain=cfg['torch_audio']['ignition_gain' if i==3 else 'hiss_gain']
        kit.WAVEFORM_GENERATORS['torch_'+kind]=lambda rate,k=kind,g=gain:torch_wave(k,rate,g)
        effects.append(kit.InstrumentDef('torch '+kind,i,'torch_'+kind,is_drum=True,drum_note=60,loop=False,rr=31,tl=0))
    fx,fx_gain=apply_linear_gain(patch_ton(kit.build_ton(effects),0),mix['sfx_gain']*mix['master_headroom'])
    fx=bytearray(fx);hiss=struct.unpack_from('>H',fx,8+2*4)[0]+4;fx[hiss+3]|=0x20
    (OUT/'FX.TON').write_bytes(fx)
    (OUT/'FX.SEQ').write_bytes(fx_sequence())
    for name in ['STAGE.SEQ','STAGE.TON','FX.SEQ','FX.TON']:
        p=OUT/name; data=p.read_bytes(); p.write_bytes(data+bytes((-len(data))%4))
    def size(name): return (OUT/name).stat().st_size
    def entry(typ,bank,addr,amount): return bytes([typ<<4|bank])+addr.to_bytes(3,'big')+bytes([128])+amount.to_bytes(3,'big')
    # Preserve SGL's known boot/DSP/transfer reservations. All audible data are
    # our generated originals, not the commercial example's banks.
    fx_addr=0x246f0
    seq_addr=max(0x2cfdc,(fx_addr+size('FX.TON')+3)&~3)
    tone_addr=max(0x37040,(seq_addr+size('STAGE.SEQ')+3)&~3)
    regions=[('driver/work',0,0xb000),('transfer/work',0xb000,0x1000),('DSP reserved',0xc000,0x10040),('DSP program reserved',0x1c040,0x540),('PCM/work reserve',0x1c580,0x8000),('FX.SEQ',0x24580,size('FX.SEQ')),('FX.TON',fx_addr,size('FX.TON')),('STAGE.SEQ',seq_addr,size('STAGE.SEQ')),('STAGE.TON',tone_addr,size('STAGE.TON'))]
    assert size('FX.SEQ')<=fx_addr-0x24580
    custom=entry(3,0,0xc000,0x10040)+entry(2,0,0x1c040,0x540)
    for typ,bank,name,addr in [(1,0,'FX.SEQ',0x24580),(0,0,'FX.TON',0x246f0),(1,1,'STAGE.SEQ',seq_addr),(0,1,'STAGE.TON',tone_addr)]: custom+=entry(typ,bank,addr,size(name))
    custom+=bytes([255])*8; (OUT/'CUSTOM.MAP').write_bytes(custom)
    for a,b in zip(regions,regions[1:]): assert a[1]+a[2]<=b[1]
    assert regions[-1][1]+regions[-1][2]<=524288
    # Bound physical slots with a conservative 50ms release window (all RR=31).
    _,ppqn,tracks=midi.read(source); es=midi.merged(tracks); ns,*_=midi.notes(es); tempos=midi.tempo_map(es)
    percussion=inspect_percussion(tracks,cfg['drum_channel'])
    (ROOT/'assets/music/drum-diagnosis.json').write_text(json.dumps(percussion,indent=2)+'\n')
    bounds=[]
    for a,b,*_ in ns: bounds.extend([(midi.seconds(a,ppqn,tempos),1),(midi.seconds(b,ppqn,tempos)+cfg['release_budget_ms']/1000,-1)])
    live=peak=0
    for _,d in sorted(bounds): live+=d; peak=max(peak,live)
    assert peak<=cfg['music_voice_budget'],('Too many music voices',peak)
    assert peak+4+5<=32, 'Torch/SFX retirement guard exceeds physical SCSP slots'
    bend_errors=[abs(min(127,((e['data'][1]<<7|e['data'][0])+64)//128)*128-(e['data'][1]<<7|e['data'][0]))/8192*cfg['bend_semitones']*100 for e in es if e['status']&240==224]
    report.update(music_instrument_boost=bank_boost,sfx_retrigger_ticks=cfg["sfx_retrigger_ticks"],latest_relative_sfx_gain=mix["sfx_gain"]/mix["reference_sfx_gain"],linear_mix={"requested":mix,"music_pcm":stage_gain,"sfx_pcm":fx_gain,"pcm_gain_ratio_before_instrument_boost":mix["music_gain"]/mix["sfx_gain"]},percussion=percussion,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),max_bend_error_cents=max(bend_errors,default=0),substitutions=['GM programs replaced by original PCM instruments per config.json','Pitch bends rounded to native SEQ 7-bit precision','Note-off velocity is not represented by SEQ gate durations','Tick-zero program/RPN setup moved before simultaneous initial note-ons','Names, key and time signatures remain in source/report, not in playable SEQ'],unsupported=unsupported,release_peak=peak,music_voice_budget=cfg['music_voice_budget'],sfx_ports=4,torch_audio=cfg['torch_audio'],physical_voice_bound=peak+4+5,
        sound_ram_regions=[{'name':n,'start':a,'size':s,'end':a+s} for n,a,s in regions],
        sound_ram_high_water=regions[-1][1]+regions[-1][2],sound_ram_unallocated=524288-sum(s for n,a,s in regions),
        outputs={n:{'bytes':size(n),'sha256':hashlib.sha256((OUT/n).read_bytes()).hexdigest()} for n in ['STAGE.SEQ','STAGE.TON','FX.SEQ','FX.TON','CUSTOM.MAP']})
    (ROOT/'assets/music/report.json').write_text(json.dumps(report,indent=2)+'\n')
    header='#ifndef MF_MUSIC_DATA_H\n#define MF_MUSIC_DATA_H\n'
    header+=f'#define MF_MUSIC_VOLUME {cfg["music_volume"]}\n#define MF_SFX_VOLUME {cfg["sfx_volume"]}\n#define MF_MUSIC_PRIORITY {cfg["music_priority"]}\n#define MF_SFX_PRIORITY {cfg["sfx_priority"]}\n'
    header+='#define MF_SFX_RETRIGGER_TICKS {'+','.join(str(x) for x in cfg['sfx_retrigger_ticks'])+'}\n'
    driver=(ROOT/'.deps/joengine/Compiler/COMMON/SGL_302j/INC/SDDRVS.TSK').read_bytes()
    header+=f'#define MF_SOUND_DRIVER_BYTES {len(driver)}\n'
    for n in ['STAGE.SEQ','STAGE.TON','FX.SEQ','FX.TON','CUSTOM.MAP']: header+=f'#define MF_{n.replace(".","_")}_BYTES {size(n)}\n'
    for n,a,amount in regions:
        if n in ['STAGE.SEQ','STAGE.TON','FX.SEQ','FX.TON']: header+=f'#define MF_{n.replace(".","_")}_ADDR 0x{a:x}\n'
    (ROOT/'src/music_data.h').write_text(header+'#endif\n')
    print('Music:',report['notes'],'notes;',size('STAGE.SEQ'),'SEQ bytes;',size('STAGE.TON'),'TON bytes;',peak,'music slots with 50ms tails')
if __name__=='__main__': build()
