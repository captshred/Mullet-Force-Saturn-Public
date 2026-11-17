#!/usr/bin/env python3
"""Compile a separate real-driver stress image; never replace the game build."""
from pathlib import Path
import shutil,subprocess
R=Path(__file__).resolve().parents[1];H=R/'build/refinement-driver-stress';sdk=R/'.deps/joengine';H.mkdir(parents=True,exist_ok=True);(H/'cd').mkdir(exist_ok=True)
shutil.copyfile(R/'tests/level1_refinement/driver-stress.c',H/'main.c');shutil.copyfile(R/'src/music.c',H/'music.c')
for name in ['CUSTOM.MAP','STAGE.SEQ','STAGE.TON','FX.SEQ','FX.TON']:shutil.copyfile(R/'assets/cd'/name,H/'cd'/name)
iso=shutil.which('genisoimage');assert iso,'genisoimage required'
(H/'Makefile').write_text(f'''JO_ENGINE_SRC_DIR = {sdk}/jo_engine
COMPILER_DIR = {sdk}/Compiler
SRCS = main.c music.c
JO_COMPILE_USING_SGL = 1
JO_COMPILE_WITH_FS_MODULE = 1
JO_COMPILE_WITH_AUDIO_MODULE = 1
JO_COMPILE_WITH_3D_MODULE = 0
JO_COMPILE_WITH_TGA_MODULE = 1
JO_COMPILE_WITH_DUAL_CPU_MODULE = 0
JO_COMPILE_WITH_RAM_CARD_MODULE = 0
JO_COMPILE_WITH_PRINTF_MODULE = 1
JO_DEBUG = 0
JO_NTSC = 1
include $(COMPILER_DIR)/COMMON/jo_engine_makefile
LIBS += $(COMPILER_DIR)/COMMON/SGL_302j/LIB_ELF/LIBSND.A
CCFLAGS += -I{R}/src -DMF_HQ_TORCH=1 -DMF_PLAYER_HURT=1 -DMF_PLAYER_DEATH=1
MKISOFS = {iso}
MKISOFS_FLAGS = -quiet -sysid "SEGA SATURN" -volid "MULLET_STRESS" -generic-boot $(IPFILE) -full-iso9660-filenames -o $(TARGET2) $(ASSETS_DIR)
''')
subprocess.run(['make','-C',str(H),'-j2','MAKEFILE=Makefile','game.iso'],check=True)
(H/'game.cue').write_text('FILE "game.iso" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n')
