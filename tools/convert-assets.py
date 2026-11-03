#!/usr/bin/env python3
"""Small FFmpeg wrappers for future user-owned assets; no runtime assets bundled."""
from pathlib import Path
import argparse,os,shutil,subprocess,tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('kind',choices=('cdda','pcm','tga'))
parser.add_argument('source',type=Path)
parser.add_argument('destination',type=Path)
parser.add_argument('--rate',type=int,default=11025,help='PCM8 sample rate only (8000..44100)')
parser.add_argument('--force',action='store_true',help='Replace an existing destination')
args=parser.parse_args()
if not shutil.which('ffmpeg'): parser.error('Install ffmpeg with tools/bootstrap.sh')
if not args.source.is_file(): parser.error('Source file does not exist')
if args.destination.exists() and not args.force: parser.error('Destination exists; pass --force to replace it')
if args.source.resolve()==args.destination.resolve(): parser.error('Source and destination must differ')
if not 8000<=args.rate<=44100: parser.error('PCM rate must be 8000..44100 Hz')
args.destination.parent.mkdir(parents=True,exist_ok=True)
fd,name=tempfile.mkstemp(prefix='.convert-',dir=args.destination.parent);os.close(fd)
temporary=Path(name)
try:
 command=['ffmpeg','-v','error','-nostdin','-y','-i',str(args.source)]
 if args.kind=='cdda':
  command+=['-map','0:a:0','-ar','44100','-ac','2','-c:a','pcm_s16le','-f','s16le']
 elif args.kind=='pcm':
  command+=['-map','0:a:0','-ar',str(args.rate),'-ac','1','-c:a','pcm_s8','-f','s8']
 else:
  command+=['-map','0:v:0','-frames:v','1','-c:v','targa','-pix_fmt','bgr24','-rle','0','-f','image2']
 subprocess.run(command+[str(temporary)],check=True)
 if args.kind=='cdda':
  # BINARY CUE audio is interleaved little-endian signed PCM16. Zero-pad the
  # final partial CD sector, preserving all original samples and channel order.
  with temporary.open('ab') as output: output.write(bytes((-temporary.stat().st_size)%2352))
 elif args.kind=='pcm' and temporary.stat().st_size>65536:
  raise ValueError('PCM effect exceeds 64 KiB; use CDDA for music or shorten the effect')
 elif args.kind=='tga':
  header=temporary.read_bytes()[:18]
  if len(header)!=18 or header[2]!=2 or header[16]!=24:
   raise ValueError('Expected uncompressed true-color 24-bit TGA')
 temporary.replace(args.destination)
 print(f'{args.kind}: {args.destination} ({args.destination.stat().st_size} bytes)')
finally:
 temporary.unlink(missing_ok=True)
