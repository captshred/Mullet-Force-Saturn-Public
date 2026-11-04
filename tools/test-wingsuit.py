#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='mf-wingsuit-') as tmp:
 for name,sources,includes in [
  ('game',['tests/wingsuit_test.c','src/wingsuit.c'],['-Isrc']),
  ('runtime',['tests/wingsuit_runtime_test.c','src/wingsuit.c'],['-Itests/wingsuit_mock','-Isrc'])]:
  exe=str(Path(tmp)/name)
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',*includes,*sources,'-o',exe],cwd=R,check=True)
  subprocess.run([exe],cwd=R,check=True)
subprocess.run(['python3','tools/validate-wingsuit.py'],cwd=R,check=True)
subprocess.run(['python3','tests/wingsuit_disc_test.py'],cwd=R,check=True)
