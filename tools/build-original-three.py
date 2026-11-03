#!/usr/bin/env python3
"""Copy exact historical prototype frames; reuse existing TGA IDs, no art edits."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,subprocess,shutil
R=Path(__file__).resolve().parents[1];O=R/'assets/original-three-walk';O.mkdir(exist_ok=True)
old=json.loads((R/'assets/animation-study/manifest.json').read_text());polish=json.loads((R/'assets/animation-polish/manifest.json').read_text());resources=polish['resources'];required=set();actors=[]
creation=subprocess.check_output(['git','rev-parse','5a6bd36'],cwd=R,text=True).strip();approved=subprocess.check_output(['git','rev-parse','ff24c5e'],cwd=R,text=True).strip()
for actor in polish['actors']:
 for f in actor['frames'][:4]:required.update(p['resource'] for p in f['parts'])
for a,n in enumerate(['buck','chuck']):
 frames=[]
 for f in range(1,4):
  rel=f'assets/animation-study/{n}-{f:02d}.png';data=(R/rel).read_bytes()
  assert data==subprocess.check_output(['git','show',creation+':'+rel],cwd=R)==subprocess.check_output(['git','show',approved+':'+rel],cwd=R)
  (O/f'{n}-{f-1:02d}.png').write_bytes(data);im=Image.open(R/rel).convert('RGBA');parts=[]
  for part,q in enumerate(old['actors'][a]['frames'][f]['parts']):
   rid=a*21+f*3+part;required.add(rid);assert resources[rid]['name']==q['name']
   blob=(R/'assets/animation-study'/q['name']).read_bytes();assert blob==subprocess.check_output(['git','show',approved+':assets/animation-study/'+q['name']],cwd=R)
   parts.append({k:q[k] for k in ['x','y','width','height']}|{'resource':rid,'name':q['name'],'tga_sha256':hashlib.sha256(blob).hexdigest()})
  frames.append({'frame':f-1,'source_frame':f,'source_path':rel,'png_sha256':hashlib.sha256(data).hexdigest(),'rgba_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'parts':parts})
 actors.append({'name':n,'frames':frames})
boot=302336+sum(resources[r]['aligned_bytes'] for r in required-{0,1,2,21,22,23});m={'creation_commit':creation,'approved_commit':approved,'baseline':'8e86fa1a4d7e8ef74392a9f1912dcc84ffb8e431','canvas':[128,96],'root':[64,92],'standing_height':88,'new_texture_bytes':0,'boot_required':sorted(required),'boot_vdp1_bytes':boot,'boot_free_bytes':458488-boot,'full_vdp1_bytes':427104,'full_free_bytes':31384,'boot_sprite_slots':95+len(required),'full_sprite_slots':176,'actors':actors}
(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
parts=',\n'.join('{'+','.join('{'+','.join('{%d,%d,%d,%d,%d}'%(p['resource'],p['x'],p['y'],p['width'],p['height']) for p in f['parts'])+'}' for f in a['frames'])+'}' for a in actors)
(R/'src/original_three_data.h').write_text('/* Exact ff24c5e prototype poses1..3; no new textures. */\n#ifndef MF_ORIGINAL_THREE_DATA_H\n#define MF_ORIGINAL_THREE_DATA_H\n#define MF_ORIGINAL_THREE_BOOT_BYTES %du\n#define MF_ORIGINAL_THREE_FULL_BYTES 427104u\nstatic const unsigned char original_three_required[81]={%s};\nstatic const mf_polish_piece original_three_parts[2][3][3]={\n%s\n};\n#endif\n'%(boot,','.join(str(int(i in required)) for i in range(81)),parts))
# Native PNG contact sheet and palette-exact GIF comparisons.
pal=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=[tuple(pal[i*3:i*3+3][::-1]) for i in range(256)];idx={c:i for i,c in enumerate(colors[:254]) if i}
sheet=Image.new('RGB',(384,232),(27,31,43));d=ImageDraw.Draw(sheet)
for ai,n in enumerate(['buck','chuck']):
 for f in range(3):
  im=Image.open(O/f'{n}-{f:02d}.png').convert('RGBA');sheet.paste(im,(128*f,116*ai),im);d.line((128*f,116*ai+92,128*f+127,116*ai+92),fill=(88,112,110));d.text((128*f+2,116*ai+98),f'{n} original {f+1}',fill=(240,240,245))
 for mode,hold in [('moderate',8),('slow',10)]:
  ims=[]
  for f in range(3):
   im=Image.open(O/f'{n}-{f:02d}.png').convert('RGBA');g=Image.new('P',im.size);g.putpalette([v for c in colors for v in c]);g.putdata([idx[c[:3]] if c[3] else 0 for c in im.getdata()]);ims.append(g.resize((384,288),Image.Resampling.NEAREST))
  ims[0].save(O/f'{n}-{mode}.gif',save_all=True,append_images=ims[1:],duration=round(hold*100/60)*10,loop=0,transparency=0,disposal=2,optimize=False)
sheet.save(O/'contact-native.png');sheet.resize((1152,696),Image.Resampling.NEAREST).save(O/'contact-3x.png')
for target,source,count,start in [('swagger','swagger-walk',3,0),('six','animation-polish',6,4)]:
 dest=O/target;dest.mkdir(exist_ok=True)
 for n in ['buck','chuck']:
  for f in range(count):shutil.copy(R/f'assets/{source}/{n}-{f+start:02d}.png',dest/f'{n}-{f:02d}.png')
html='''<!doctype html><meta charset="utf-8"><title>Original three / Swagger / corrected six</title><style>body{background:#1b1f2b;color:#eee;font:16px system-ui;max-width:1300px;margin:24px auto}img,canvas{max-width:100%;image-rendering:pixelated}button{padding:8px;margin:4px}</style>
<h1>Exact original three-pose restoration</h1><p>Left: ff24c5e original three. Middle: Swagger. Right: corrected six at75% playback. Top Buck, bottom Chuck. All native88px, unchanged palette/root.</p>
<button id="timing">Original timing: moderate8 ticks</button><button id="pause">Pause/play</button><button id="step">Step poses</button><button id="flip">Mirror</button><p id="status"></p><canvas width="1152" height="576"></canvas><img src="contact-3x.png">
<script>const names=['buck','chuck'],sets=['','swagger/','six/'],frames=names.map(n=>sets.map((s,v)=>Array.from({length:v===2?6:3},(_,f)=>{let im=new Image;im.src=s+n+'-'+String(f).padStart(2,'0')+'.png';return im})));const canvas=document.querySelector('canvas'),ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;let clocks=[0,0,0,0],slow=false,paused=false,flip=false,last=performance.now(),acc=0;
function holds(a,v){return v===0?[slow?10:8,slow?10:8,slow?10:8]:v===1?(a?[15,14,15]:[14,14,14]):[7,7,6,7,7,6]}
function key(a,v){return v===1?a+1:v===2?3:0}function pose(a,v){let t=clocks[key(a,v)],h=holds(a,v);for(let f=0;f<h.length;f++){if(t<h[f])return f;t-=h[f]}return 0}
document.getElementById('timing').onclick=()=>{slow=!slow;clocks[0]=0;document.getElementById('timing').textContent='Original timing: '+(slow?'slow10':'moderate8')+' ticks'};document.getElementById('pause').onclick=()=>paused=!paused;document.getElementById('flip').onclick=()=>flip=!flip;document.getElementById('step').onclick=()=>{paused=true;for(let v=0;v<3;v++)for(let a=0;a<(v===1?2:1);a++){let h=holds(a,v),f=(pose(a,v)+1)%h.length;clocks[key(a,v)]=h.slice(0,f).reduce((x,y)=>x+y,0)}};
function draw(t){acc+=Math.min(100,t-last);last=t;while(acc>=1000/60){if(!paused)clocks=clocks.map((v,i)=>(v+1)%[(slow?30:24),42,44,40][i]);acc-=1000/60}ctx.fillStyle='#1b1f2b';ctx.fillRect(0,0,1152,576);for(let a=0;a<2;a++){for(let v=0;v<3;v++){ctx.save();ctx.translate(v*384+(flip?384:0),a*288);ctx.scale(flip?-3:3,3);let im=frames[a][v][pose(a,v)];if(im.complete&&im.naturalWidth)ctx.drawImage(im,0,0);ctx.restore()}ctx.strokeStyle='#58706e';ctx.beginPath();ctx.moveTo(0,a*288+276);ctx.lineTo(1152,a*288+276);ctx.stroke()}document.getElementById('status').textContent='Original '+(pose(0,0)+1)+' / Swagger B'+(pose(0,1)+1)+' C'+(pose(1,1)+1)+' / Six '+(pose(0,2)+1);requestAnimationFrame(draw)}requestAnimationFrame(draw)</script>'''
(O/'comparison.html').write_text(html)
print(json.dumps({k:m[k] for k in ['boot_vdp1_bytes','boot_free_bytes','boot_sprite_slots','full_vdp1_bytes','new_texture_bytes']},indent=2))
