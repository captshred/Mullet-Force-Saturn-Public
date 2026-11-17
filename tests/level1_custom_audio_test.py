#!/usr/bin/env python3
"""Regressions for GP ties, duplicate drum attacks, native gates and rate tuning."""
from pathlib import Path
import sys,tempfile,zipfile,unittest,struct,importlib.util
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from level1_audio import read_gp,encode_seq,build_ton
import seq
class AudioTests(unittest.TestCase):
 def test_simultaneous_duplicate_drums_keep_independent_gates(self):
  n=[dict(on=1938,off=2000,channel=12,pitch=38,velocity=25,program=4),dict(on=1938,off=2200,channel=13,pitch=38,velocity=127,program=4)]
  s=seq.decode(encode_seq(n,[],2400));self.assertEqual(s['notes'],[(1938,2000,12,38,25),(1938,2200,13,38,127)])
  self.assertEqual(s['loops'],[0,2400])
 def test_large_gates_and_silence_do_not_move_notes(self):
  n=[dict(on=20000,off=52000,channel=0,pitch=26,velocity=76,program=2)]
  self.assertEqual(seq.decode(encode_seq(n,[],60000))['notes'],[(20000,52000,0,26,76)])
 def test_program_selection_precedes_each_simultaneous_attack(self):
  n=[dict(on=0,off=120,channel=12,pitch=49,velocity=127,program=7),dict(on=0,off=240,channel=12,pitch=52,velocity=100,program=9)]
  data=encode_seq(n,[],480)
  self.assertLess(data.index(bytes([0xcc,7,0])),data.index(bytes([12,49,127,120,0])))
  self.assertLess(data.index(bytes([12,49,127,120,0])),data.index(bytes([0xcc,9,0])))
 def test_gp_reused_notes_and_ties_expand_without_replaying_attack(self):
  text='''<GPIF><MasterTrack><Automations><Automation><Type>Tempo</Type><Bar>0</Bar><Value>164 2</Value></Automation></Automations></MasterTrack><MasterBars><MasterBar><Time>4/4</Time><Bars>0</Bars></MasterBar><MasterBar><Time>4/4</Time><Bars>1</Bars></MasterBar></MasterBars><Bars><Bar id="0"><Voices>0 -1 -1 -1</Voices></Bar><Bar id="1"><Voices>1 -1 -1 -1</Voices></Bar></Bars><Voices><Voice id="0"><Beats>0</Beats></Voice><Voice id="1"><Beats>1</Beats></Voice></Voices><Beats><Beat id="0"><Rhythm ref="0"/><Dynamic>MF</Dynamic><Notes>0</Notes></Beat><Beat id="1"><Rhythm ref="0"/><Dynamic>MF</Dynamic><Notes>1</Notes></Beat></Beats><Rhythms><Rhythm id="0"><NoteValue>Whole</NoteValue></Rhythm></Rhythms><Notes><Note id="0"><Tie origin="true"/><Properties><Property name="Midi"><Number>48</Number></Property><Property name="String"><String>0</String></Property></Properties></Note><Note id="1"><Tie destination="true"/><Properties><Property name="Midi"><Number>48</Number></Property><Property name="String"><String>0</String></Property></Properties></Note></Notes></GPIF>'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'fixture.gp'
   with zipfile.ZipFile(p,'w') as z:z.writestr('Content/score.gpif',text)
   notes,end,meters,rows=read_gp(p)
  self.assertEqual((len(notes),len(rows),end),(1,2,3840));self.assertEqual((notes[0]['on'],notes[0]['off'],notes[0]['beat_off']),(0,3840,1920))
 def test_native_pcm8_rate_root_and_loop_guard(self):
  sample=dict(role='fixture',program=0,root=48,rate=22050,bits=8,frames=8,loop=True,lsa=4,tl=8,pcm=bytes([0,1,2,3,4,5,6,7]))
  t=build_ton([sample]);v=int.from_bytes(t[8:10],'big');l=v+4;sa=((t[l+3]&15)<<16)|int.from_bytes(t[l+4:l+6],'big')
  self.assertEqual(t[l+3]&0x30,0x30);self.assertEqual(t[l+25],60);self.assertEqual(t[sa+8:sa+12],bytes([4,5,6,7]))
if __name__=='__main__':unittest.main()
