"""Strict SMF reader/format-0 writer used by the reproducible music pipeline.
Metadata is data only. No embedded text, SysEx or other MIDI data is executed.
"""
import struct
from pathlib import Path
from collections import Counter,defaultdict,deque

def vlq(data,pos):
    n=0
    for _ in range(4):
        if pos>=len(data): raise ValueError('Truncated MIDI VLQ')
        b=data[pos]; pos+=1; n=(n<<7)|(b&127)
        if b<128: return n,pos
    raise ValueError('Invalid MIDI VLQ')
def put_vlq(n):
    assert 0<=n<0x10000000
    out=[n&127]; n>>=7
    while n: out.insert(0,(n&127)|128); n>>=7
    return bytes(out)
def read(path):
    data=Path(path).read_bytes()
    assert data[:4]==b'MThd'
    length,fmt,count,ppqn=struct.unpack_from('>IHHH',data,4)
    assert fmt in (0,1) and length>=6 and count and 0<ppqn<32768
    pos=8+length; tracks=[]
    for tr in range(count):
        assert data[pos:pos+4]==b'MTrk'
        size=struct.unpack_from('>I',data,pos+4)[0]; pos+=8
        buf=data[pos:pos+size]; assert len(buf)==size; pos+=size
        p=0; clock=0; running=0; events=[]
        while p<len(buf):
            dt,p=vlq(buf,p); clock+=dt; b=buf[p]
            if b>=128: status=b; p+=1
            else: status=running; assert 128<=status<240
            event={'tick':clock,'track':tr,'order':len(events),'status':status}
            if status==255:
                kind=buf[p]; p+=1; size,p=vlq(buf,p); payload=buf[p:p+size]; p+=size
                assert len(payload)==size
                event.update(meta=kind,data=payload); running=0
            elif status in (240,247):
                size,p=vlq(buf,p); event['data']=buf[p:p+size]; p+=size; running=0
            else:
                assert 128<=status<240
                size=1 if status&240 in (192,208) else 2
                event['data']=buf[p:p+size]; p+=size
                assert len(event['data'])==size and all(x<128 for x in event['data'])
                running=status
            events.append(event)
        assert p==len(buf); tracks.append(events)
    assert pos==len(data)
    return fmt,ppqn,tracks

def merged(tracks):
    return sorted((e for t in tracks for e in t),key=lambda e:(e['tick'],e['track'],e['order']))
def notes(events):
    active=defaultdict(deque); result=[]; overlap=0; stray=0
    for e in events:
        s=e['status']; d=e['data']; c=s&15
        if s&240==144 and d[1]:
            overlap+=bool(active[c,d[0]]); active[c,d[0]].append(e)
        elif s&240==128 or s&240==144 and not d[1]:
            if not active[c,d[0]]: stray+=1; continue
            on=active[c,d[0]].popleft()
            result.append((on['tick'],e['tick'],c,on['data'][0],on['data'][1]))
    return sorted(result),overlap,stray,sum(len(v) for v in active.values())
def tempo_map(events):
    tempos={0:500000}
    for e in events:
        if e.get('meta')==81:
            assert len(e['data'])==3; tempos[e['tick']]=int.from_bytes(e['data'],'big')
    return sorted(tempos.items())
def seconds(tick,ppqn,tempos):
    total=0
    for i,(t,us) in enumerate(tempos):
        end=min(tick,tempos[i+1][0] if i+1<len(tempos) else tick)
        if end>t: total+=(end-t)*us/(ppqn*1000000)
        if end==tick: break
    return total

def inspect(path):
    fmt,ppqn,tracks=read(path); events=merged(tracks); ns,overlap,stray,unclosed=notes(events)
    ts=tempo_map(events); end=max(e['tick'] for e in events)
    counters=[]; names={128:'note_off',144:'note_on',160:'poly_pressure',176:'cc',192:'program',208:'pressure',224:'bend'}
    for i,track in enumerate(tracks):
        channels=sorted({(e['status']&15)+1 for e in track if e['status']<240})
        counters.append({'index':i,'name':next((e['data'].decode('latin1') for e in track if e.get('meta')==3),''),
            'channels':channels,'end_tick':track[-1]['tick'],
            'programs':sorted({e['data'][0] for e in track if e['status']&240==192}),
            'events':dict(Counter(names.get(e['status']&240,'meta' if e['status']==255 else 'sysex') for e in track)),
            'bend_range': [min([((e['data'][1]<<7)|e['data'][0])-8192 for e in track if e['status']&240==224],default=0),max([((e['data'][1]<<7)|e['data'][0])-8192 for e in track if e['status']&240==224],default=0)]})
    bounds=[]; release_bounds=[]
    for a,b,c,n,v in ns:
        bounds += [(a,1),(b,-1)]
        release_bounds += [(seconds(a,ppqn,ts),1),(seconds(b,ppqn,ts)+.1,-1)]
    def peak(bounds):
        live=0; high=0
        for _,d in sorted(bounds): live+=d; high=max(live,high)
        return high
    return {'format':fmt,'ppqn':ppqn,'duration_ticks':end,'duration_seconds':seconds(end,ppqn,ts),
        'tracks':counters,'tempos':[{'tick':t,'microseconds_per_beat':us,'bpm':60000000/us} for t,us in ts],
        'time_signatures':[{'tick':e['tick'],'numerator':e['data'][0],'denominator':2**e['data'][1]} for e in events if e.get('meta')==88],
        'notes':len(ns),'max_simultaneous_notes':peak(bounds),'peak_with_100ms_release':peak(release_bounds),
        'same_key_overlaps':overlap,'unmatched_offs':stray,'unclosed_notes':unclosed,
        'controllers':{str((c+1,cc)):sorted({e['data'][1] for e in events if e['status']==176+c and e['data'][0]==cc}) for c,cc in sorted({(e['status']&15,e['data'][0]) for e in events if e['status']&240==176})},
        'drum_notes':sorted({n for a,b,c,n,v in ns if c==9})}

def write_format0(path,ppqn,events,end):
    out=bytearray(); prev=0
    for tick,payload in events:
        assert tick>=prev; out+=put_vlq(tick-prev)+payload; prev=tick
    out+=put_vlq(end-prev)+b'\xff\x2f\x00'
    Path(path).write_bytes(b'MThd'+struct.pack('>IHHH',6,0,1,ppqn)+b'MTrk'+struct.pack('>I',len(out))+out)
