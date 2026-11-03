#!/usr/bin/env python3
"""Exact indexed packing of four essential new resources; originals remain immutable."""
from pathlib import Path
from PIL import Image
import struct,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'assets/corporate-punk-hq-combat';B=R/'assets/corporate-punk-lighting';pal=(B/'palette.bgr24').read_bytes();resources=[];parts={}
for name in ['strike','hurt','fall','ground']:
 im=Image.open(O/f'{name}.png');assert im.mode=='P' and im.size==(144,112)
 # The strike shares the original head, hips, legs and boots; only torso/arm is new.
 q=Image.new('P',im.size);q.putpalette(im.getpalette());q.info['transparency']=0
 q.paste(im.crop((0,38,144,68)),(0,38)) if name=='strike' else q.paste(im)
 box=q.getbbox();x,y,r,b=box;w=(r-x+7)//8*8;h=(b-y+1)//2*2
 raw=bytes(q.getpixel((xx,yy)) if xx<144 and yy<112 else 0 for yy in range(y+h-1,y-1,-1) for xx in range(x,x+w));assert max(raw)<254
 hd=bytearray(18);hd[1:3]=b'\1\1';struct.pack_into('<H',hd,5,256);hd[7]=24;struct.pack_into('<HH',hd,12,w,h);hd[16]=8
 blob=bytes(hd)+pal+raw;file=f'CQ{len(resources):02}.TGA';(O/file).write_bytes(blob);rid=10+len(resources);resources.append(dict(name=file,width=w,height=h,bytes=(w*h+31)&~31,sha256=hashlib.sha256(blob).hexdigest()));parts[name]=dict(resource=rid,x=x-16,y=y-16,width=w,height=h)
new=sum(r['bytes'] for r in resources);m=dict(parent='bba999c0621f0d6f16aa13a2f776cc7dd25105a0',canvas=[144,112],root=[64,108],resources=resources,parts=parts,texture_bytes=new,replaced_bytes=56960,boot_bytes=457888-56960+new,free_bytes=458488-(457888-56960+new),slots=254-12+len(resources),palette_banks_added=0,shared_idle_walk_bytes=11744)
(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');assert m['free_bytes']>0 and m['slots']<=255
lines=['/* Generated indexed enemy combat pieces. Original CP bank is shared. */','#ifndef MF_CORPORATE_HQ_DATA_H','#define MF_CORPORATE_HQ_DATA_H',f'#define MF_CPHQ_BYTES {new}u','#define MF_CPHQ_REPLACED 56960u','#define MF_CPHQ_NEW 4','static const mf_cp_resource cphq_resources[MF_CPHQ_NEW]={']
lines+=['{"%s",%d,%d},'%(p['name'],p['width'],p['height']) for p in resources];lines+=['};','static const mf_cp_piece cphq_strike_upper={%d,%d,%d,%d};'%tuple(parts['strike'][k] for k in ['resource','x','y','width']),'static const mf_cp_piece cphq_full[3]={'];lines+=['{%d,%d,%d,%d},'%tuple(parts[n][k] for k in ['resource','x','y','width']) for n in ['hurt','fall','ground']];lines+=['};','#endif'];(R/'src/corporate_hq_data.h').write_text('\n'.join(lines)+'\n');print(m)
