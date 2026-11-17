#!/usr/bin/env python3
"""Panic isolation, runtime roundtrip and exact private-free preservation tests."""
from pathlib import Path
import sys,subprocess,unittest,struct,hashlib,collections
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from level1_refinement import BASE,read,write,signature,curve
import seq
class RefinementTests(unittest.TestCase):
 def original(self,name):return subprocess.check_output(['git','show',BASE+':'+name],cwd=R)
 def test_sequence_roundtrip_preserves_notes_tempo_controls_and_loop(self):
  data=self.original('assets/cd/STAGE.SEQ');h,events,end=read(data);rebuilt=write(h,events)
  a=seq.decode(data);b=seq.decode(rebuilt)
  for key in ('notes','controls','loops','programs','bends','tempos','end'):self.assertEqual(a[key],b[key])
 def test_sfx_gate_and_program_unchanged_and_no_global_panic(self):
  a=self.original('assets/cd/FX.SEQ');b=(R/'assets/cd/FX.SEQ').read_bytes()
  for song in range(8):
   x=seq.decode(a,song);y=seq.decode(b,song)
   for key in ('notes','programs','loops','tempos','end'):self.assertEqual(x[key],y[key])
   self.assertFalse(any(cc==123 for t,c,cc,v in y['controls']))
   self.assertEqual(y['controls'],[(t,c,32 if cc==123 else cc,v) for t,c,cc,v in x['controls']])
 def test_native_driver_confirms_global_cc123_and_noop_cc120(self):
  path=R/'.deps/joengine/Compiler/COMMON/SGL_302j/INC/SDDRVS.TSK'
  if not path.exists():self.skipTest('pinned SDK unavailable')
  data=path.read_bytes();self.assertEqual(hashlib.sha256(data).hexdigest(),'68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6')
  self.assertEqual(struct.unpack_from('>H',data,0x2fb8+2*123)[0],0x3172)
  self.assertEqual(data[0x317a:0x3192].hex(),'48e7fff e7e1f49ee10002a7c00100000426c003a422c0000'.replace(' ',''))
 def test_retained_rhythm_and_unique_harmonies_centered_leads_keep_pan(self):
  old=read(self.original('assets/cd/STAGE.SEQ'))[1];new=read((R/'assets/cd/STAGE.SEQ').read_bytes())[1]
  lookup={signature(n):n for n in old if n['kind']=='note'};right=[]
  for n in new:
   if n['kind']!='note':continue
   prior=lookup[signature(n)];self.assertEqual(curve(n,new),curve(prior,old))
   self.assertEqual(n['pan'],64 if prior['pan'] in (35,93) else prior['pan'])
   if prior['pan']==93:right.append(n)
  self.assertEqual(len(right),6);self.assertTrue(any(n['pitch']==79 for n in right));self.assertTrue(any(n['pitch']==38 for n in right))
 def test_no_pcm_or_sfx_bank_change(self):
  old=self.original('assets/cd/STAGE.TON');new=(R/'assets/cd/STAGE.TON').read_bytes();allowed={int.from_bytes(old[8+2*i:10+2*i],'big')+19 for i in range(13)}
  self.assertEqual(len(old),len(new));self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(old,new))))
  self.assertEqual(self.original('assets/cd/FX.TON'),(R/'assets/cd/FX.TON').read_bytes())
if __name__=='__main__':unittest.main()
