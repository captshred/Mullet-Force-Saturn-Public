#!/usr/bin/env bash
# Release gate: run only from a committed, clean source checkout.
set -euo pipefail
cd "$(dirname "$0")/.."
base=5ca590d774cc91d0ac1bb4ce6b325aa647b3dd59
git merge-base --is-ancestor "$base" HEAD
if git merge-base --is-ancestor dd3510d09ec7d91d988f2ace7c22d46d93c7bef0 HEAD 2>/dev/null; then
    echo 'Obsolete SFX feature ancestry is forbidden.' >&2; exit 1
fi
[[ -z $(git status --porcelain --untracked-files=all) ]] || { echo 'Release verification requires a clean Git tree.' >&2; exit 1; }
for path in src/wingsuit_audio.c src/wingsuit_audio_data.h tools/build-source-complete.sh assets/wingsuit/WMUSIC.MAP assets/wingsuit/WMUSIC.SEQ assets/wingsuit/WMUSIC.TON; do
    git ls-files --error-unmatch "$path" >/dev/null
    test -s "$path"
done
sha=$(git rev-parse HEAD)
python3 tools/validate-source-recovery.py
bash tools/setup.sh
make clean
bash tools/build-source-complete.sh
make test
make check
grep -Fx "Commit: $sha" build/BUILD-INFO.txt
printf '\nSource-complete recovery candidate; manual approval pending.\nSource commit: %s\n' "$sha" >> build/BUILD-INFO.txt
git ls-files -z | xargs -0 sha256sum > build/DEVELOPMENT-SOURCE-SHA256SUMS.txt
(cd build && sha256sum mullet-force.bin mullet-force.cue BUILD-INFO.txt DEVELOPMENT-SOURCE-SHA256SUMS.txt > CANONICAL-SHA256SUMS.txt && sha256sum --check CANONICAL-SHA256SUMS.txt)
[[ -z $(git status --porcelain --untracked-files=all) ]]
