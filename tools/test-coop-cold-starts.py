#!/usr/bin/env python3
"""Repeat the existing read-only cold-start/Level2 comparison on this candidate.
Pass the candidate BIN/CUE and game.elf as both phase1 and phase2 inputs.
LTO moved the runtime controller away from shooter; identify its phase beside
its own failed_reason diagnostic, rather than beside the large shooter pool.
"""
from pathlib import Path
source=(Path(__file__).with_name('test-ricky-playable-runtime.py')).read_text()
old="ws-256<v<ws";assert source.count(old)==1
source=source.replace(old,"abs(v-address(s,'_failed_reason'))<64")
exec(compile(source,str(Path(__file__).with_name('test-ricky-playable-runtime.py')),'exec'))
