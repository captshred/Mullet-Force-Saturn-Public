"""Import supplied combat WAVs; no synthetic substitutions or resampling."""
from pathlib import Path
import wave,struct,hashlib,math
FILES=[('Jab_1.wav',.35),('CONNECT_1.wav',.45),('bat woosh_1.wav',.38)]

def load(root,mix_gain):
    waves=[];report=[]
    for name,target in FILES:
        path=Path(root)/name
        with wave.open(str(path),'rb') as w:
            channels,width,rate,n=w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()
            assert width==2 and rate==44100 and channels in (1,2)
            raw=struct.unpack('<'+str(n*channels)+'h',w.readframes(n))
        values=[sum(raw[i*channels:(i+1)*channels])/channels/32768 for i in range(n)]
        peak=max(map(abs,values));threshold=max(1/32768,peak*.0001)
        active=[i for i,v in enumerate(values) if abs(v)>=threshold];assert active
        start=max(0,active[0]-16);end=min(n,active[-1]+97)
        v=values[start:end]
        for i in range(len(v)):v[i]*=min(1,i/16,(len(v)-1-i)/96)
        gain=target/(max(map(abs,v))*.9*mix_gain)
        result=[x*gain for x in v]
        assert max(map(abs,result))*.9<1, 'Pre-mix PCM must not clip'
        assert len(result)<=65535 and result[0]==result[-1]==0
        waves.append(result)
        report.append(dict(file=name,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_channels=channels,source_frames=n,sample_rate=rate,trim_start=start,trim_end_exclusive=end,frames=len(v),duration_seconds=len(v)/rate,mono='arithmetic mean, no resampling',edge_fade_frames=[16,96],source_mono_peak=peak,gain_before_ton=gain,target_final_peak_fraction=target))
    return waves,report
