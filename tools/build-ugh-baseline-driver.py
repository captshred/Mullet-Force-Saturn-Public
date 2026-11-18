#!/usr/bin/env python3
"""Same request schedule with exact prior transport/banks; diagnostic HUD stub only."""
from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[1];BASE='744053ba851c9da6b8953708f125313f177b7dcb'
s=(R/'tools/build-ugh-driver.py').read_text().replace("H=R/'build/ugh-driver'","H=R/'build/ugh-baseline-driver'")
s=s.replace("shutil.copyfile(R/'src/music.c',H/'music.c')", "(H/'music.c').write_bytes(subprocess.check_output(['git','show',BASE+':src/music.c'],cwd=R)+b'\\nint mf_music_protected(void){return 0;}\\n')\n(H/'music_data.h').write_bytes(subprocess.check_output(['git','show',BASE+':src/music_data.h'],cwd=R))")
s=s.replace("shutil.copyfile(R/'assets/cd'/name,H/'cd'/name)","(H/'cd'/name).write_bytes(subprocess.check_output(['git','show',BASE+':assets/cd/'+name],cwd=R))")
exec(compile(s,str(R/'tools/build-ugh-driver.py'),'exec'),dict(__file__=str(R/'tools/build-ugh-driver.py'),BASE=BASE))
