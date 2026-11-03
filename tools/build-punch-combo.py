#!/usr/bin/env python3
"""Two indexed native upper textures, exact approved heads and shared legs."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,struct
R=Path(__file__).resolve().parents[1];O=R/'assets/punch-combo'
def build():
 source=Image.open(O/'source/rear-cross-study.png').convert('RGBA');pal=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=np.array([list(pal[3*i:3*i+3][::-1]) for i in range(256)],dtype=np.int32)
 entries=[]
 for a,n in enumerate(['buck','chuck']):
  box=[(274,11,1002,695),(1069,5,1801,695)][a];crop=source.crop(box);h=88;w=round(crop.width*h/crop.height);q=crop.resize((w,h),Image.Resampling.NEAREST);arr=np.array(q);arr[:,:,3]=np.where(arr[:,:,3]>=128,255,0);q=Image.fromarray(arr)
  im=Image.new('RGBA',(160,112));im.alpha_composite(q,([26,24][a],18))
  # The artwork study supplies arms/torso only. Approved heads remain exact.
  guard=im.crop((80,32,94,43));arr=np.array(im);arr[:40]=0;im=Image.fromarray(arr);idle=Image.open(R/f'assets/animation-polish/{n}-00.png').convert('RGBA');im.alpha_composite(idle.crop((39,0,89,24)),(41,16));im.alpha_composite(guard,(80,32))
  upper=im.crop((40,20,120,64));arr=np.array(upper);flat=arr[:,:,:3].reshape(-1,3).astype(np.int32);ids=np.empty(len(flat),dtype=np.uint8)
  # Raw indices1..253 only: 0 is transparent; loader adds one to every index.
  for i,c in enumerate(flat):ids[i]=1+np.argmin(((colors[1:254]-c)**2).sum(axis=1))
  ids[arr[:,:,3].reshape(-1)==0]=0;idx=ids.reshape(44,80);rgba=np.zeros((44,80,4),dtype=np.uint8);rgba[:,:,:3]=colors[idx];rgba[:,:,3]=np.where(idx,255,0);rgba[idx==0]=0;upper=Image.fromarray(rgba)
  header=bytearray((R/'assets/gallery/GB0.TGA').read_bytes()[:18]);struct.pack_into('<HH',header,12,80,44);header[17]=0
  blob=bytes(header)+pal+idx[::-1].tobytes();path=O/f'XC{a}.TGA';path.write_bytes(blob);upper.save(O/f'{n}-upper-native.png')
  entries.append({'actor':n,'name':path.name,'width':80,'height':44,'x':40,'y':20,'bytes':3520,'sha256':hashlib.sha256(blob).hexdigest(),'opaque_bounds':list(upper.getbbox()),'used_colors':len(set(ids))-1})
 m={'parent':'84f7ba38ea239119d98e86cfabe57daa1ca97679','palette':'assets/gallery/GB0.TGA','palette_sha256':hashlib.sha256(pal).hexdigest(),'resources':entries,'added_bytes':7040,'added_definitions':2,'boot_bytes':453344,'free_bytes':5144,'definitions':255,'head_offset':[2,0],'shared_lower':'seq_lower[actor]','source_sha256':hashlib.sha256((O/'source/rear-cross-study.png').read_bytes()).hexdigest()};(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(m)
if __name__=='__main__':build()
