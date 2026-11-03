"""Read-only Yabause save-state trace decoding and native artwork matching."""
from pathlib import Path
import ctypes as C,json,re,hashlib
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1]
def fields(name):
    text=(R/'src/game.h').read_text()
    body=re.search(r'typedef struct\s*\{([^}]+)\}\s*'+name+r';',text).group(1)
    if name=='mf_game':body=body.split('mf_dash_state dash')[0] # Stable original trace prefix.
    return [(field.strip(),C.c_int32) for decl in re.findall(r'(?:int|unsigned)\s+([^;]+);',body) for field in decl.split(',')]
class Player(C.Structure):_fields_=fields('mf_player')
class Enemy(C.Structure):_fields_=fields('mf_enemy')
class Drum(C.Structure):_fields_=fields('mf_drum')
class Game(C.Structure):_fields_=[('players',Player*2),('enemies',Enemy*2),('drums',Drum*3)]+fields('mf_game')
class Record(C.Structure):_fields_=[('frame',C.c_uint32),('game',Game),('idle',C.c_uint32*2),('texture_hash',C.c_uint32)]
def trace(folder):
    data=(folder/'trace.bin').read_bytes();assert len(data)%C.sizeof(Record)==0
    records=[Record.from_buffer_copy(data[i:i+C.sizeof(Record)]) for i in range(0,len(data),C.sizeof(Record))]
    return {v.frame:v for v in records}
def pose(rec,actor,swagger=False,original_hold=0):
    p=rec.game.players[actor]
    if not p.active or not p.health or p.hurt or p.attack or p.height or p.vz or p.landing or p.torch:return -1
    if p.moving:
        if original_hold:return 15+(p.walk//original_hold)%3
        if swagger:
            text=(R/'src/swagger_timing.h').read_text();name='CHUCK' if actor else 'BUCK'
            h=list(map(int,re.search(r'MF_SWAGGER_'+name+r'_HOLDS\s+\{([^}]+)',text).group(1).split(',')))
            t=p.walk%sum(h)
            return 12 if t<h[0] else 13 if t<h[0]+h[1] else 14
        return 4+((p.walk%40)*3)//20
    t=rec.idle[actor]
    for f,hold in enumerate([[24,16,24,16],[30,18,24,18]][actor]):
        if t<hold:return f
        t-=hold
    raise AssertionError('Invalid idle clock')
def hardware(im):
    a=np.asarray(im).copy();v=a[:,:,:3].astype(np.uint16)
    v[:,:,0]=(v[:,:,0]//8)*255//31;v[:,:,1]=(v[:,:,1]//8)*2*255//63;v[:,:,2]=(v[:,:,2]//8)*255//31
    a[:,:,:3]=v.astype(np.uint8);return a

def validate(folder,control=None,swagger=False,original_hold=0,knee_lift=False):
    records=trace(folder);textures={r.texture_hash for r in records.values() if r.frame>=330}
    assert len(textures)==1,'VDP1 textures changed during gameplay'
    if control:
        comparison=trace(control)
        for frame,r in records.items():
            if frame>=330:assert bytes(r.game)==bytes(comparison[frame].game),f'Simulation differs from original renderer at {frame}'
    frames={(a,f,d):hardware(Image.open(R/f'assets/animation-polish/{n}-{f:02d}.png').convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT) if d<0 else Image.open(R/f'assets/animation-polish/{n}-{f:02d}.png').convert('RGBA'))
            for a,n in enumerate(['buck','chuck']) for f in range(10) for d in [-1,1]}
    if swagger:
        frames.update({(a,f+12,d):hardware(Image.open(R/f'assets/swagger-walk/{n}-{f:02d}.png').convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT) if d<0 else Image.open(R/f'assets/swagger-walk/{n}-{f:02d}.png').convert('RGBA'))
                       for a,n in enumerate(['buck','chuck']) for f in range(3) for d in [-1,1]})
    if original_hold:
        frames.update({(a,f+15,d):hardware(Image.open(R/f'assets/original-three-walk/{n}-{f:02d}.png').convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT) if d<0 else Image.open(R/f'assets/original-three-walk/{n}-{f:02d}.png').convert('RGBA'))
                       for a,n in enumerate(['buck','chuck']) for f in range(3) for d in [-1,1]})
    if knee_lift:
        assert original_hold==10
        frames.update({(a,15,d):hardware(Image.open(R/f'assets/knee-lift/{n}-00.png').convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT) if d<0 else Image.open(R/f'assets/knee-lift/{n}-00.png').convert('RGBA'))
                       for a,n in enumerate(['buck','chuck']) for d in [-1,1]})
    fallback_checks=[]
    checks=[];seen=[set(),set()];directions=[set(),set()];lags={};failures=[]
    for path in sorted(folder.glob('frame-*.ppm')):
        frame=int(path.stem.split('-')[1]);actual=np.asarray(Image.open(path).convert('RGB'))
        if frame<345:continue
        # SGL submits commands ahead of the displayed frame. Measure its fixed
        # pipeline lag, rather than moving/warping the reference to fit a pose.
        for actor in range(2):
            candidates=[]
            for lag in [-3]:
                rec=records.get(frame+lag)
                if rec is None:continue
                p=rec.game.players[actor];f=pose(rec,actor,swagger,original_hold)
                if f<0 or (p.invulnerable and p.invulnerable<112 and not rec.game.ticks&4):continue
                ref=frames[actor,f,1 if p.facing>0 else -1]
                left=p.x//256-rec.game.camera-64+1;top=p.y//256-92+1
                yy,xx=np.where(ref[:,:,3]>0);sx=xx+left;sy=yy+top
                keep=(sx>=0)&(sx<320)&(sy>=58)&(sy<221)
                # Exclude possible occluding original enemy/drum/other-player
                # bounding areas. Remaining pixels still span all three pieces.
                others=[]
                for j,op in enumerate(rec.game.players):
                    if j!=actor and op.active:
                        wide=112 if (op.attack or op.height or op.vz) else 64
                        others.append((op.x//256-rec.game.camera-wide,op.y//256-op.height//256-96,wide*2,100))
                for e in rec.game.enemies:
                    if e.state:others.append((e.x//256-rec.game.camera-70,e.y//256-96,140,98))
                for d in rec.game.drums:
                    if d.hp:others.append((d.x//256-rec.game.camera-18,d.y//256-48,36,50))
                if rec.game.paused or not rec.game.started:others.append((32,164,256,40))
                for x,y,w,h in others:keep&=~((sx>=x)&(sx<x+w)&(sy>=y)&(sy<y+h))
                sx,sy,xx,yy=sx[keep],sy[keep],xx[keep],yy[keep]
                if len(xx)<250:continue
                errors=int(np.any(actual[sy,sx]!=ref[yy,xx,:3],axis=1).sum())
                candidates.append((errors,-len(xx),lag,f,p.facing,left,top))
            if not candidates:continue
            best=min(candidates)
            if best[0]:failures.append((frame,actor,best));continue
            _,neg,lag,f,d,x,y=best;lags[lag]=lags.get(lag,0)+1;seen[actor].add(f);directions[actor].add(d)
            checks.append({'frame':frame,'actor':actor,'pose':f,'facing':d,'pipeline_lag':lag,'pixels':-neg,'mismatches':0})
    if control:
        for path in sorted(folder.glob('frame-*.ppm')):
            frame=int(path.stem.split('-')[1]);rec=records.get(frame-3)
            if rec is None or frame<345:continue
            other=control/path.name
            if not other.exists():continue
            actual=np.asarray(Image.open(path).convert('RGB'));original=np.asarray(Image.open(other).convert('RGB'))
            yy,xx=np.indices((240,320))
            for actor,p in enumerate(rec.game.players):
                if not p.active or pose(rec,actor,swagger,original_hold)>=0:continue
                x=p.x//256-rec.game.camera;y=p.y//256-p.height//256
                keep=(xx>=x-112)&(xx<x+112)&(yy>=max(58,y-96))&(yy<min(222,y+3))
                for j,op in enumerate(rec.game.players):
                    if j!=actor and pose(rec,j,swagger,original_hold)>=0:
                        ox=op.x//256-rec.game.camera;oy=op.y//256
                        keep&=~((xx>=ox-64)&(xx<ox+64)&(yy>=oy-92)&(yy<oy+4))
                count=int(keep.sum())
                if count<100:continue
                errors=int(np.any(actual[keep]!=original[keep],axis=1).sum())
                assert errors==0,('Original fallback differs',frame,actor,errors)
                kind='torch' if p.torch else 'bat' if p.bat and p.attack else 'kick' if p.height and p.attack else 'jump' if p.height or p.vz else 'hurt' if p.hurt else 'landing' if p.landing else 'punch' if p.attack else 'defeat'
                fallback_checks.append({'frame':frame,'actor':actor,'state':kind,'compared_pixels':count,'mismatches':0})
        assert {'torch','bat','kick','jump','hurt','landing','punch'}<={v['state'] for v in fallback_checks},{v['state'] for v in fallback_checks}
    # Long pauses and combat can hide/occlude a fighter; document them rather
    # than counting excluded pixels as successful comparisons.
    assert len(checks)>100,(len(checks),failures[:5])
    for a in range(2):assert (set(range(15,18)) if original_hold else set(range(12,15)) if swagger else set(range(4,10)))<=seen[a],(a,seen[a]);assert directions[a]=={-1,1}
    assert not failures,failures[:10]
    report={'fallback_checks':fallback_checks,'fallback_compared_pixels':sum(v['compared_pixels'] for v in fallback_checks),'frames_run':max(records)+1,'character_pixel_checks':checks,'compared_pixels':sum(v['pixels'] for v in checks),'mismatched_pixels':0,'seen_poses':[sorted(s) for s in seen],'facings':[sorted(s) for s in directions],
            'display_pipeline_lags':lags,'resident_texture_hashes':sorted(textures),'simulation_matches_original_renderer':bool(control),'simulation_frames_compared':len([f for f in records if f>=330]) if control else 0,
            'method':'Normal controller input, read-only libretro save states; native indexed source -> hardware RGB565. Roots from actual world/camera state; possible actor/drum occlusions excluded. No game hooks or RAM writes.'}
    (folder/'validation.json').write_text(json.dumps(report,indent=2)+'\n');return report
