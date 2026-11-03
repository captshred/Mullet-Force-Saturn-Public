#!/usr/bin/env python3
"""Offline before/after review and measured silhouette audit; no game assets changed."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
R=Path(__file__).resolve().parents[1];O=R/'assets/animation-polish';before=O/'gait-before'
results={};sheet=Image.new('RGB',(768,464),(27,31,43));d=ImageDraw.Draw(sheet)
for ai,name in enumerate(['buck','chuck']):
 results[name]=[]
 for version in range(2):
  for phase in range(6):
   p=(O if version else before)/f'{name}-{phase+4:02d}.png';im=Image.open(p).convert('RGBA');x=phase*128;y=(ai*2+version)*116
   sheet.paste(im,(x,y),im);d.line((x,y+92,x+127,y+92),fill=(88,112,110));d.text((x+1,y+98),f'{name} {"after" if version else "before"} {phase+1}',fill=(240,240,245))
 for phase in range(3):
  record={'pair':[phase+1,phase+4]}
  for label,folder in [('before',before),('after',O)]:
   a=Image.open(folder/f'{name}-{phase+4:02d}.png').convert('RGBA');b=Image.open(folder/f'{name}-{phase+7:02d}.png').convert('RGBA')
   ap=list(a.crop((0,52,128,96)).getdata());bp=list(b.crop((0,52,128,96)).getdata())
   changed=sum(bool(x[3])!=bool(y[3]) for x,y in zip(ap,bp));union=sum(bool(x[3] or y[3]) for x,y in zip(ap,bp));inter=sum(bool(x[3] and y[3]) for x,y in zip(ap,bp))
   record[label]={'rgba_identical':a.tobytes()==b.tobytes(),'lower_silhouette_changed_pixels':changed,'silhouette_iou':inter/union}
  results[name].append(record)
sheet.save(O/'gait-compare-native.png');sheet.resize((1536,928),Image.Resampling.NEAREST).save(O/'gait-compare-2x.png')
(O/'gait-audit.json').write_text(json.dumps(results,indent=2)+'\n')
html='''<!doctype html><meta charset="utf-8"><title>Opposite-stride correction review</title>
<style>body{background:#1b1f2b;color:#eee;font:16px system-ui;max-width:1000px;margin:24px auto}canvas,img{image-rendering:pixelated;max-width:100%}button{padding:8px;margin:4px}a{color:#9df}</style>
<h1>Six-frame gait correction</h1><p>Left: ebc9d79 before. Right: corrected opposite stride. Top Buck; bottom Chuck. Frames 1–3 and upper bodies are pixel-identical. Same native 88px height, palette and five ticks per frame.</p>
<button id="pause">Pause / play</button><button id="step">Next pose</button><button id="flip">Mirror</button><p id="status"></p><canvas id="view" width="768" height="576"></canvas>
<p>Review the leg overlap at 3→4 and 6→1, toe-off and planted feet. This is the isolated animation preview; gameplay sprite banks are unchanged.</p><img src="gait-compare-2x.png"><p><a href="preview.html">Prototype / idle / transition viewer</a></p>
<script>
const c=document.querySelector('canvas'),ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;
const names=['buck','chuck'],images=names.map(n=>[0,1].map(v=>Array.from({length:6},(_,f)=>{let i=new Image;i.src=(v?'':'gait-before/')+n+'-'+String(f+4).padStart(2,'0')+'.png';return i})));
let paused=false,flip=false,frame=0,acc=0,last=performance.now();
document.getElementById('pause').onclick=()=>paused=!paused;document.getElementById('step').onclick=()=>{paused=true;frame=(frame+1)%6;acc=0};document.getElementById('flip').onclick=()=>flip=!flip;
function draw(t){if(!paused){acc+=Math.min(100,t-last);while(acc>=5000/60){acc-=5000/60;frame=(frame+1)%6}}last=t;ctx.fillStyle='#1b1f2b';ctx.fillRect(0,0,768,576);for(let a=0;a<2;a++){for(let v=0;v<2;v++){ctx.save();ctx.translate(v*384+(flip?384:0),a*288);ctx.scale(flip?-3:3,3);let im=images[a][v][frame];if(im.complete&&im.naturalWidth)ctx.drawImage(im,0,0);ctx.restore()}ctx.strokeStyle='#58706e';ctx.beginPath();ctx.moveTo(0,a*288+276);ctx.lineTo(768,a*288+276);ctx.stroke()}document.getElementById('status').textContent='Pose '+(frame+1)+' / 6'+(paused?' paused':'');requestAnimationFrame(draw)}requestAnimationFrame(draw)
</script>'''
(O/'gait-review.html').write_text(html)
p=O/'preview.html';s=p.read_text();line='<p><a href="gait-review.html">Compare the prior polish against the corrected opposite stride</a></p>'
if line not in s:s=s.replace('<h2>Walk comparisons</h2>',line+'\n<h2>Walk comparisons</h2>');p.write_text(s)
print(json.dumps(results,indent=2))
