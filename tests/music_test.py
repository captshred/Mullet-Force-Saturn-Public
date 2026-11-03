#!/usr/bin/env python3
import unittest,tempfile,sys,subprocess,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import midi,seq,music
class MusicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.work=Path(cls.tmp.name)
        cls.exe=cls.work/'mid2seq'
        subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-O2',str(ROOT/'third_party/mid2seq/mid2seq.c'),'-o',str(cls.exe)],check=True)
        cls.cfg=json.loads((ROOT/'assets/music/config.json').read_text())
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def convert(self,events,end,loop=True):
        src=self.work/'in.mid'; dst=self.work/'out.seq'
        midi.write_format0(src,480,events,end)
        subprocess.run([str(self.exe),str(src),str(dst)]+(['--loop'] if loop else []),check=True,stdout=subprocess.DEVNULL)
        return seq.decode(dst.read_bytes())
    def test_tempo_changes_gates_velocities_and_loop(self):
        s=self.convert([(0,b'\xff\x51\x03\x07\xa1\x20'),(0,b'\xc0\x00'),(0,b'\x90\x3c\x49'),
            (240,b'\xe0\x40\x40'),(480,b'\xff\x51\x03\x06\x1a\x80'),(960,b'\x80\x3c\0'),
            (960,b'\x90\x40\x65'),(1920,b'\x80\x40\0'),(1920,b'\xb0\x78\0')],1920)
        self.assertEqual(s['tempos'],[(480,500000),(1440,400000)])
        self.assertEqual(s['notes'],[(0,960,0,60,73),(960,1920,0,64,101)])
        self.assertEqual(s['bends'],[(240,0,65)])
        self.assertEqual(s['loops'],[0,1920]);self.assertEqual(s['tempo_loop_offset'],8)
    def test_long_initial_silence_gate_and_nonlooping(self):
        s=self.convert([(0,b'\xff\x51\x03\x07\xa1\x20'),(6144,b'\x90\x3c\x55'),
            (22528,b'\x80\x3c\0'),(22528,b'\xb0\x78\0')],22528,False)
        self.assertEqual(s['notes'],[(6144,22528,0,60,85)]);self.assertFalse(s['loops'])
    def test_rejects_truncated_converter_header(self):
        path=self.work/'truncated.mid'; path.write_bytes(b'MThd')
        result=subprocess.run([str(self.exe),str(path),str(self.work/'bad.seq')],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Truncated MIDI header',result.stderr)
    def test_source_report(self):
        r=midi.inspect(ROOT/'assets/music/drop-zone.mid')
        self.assertEqual((r['format'],r['ppqn'],len(r['tracks']),r['notes'],r['max_simultaneous_notes']),(1,480,6,5120,11))
        self.assertFalse(r['drum_notes']);self.assertFalse(r['unclosed_notes'])
        self.assertAlmostEqual(r['duration_seconds'],213.292299)
    def test_percussion_route(self):
        a=self.work/'drums.mid'; b=self.work/'drums-normal.mid'
        midi.write_format0(a,480,[(0,b'\x99\x2a\x64'),(60,b'\x89\x2a\0')],120)
        self.assertEqual(music.normalize(a,b,self.cfg),[])
        _,_,tt=midi.read(b);ns,*_=midi.notes(midi.merged(tt))
        self.assertEqual(ns,[(0,60,11,60,100)]) # MIDI ch10 hat -> SCSP ch12, voice5
        self.assertTrue(any(e['status']==0xcb and e['data']==b'\x05' for e in midi.merged(tt)))
    def test_bad_gate_and_sustain_fail_loudly(self):
        a=self.work/'invalid.mid'; b=self.work/'invalid-normal.mid'
        midi.write_format0(a,480,[(0,b'\xc0\x1e'),(0,b'\x90\x3c\x60')],100)
        with self.assertRaises(ValueError): music.normalize(a,b,self.cfg)
        midi.write_format0(a,480,[(0,b'\xc0\x1e'),(0,b'\xb0\x40\x7f')],100)
        with self.assertRaises(ValueError): music.normalize(a,b,self.cfg)
    def test_overlapping_percussion_is_fixed_pitch_and_separate(self):
        a=self.work/'overlap-drums.mid';b=self.work/'overlap-normal.mid'
        midi.write_format0(a,480,[(0,b'\x99\x24\x64'),(0,b'\x99\x26\x5a'),(0,b'\x99\x2a\x50'),
            (60,b'\x89\x2a\0'),(120,b'\x89\x26\0'),(240,b'\x89\x24\0')],480)
        music.normalize(a,b,self.cfg)
        _,_,tracks=midi.read(b);ns,*_=midi.notes(midi.merged(tracks))
        self.assertEqual(ns,[(0,60,11,60,80),(0,120,10,60,90),(0,240,9,60,100)])
    def test_linear_gain_and_clipping_rejection(self):
        music.register()
        original=music.patch_ton(music.kit.build_ton(music.kit.load_config(str(ROOT/'assets/music/config.json'))),6)
        scaled,report=music.apply_linear_gain(original,1.35)
        n=(struct.unpack_from('>H',original)[0]-8)//2
        start=max(struct.unpack_from('>H',original,8+2*i)[0]+36 for i in range(n))
        self.assertEqual(scaled[:start],original[:start])
        for i in range(start,len(original),2):
            a=struct.unpack_from('>h',original,i)[0]; b=struct.unpack_from('>h',scaled,i)[0]
            self.assertLessEqual(abs(b-1.35*a),.500001)
        self.assertEqual(report['hard_clipped_samples'],0)
        with self.assertRaises(ValueError): music.apply_linear_gain(original,2)
    def test_music_boost_uses_tl_and_safe_pcm_without_clipping(self):
        music.register()
        old=music.patch_ton(music.kit.build_ton(music.kit.load_config(str(ROOT/'assets/music/config.json'))),6)
        old,_=music.apply_linear_gain(old,1.35)
        new,report=music.boost_music_bank(old,6)
        self.assertEqual(len(old),len(new))
        for i,entry in enumerate(report):
            layer=struct.unpack_from('>H',new,8+2*i)[0]+4
            self.assertEqual(new[layer+15],entry['tl_after'])
            self.assertGreaterEqual(entry['tl_after'],0)
            self.assertLess(entry['peak_after'],32768)
            if i<3:self.assertAlmostEqual(entry['actual_boost_db'],6)
            # The envelope, pitch and routing of every voice are preserved.
            for offset in range(32):
                if offset!=15:self.assertEqual(old[layer+offset],new[layer+offset])
        self.assertEqual(report[3]['actual_boost_db'],4.5) # explicit unused kick limit
        self.assertFalse(report[3]['residual_pcm_boost_safe'])
    def test_torch_waves_and_loop_gates(self):
        for kind,gain in [('ignite',.45),('hiss',.2)]:
            a=music.torch_wave(kind,44100,gain)
            self.assertEqual(a,music.torch_wave(kind,44100,gain))
            self.assertEqual(a[0],0);self.assertEqual(a[-1],0)
            self.assertLess(max(abs(v) for v in a),1)
        payload=music.fx_sequence()
        self.assertEqual(struct.unpack_from('>H',payload)[0],5)
        self.assertFalse(seq.decode(payload,3)['loops'])
        self.assertEqual(seq.decode(payload,4)['loops'],[0,240])
        self.assertEqual(seq.decode(payload,4)['notes'],[(0,240,0,60,110)])
    def test_original_bank_is_deterministic(self):
        self.assertEqual(music.drum('snare',44100),music.drum('snare',44100))
        self.assertTrue(all(abs(v)<=1 for v in music.waveform('crunch',401)))
        self.assertEqual(music.drum('cymbal',44100)[-1],0)
if __name__=='__main__': unittest.main()
