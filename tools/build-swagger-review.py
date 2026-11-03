#!/usr/bin/env python3
"""Disk-only animated comparison; does not change game sprite assets."""
from pathlib import Path
from PIL import Image
import re,shutil
R=Path(__file__).resolve().parents[1];O=R/'assets/swagger-walk';P=R/'assets/animation-polish';ref=O/'reference-six';ref.mkdir(exist_ok=True)
palette=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=[tuple(palette[i*3:i*3+3][::-1]) for i in range(256)];indices={c:i for i,c in enumerate(colors[:254]) if i}
for name in ['buck','chuck']:
 ims=[]
 for f in range(4,10):
  path=P/f'{name}-{f:02d}.png';shutil.copy(path,ref/path.name);im=Image.open(path).convert('RGBA');g=Image.new('P',im.size);g.putpalette([v for c in colors for v in c]);g.putdata([indices[c[:3]] if c[3] else 0 for c in im.getdata()]);ims.append(g.resize((384,288),Image.Resampling.NEAREST))
 ims[0].save(O/f'{name}-six.gif',save_all=True,append_images=ims[1:],duration=[120,120,100,120,120,100],loop=0,transparency=0,disposal=2,optimize=False)
timing=(R/'src/swagger_timing.h').read_text();holds=[list(map(int,re.search(n+r'_HOLDS\s+\{([^}]+)',timing).group(1).split(','))) for n in ['MF_SWAGGER_BUCK','MF_SWAGGER_CHUCK']]
html='''<!doctype html><meta charset="utf-8"><title>Swagger / six-frame walk comparison</title>
<style>body{font:16px system-ui;background:#1b1f2b;color:#eee;max-width:1100px;margin:24px auto}img,canvas{image-rendering:pixelated;max-width:100%}button{padding:8px;margin:4px}</style>
<h1>Restrained three-pose swagger</h1><p>Left: preserved six-frame walk at75% playback (40 ticks). Right: compact three-pose weight-transfer experiment. Top Buck, bottom Chuck. Same88px height, palette and root. Faces/upper bodies unchanged.</p>
<button id="pause">Pause/play</button><button id="step">Step both cycles</button><button id="flip">Mirror</button><button id="reset">Restart loops</button><p id="status"></p><canvas width="768" height="576"></canvas>
<p>Play the two builds to assess foot sliding at unchanged movement speed. This viewer tests source appearance/cadence; it does not simulate collision or change world speed.</p><img src="swagger-contact-3x.png">
<script>
const holds=HOLDS,oldHolds=[7,7,6,7,7,6],names=['buck','chuck'];
const frames=names.map(n=>[Array.from({length:6},(_,f)=>{let i=new Image;i.src='reference-six/'+n+'-'+String(f+4).padStart(2,'0')+'.png';return i}),Array.from({length:3},(_,f)=>{let i=new Image;i.src=n+'-'+String(f).padStart(2,'0')+'.png';return i})]);
const c=document.querySelector('canvas'),ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;let ticks=[0,0,0],paused=false,flip=false,last=performance.now(),acc=0;
function phase(t,h){for(let f=0;f<h.length;f++){if(t<h[f])return f;t-=h[f]}return0}
function start(f,h){return h.slice(0,f).reduce((a,b)=>a+b,0)}
document.getElementById('pause').onclick=()=>paused=!paused;document.getElementById('flip').onclick=()=>flip=!flip;document.getElementById('reset').onclick=()=>{ticks=[0,0,0];acc=0};document.getElementById('step').onclick=()=>{paused=true;let h=[oldHolds,...holds];ticks=ticks.map((t,i)=>start((phase(t,h[i])+1)%h[i].length,h[i]))};
function draw(t){acc+=Math.min(100,t-last);last=t;while(acc>=1000/60){if(!paused)ticks=ticks.map((v,i)=>(v+1)%[40,holds[0].reduce((a,b)=>a+b,0),holds[1].reduce((a,b)=>a+b,0)][i]);acc-=1000/60}ctx.fillStyle='#1b1f2b';ctx.fillRect(0,0,768,576);for(let a=0;a<2;a++){for(let v=0;v<2;v++){let f=phase(ticks[v?a+1:0],v?holds[a]:oldHolds);ctx.save();ctx.translate(v*384+(flip?384:0),a*288);ctx.scale(flip?-3:3,3);let im=frames[a][v][f];if(im.complete&&im.naturalWidth)ctx.drawImage(im,0,0);ctx.restore()}ctx.strokeStyle='#58706e';ctx.beginPath();ctx.moveTo(0,a*288+276);ctx.lineTo(768,a*288+276);ctx.stroke()}document.getElementById('status').textContent='Six pose '+(phase(ticks[0],oldHolds)+1)+' | Buck swagger '+(phase(ticks[1],holds[0])+1)+' | Chuck swagger '+(phase(ticks[2],holds[1])+1);requestAnimationFrame(draw)}requestAnimationFrame(draw)
</script>'''.replace('HOLDS',str(holds)).replace('return0','return 0')
(O/'comparison.html').write_text(html)
