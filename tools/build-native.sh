#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/cd
stage_clear=${MF_LEVEL1_STAGE_CLEAR:-0}
[[ $stage_clear == 0 || $stage_clear == 1 ]] || exit 1
if [[ $stage_clear == 1 && ${MF_ARCADE_FX:-0} != 1 ]]; then echo 'Stage clear requires THE ONE arcade FX profile.' >&2; exit 1; fi
printf '%s\n' "$stage_clear" > build/level1-stage-clear-mode.txt
live=${MF_LIVE_CITY_PARALLAX:-0}
[[ $live == 0 || $live == 1 ]] || exit 1
if [[ $live == 1 && ${MF_CITY_CLEANUP:-0} != 1 ]]; then echo 'Live parallax requires cleanup.' >&2; exit 1; fi
gallery=${MF_SPRITE_GALLERY:-0}
[[ $gallery == 0 || $gallery == 1 ]] || { echo 'MF_SPRITE_GALLERY must be 0 or 1' >&2; exit 1; }
printf '%s\n' "$gallery" > build/gallery-mode.txt
vdp2=${MF_VDP2_STREET:-1}
[[ $vdp2 == 0 || $vdp2 == 1 ]] || { echo 'MF_VDP2_STREET must be 0 or 1' >&2; exit 1; }
printf '%s\n' "$vdp2" > build/vdp2-mode.txt
city=${MF_CITY_NEON:-0}
[[ $city == 0 || $city == 1 ]] || exit 1
if [[ $city == 1 && $vdp2 != 1 ]]; then echo 'City neon requires VDP2.' >&2; exit 1; fi
printf '%s\n' "$city" > build/city-neon-mode.txt
cleanup=${MF_CITY_CLEANUP:-0}
[[ $cleanup == 0 || $cleanup == 1 ]] || exit 1
if [[ $cleanup == 1 && $city != 1 ]]; then echo 'City cleanup requires neon stage.' >&2; exit 1; fi
printf '%s\n' "$cleanup" > build/city-cleanup-mode.txt
legacy=${MF_STREET_LEGACY_CHECK:-0}
[[ $legacy == 0 || $legacy == 1 ]] || { echo 'MF_STREET_LEGACY_CHECK must be 0 or 1' >&2; exit 1; }
printf '%s\n' "$legacy" > build/street-legacy-mode.txt
parallax=${MF_PARALLAX_DEMO:-0}
[[ $parallax == 0 || $parallax == 1 ]] || { echo 'MF_PARALLAX_DEMO must be 0 or 1' >&2; exit 1; }
if [[ $parallax == 1 && ( $vdp2 != 1 || $gallery != 1 || $legacy != 0 ) ]]; then
    echo 'Parallax preview requires MF_VDP2_STREET=1 MF_SPRITE_GALLERY=1 and the fixed display check.' >&2
    exit 1
fi
printf '%s\n' "$parallax" > build/parallax-mode.txt
animation=${MF_ANIMATION_PREVIEW:-0}
[[ $animation == 0 || $animation == 1 ]] || { echo 'MF_ANIMATION_PREVIEW must be 0 or 1' >&2; exit 1; }
if [[ $animation == 1 && ( $vdp2 != 1 || $gallery != 1 || $legacy != 0 ) ]]; then
    echo 'Animation study requires VDP2, gallery and the fixed display check.' >&2; exit 1
fi
printf '%s\n' "$animation" > build/animation-mode.txt
playable=${MF_PLAYABLE_ANIMATION:-0}
[[ $playable == 0 || $playable == 1 ]] || { echo 'MF_PLAYABLE_ANIMATION must be 0 or 1' >&2; exit 1; }
if [[ $playable == 1 && $animation != 1 ]]; then
    echo 'Playable animation requires the shared resident animation preview bank.' >&2; exit 1
fi
printf '%s\n' "$playable" > build/playable-animation-mode.txt
swagger=${MF_SWAGGER_WALK:-0}
[[ $swagger == 0 || $swagger == 1 ]] || { echo 'MF_SWAGGER_WALK must be 0 or 1' >&2; exit 1; }
if [[ $swagger == 1 && $playable != 1 ]]; then
    echo 'Swagger requires the playable shared character bank.' >&2; exit 1
fi
printf '%s\n' "$swagger" > build/swagger-mode.txt
original=${MF_ORIGINAL_THREE_WALK:-0}
knee=${MF_WALK_KNEE_LIFT:-0}
[[ $knee == 0 || $knee == 1 ]] || { echo 'MF_WALK_KNEE_LIFT must be 0 or 1' >&2; exit 1; }
slow=${MF_ORIGINAL_WALK_SLOW:-$knee}
[[ $original == 0 || $original == 1 ]] && [[ $slow == 0 || $slow == 1 ]] || { echo 'Original walk flags must be 0 or 1' >&2; exit 1; }
if [[ $original == 1 && ( $playable != 1 || $swagger != 0 ) ]] || [[ $slow == 1 && $original != 1 ]]; then
    echo 'Original three walk requires playable=1, swagger=0; slow requires original=1.' >&2; exit 1
fi
printf '%s\n' "$original" > build/original-three-mode.txt
printf '%s\n' "$slow" > build/original-walk-slow.txt
if [[ $knee == 1 && ( $original != 1 || $slow != 1 ) ]]; then
    echo 'Knee lift requires original three walk and Timing B (slow=1).' >&2; exit 1
fi
printf '%s\n' "$knee" > build/knee-lift-mode.txt
corporate=${MF_CORPORATE_PUNK:-0}
[[ $corporate == 0 || $corporate == 1 ]] || { echo 'MF_CORPORATE_PUNK must be 0 or 1' >&2; exit 1; }
if [[ $corporate == 1 && $knee != 1 ]]; then
    echo 'Corporate Punk review requires the locked knee-lift Timing B player configuration.' >&2; exit 1
fi
printf '%s\n' "$corporate" > build/corporate-mode.txt
refined=${MF_CORPORATE_REFINED:-0}
[[ $refined == 0 || $refined == 1 ]] || { echo 'MF_CORPORATE_REFINED must be0 or1' >&2; exit 1; }
if [[ $refined == 1 && $corporate != 1 ]]; then echo 'Refined artwork requires Corporate Punk integration.' >&2; exit 1; fi
printf '%s\n' "$refined" > build/corporate-refined-mode.txt
lighting=${MF_CORPORATE_LIGHTING:-0}
[[ $lighting == 0 || $lighting == 1 ]] || { echo 'MF_CORPORATE_LIGHTING must be0 or1' >&2; exit 1; }
if [[ $lighting == 1 && $refined != 1 ]]; then echo 'Soft lighting requires the approved refined enemy bank.' >&2; exit 1; fi
printf '%s\n' "$lighting" > build/corporate-lighting-mode.txt
cphq=${MF_CP_HQ_COMBAT:-0}
[[ $cphq == 0 || $cphq == 1 ]] || exit 1
if [[ $cphq == 1 && $lighting != 1 ]]; then echo 'HQ enemy combat requires approved lighting bank.' >&2; exit 1; fi
printf '%s\n' "$cphq" > build/corporate-hq-mode.txt
dash=${MF_DASH_ENABLED:-0}
[[ $dash == 0 || $dash == 1 ]] || { echo 'MF_DASH_ENABLED must be0 or1' >&2; exit 1; }
dash_preset=${MF_DASH_PRESET:-B}
case "$dash_preset" in A) dash_num=15;; B) dash_num=17;; *) echo 'MF_DASH_PRESET must be A or B' >&2; exit 1;; esac
if [[ $dash == 1 && $lighting != 1 ]]; then echo 'Dash review requires the approved soft-lighting/player configuration.' >&2; exit 1; fi
printf '%s\n' "$dash" > build/dash-mode.txt
printf '%s\n' "$dash_num" > build/dash-preset.txt
run_bat=${MF_RUN_BAT:-0}
[[ $run_bat == 0 || $run_bat == 1 ]] || exit 1
if [[ $run_bat == 1 && ( $dash != 1 || $dash_preset != B ) ]]; then echo 'Running bat requires approved dash preset B.' >&2; exit 1; fi
printf '%s\n' "$run_bat" > build/run-bat-mode.txt
visual=${MF_RUNNING_BAT_VISUALS:-0}
[[ $visual == 0 || $visual == 1 ]] || exit 1
if [[ $visual == 1 && $run_bat != 1 ]]; then echo 'Bat visuals require approved running bat mode.' >&2; exit 1; fi
printf '%s\n' "$visual" > build/running-bat-visual-mode.txt
combat=${MF_COMBAT_ANIMATION:-0}
[[ $combat == 0 || $combat == 1 ]] || exit 1
if [[ $combat == 1 && ( $visual != 1 || $playable != 1 ) ]]; then echo 'Combat prototype requires running-bat visuals and playable animation.' >&2; exit 1; fi
printf '%s\n' "$combat" > build/combat-animation-mode.txt
momentum=${MF_BAT_MOMENTUM:-0}
[[ $momentum == 0 || $momentum == 1 ]] || exit 1
if [[ $momentum == 1 && $combat != 1 ]]; then echo 'Planted slide build requires the combat prototype.' >&2; exit 1; fi
printf '%s\n' "$momentum" > build/bat-momentum-mode.txt
sequence=${MF_ATTACK_SEQUENCE:-0}
[[ $sequence == 0 || $sequence == 1 ]] || exit 1
if [[ $sequence == 1 && $momentum != 1 ]]; then echo 'Attack sequencing requires the validated planted slide.' >&2; exit 1; fi
printf '%s\n' "$sequence" > build/attack-sequence-mode.txt
jab=${MF_JAB_COHESION:-0}
[[ $jab == 0 || $jab == 1 ]] || exit 1
if [[ $jab == 1 && $sequence != 1 ]]; then echo 'Jab review requires the validated attack sequencing build.' >&2; exit 1; fi
printf '%s\n' "$jab" > build/jab-cohesion-mode.txt
hq_jump=${MF_HQ_JUMP:-0}
[[ $hq_jump == 0 || $hq_jump == 1 ]] || exit 1
printf "%s\n" "$hq_jump" > build/hq-jump-mode.txt
hq_torch=${MF_HQ_TORCH:-0}
[[ $hq_torch == 0 || $hq_torch == 1 ]] || exit 1
if [[ $hq_torch == 1 && $jab != 1 ]]; then echo "HQ torch requires the approved jab build." >&2; exit 1; fi
printf "%s\n" "$hq_torch" > build/hq-torch-mode.txt
if [[ $hq_jump == 1 && $hq_torch != 1 ]]; then echo "HQ jump requires the validated HQ torch build." >&2; exit 1; fi
player_hurt=${MF_PLAYER_HURT:-0}
[[ $player_hurt == 0 || $player_hurt == 1 ]] || exit 1
if [[ $player_hurt == 1 && ( $cphq != 1 || $hq_jump != 1 || $combat != 1 || $sequence != 1 || $visual != 1 || $jab != 1 ) ]]; then echo 'Player hurt test requires latest HQ enemy/jump baseline.' >&2; exit 1; fi
printf '%s\n' "$player_hurt" > build/player-hurt-mode.txt
player_death=${MF_PLAYER_DEATH:-0}
[[ $player_death == 0 || $player_death == 1 ]] || exit 1
if [[ $player_death == 1 && $player_hurt != 1 ]]; then echo 'Player death requires approved HQ hurt.' >&2; exit 1; fi
printf '%s\n' "$player_death" > build/player-death-mode.txt
denim=${MF_CHUCK_DENIM_CLEANUP:-0}
[[ $denim == 0 || $denim == 1 ]] || exit 1
if [[ $denim == 1 && $player_death != 1 ]]; then echo 'Chuck cleanup requires approved HQ hurt/death profile.' >&2; exit 1; fi
printf '%s\n' "$denim" > build/chuck-denim-mode.txt
combo=${MF_PUNCH_COMBO:-0}
[[ $combo == 0 || $combo == 1 ]] || exit 1
if [[ $combo == 1 && ( $jab != 1 || ${MF_FAST_RUNNING_BAT:-0} != 1 || $player_death != 1 ) ]]; then echo 'Combo requires latest fast-bat HQ build.' >&2; exit 1; fi
printf '%s\n' "$combo" > build/punch-combo-mode.txt
fast_bat=${MF_FAST_RUNNING_BAT:-0}
[[ $fast_bat == 0 || $fast_bat == 1 ]] || exit 1
if [[ $fast_bat == 1 && ( $sequence != 1 || $run_bat != 1 || $player_death != 1 ) ]]; then echo 'Fast bat requires the full approved HQ profile.' >&2; exit 1; fi
printf '%s\n' "$fast_bat" > build/fast-bat-mode.txt
waist=${MF_PLAYER_RUN_WAIST:-0}
[[ $waist == 0 || $waist == 1 ]] || exit 1
if [[ $waist == 1 && $denim != 1 ]]; then echo 'Run waist fix requires approved Chuck denim profile.' >&2; exit 1; fi
printf '%s\n' "$waist" > build/run-waist-mode.txt
preserve_audio=${MF_PRESERVE_AUDIO:-$jab}
[[ $preserve_audio == 0 || $preserve_audio == 1 ]] || exit 1
if [[ $jab == 1 && $preserve_audio != 1 ]]; then echo 'Jab milestone must preserve existing audio assets.' >&2; exit 1; fi
printf '%s\n' "$preserve_audio" > build/preserve-audio-mode.txt
arcade_fx=${MF_ARCADE_FX:-0}
[[ $arcade_fx == 0 || $arcade_fx == 1 ]] || exit 1
if [[ $arcade_fx == 1 && ( $combo != 1 || $live != 1 || $cleanup != 1 || $preserve_audio != 1 ) ]]; then
    echo 'Arcade FX requires the complete HQ gameplay/parallax + preserved SFX2 profile.' >&2; exit 1
fi
printf '%s\n' "$arcade_fx" > build/arcade-fx-mode.txt
python3 tools/build-street.py
python3 tools/build-parallax.py
if [[ $preserve_audio == 1 ]]; then
    python3 tools/check-preserved-audio.py
else
    echo "Public builds require MF_PRESERVE_AUDIO=1; music authoring stays private." >&2
    exit 1
fi
build_commit=${MF_BUILD_COMMIT:-source-archive}
build_branch=${MF_BUILD_BRANCH:-source-archive}
[[ $build_commit =~ ^[0-9a-f]{40}$ || $build_commit == source-archive ]]
printf '%s\n' "$live" > build/live-city-mode.txt
printf '#define MF_BUILD_COMMIT "%s"\n' "$build_commit" > build/build-info.h
printf '#define MF_LEVEL1_STAGE_CLEAR %s\n' "$stage_clear" >> build/build-info.h
printf '#define MF_ARCADE_FX %s\n' "$arcade_fx" >> build/build-info.h
printf '#define MF_SPRITE_GALLERY %s\n' "$gallery" >> build/build-info.h
printf '#define MF_VDP2_STREET %s\n' "$vdp2" >> build/build-info.h
printf '#define MF_CITY_NEON %s\n' "$city" >> build/build-info.h
printf '#define MF_LIVE_CITY_PARALLAX %s\n' "$live" >> build/build-info.h
printf '#define MF_CITY_CLEANUP %s\n' "$cleanup" >> build/build-info.h
printf '#define MF_STREET_LEGACY_CHECK %s\n' "$legacy" >> build/build-info.h
printf '#define MF_PARALLAX_DEMO %s\n' "$parallax" >> build/build-info.h
printf '#define MF_ANIMATION_PREVIEW %s\n' "$animation" >> build/build-info.h
printf '#define MF_PLAYABLE_ANIMATION %s\n' "$playable" >> build/build-info.h
printf '#define MF_SWAGGER_WALK %s\n' "$swagger" >> build/build-info.h
printf '#define MF_ORIGINAL_THREE_WALK %s\n' "$original" >> build/build-info.h
printf '#define MF_ORIGINAL_WALK_SLOW %s\n' "$slow" >> build/build-info.h
printf '#define MF_WALK_KNEE_LIFT %s\n' "$knee" >> build/build-info.h
printf '#define MF_CORPORATE_PUNK %s\n' "$corporate" >> build/build-info.h
printf '#define MF_PLAYER_DEATH %s\n' "$player_death" >> build/build-info.h
printf '#define MF_PLAYER_HURT %s\n' "$player_hurt" >> build/build-info.h
printf '#define MF_CP_HQ_COMBAT %s\n' "$cphq" >> build/build-info.h
printf '#define MF_CORPORATE_REFINED %s\n' "$refined" >> build/build-info.h
printf '#define MF_CORPORATE_LIGHTING %s\n' "$lighting" >> build/build-info.h
printf '#define MF_HQ_JUMP %s\n' "$hq_jump" >> build/build-info.h
printf '#define MF_HQ_TORCH %s\n' "$hq_torch" >> build/build-info.h
printf '#define MF_PUNCH_COMBO %s\n' "$combo" >> build/build-info.h
printf '#define MF_FAST_RUNNING_BAT %s\n' "$fast_bat" >> build/build-info.h
printf '#define MF_JAB_COHESION %s\n' "$jab" >> build/build-info.h
printf '#define MF_ATTACK_SEQUENCE %s\n' "$sequence" >> build/build-info.h
printf '#define MF_BAT_MOMENTUM %s\n' "$momentum" >> build/build-info.h
printf '#define MF_COMBAT_ANIMATION %s\n' "$combat" >> build/build-info.h
printf '#define MF_RUNNING_BAT_VISUALS %s\n' "$visual" >> build/build-info.h
printf '#define MF_RUN_BAT %s\n' "$run_bat" >> build/build-info.h
printf '#define MF_DASH_ENABLED %s\n#define MF_DASH_PRESET %s\n' "$dash" "$dash_num" >> build/build-info.h
sha256sum src/*.c src/*.h make/saturn.mk assets/cd/* assets/music/config.json tools/music.py tools/custom_sfx.py tools/midi.py tools/seq.py third_party/mid2seq/*.c third_party/mid2seq/*.py > build/SOURCE-SHA256SUMS.txt
sha256sum build/level1-stage-clear-mode.txt >> build/SOURCE-SHA256SUMS.txt
sha256sum build/gallery-mode.txt >> build/SOURCE-SHA256SUMS.txt
sha256sum build/vdp2-mode.txt assets/vdp2/* tools/build-street.py >> build/SOURCE-SHA256SUMS.txt
sha256sum build/street-legacy-mode.txt >> build/SOURCE-SHA256SUMS.txt
if [[ $gallery == 1 ]]; then
    sha256sum assets/gallery/* >> build/SOURCE-SHA256SUMS.txt
fi
sha256sum build/parallax-mode.txt assets/parallax/* tools/build-parallax.py >> build/SOURCE-SHA256SUMS.txt
sha256sum build/knee-lift-mode.txt >> build/SOURCE-SHA256SUMS.txt
if [[ $knee == 1 ]]; then sha256sum assets/knee-lift/overrides/*.TGA assets/knee-lift/manifest.json tools/build-knee-lift.py >> build/SOURCE-SHA256SUMS.txt; fi
sha256sum build/original-three-mode.txt build/original-walk-slow.txt assets/original-three-walk/manifest.json tools/build-original-three.py >> build/SOURCE-SHA256SUMS.txt
sha256sum build/swagger-mode.txt >> build/SOURCE-SHA256SUMS.txt
if [[ $swagger == 1 ]]; then
    sha256sum assets/swagger-walk/*.TGA assets/swagger-walk/manifest.json tools/build-swagger-walk.py >> build/SOURCE-SHA256SUMS.txt
fi
sha256sum build/playable-animation-mode.txt >> build/SOURCE-SHA256SUMS.txt
sha256sum build/animation-mode.txt >> build/SOURCE-SHA256SUMS.txt
if [[ $animation == 1 ]]; then
    sha256sum assets/animation-study/*.TGA assets/animation-study/manifest.json tools/build-animation-study.py assets/animation-polish/*.TGA assets/animation-polish/manifest.json tools/build-animation-polish.py >> build/SOURCE-SHA256SUMS.txt
fi
sha256sum build/jab-cohesion-mode.txt build/preserve-audio-mode.txt build/attack-sequence-mode.txt build/bat-momentum-mode.txt build/combat-animation-mode.txt build/running-bat-visual-mode.txt build/run-bat-mode.txt build/dash-mode.txt build/dash-preset.txt build/corporate-lighting-mode.txt build/corporate-refined-mode.txt build/corporate-mode.txt >> build/SOURCE-SHA256SUMS.txt
if [[ $corporate == 1 ]]; then sha256sum assets/corporate-punk-animation/*.TGA assets/corporate-punk-animation/manifest.json >> build/SOURCE-SHA256SUMS.txt; fi
if [[ $refined == 1 ]]; then sha256sum assets/corporate-punk-refined/*.TGA assets/corporate-punk-refined/manifest.json >> build/SOURCE-SHA256SUMS.txt; fi
if [[ $lighting == 1 ]]; then sha256sum assets/corporate-punk-lighting/*.TGA assets/corporate-punk-lighting/manifest.json >> build/SOURCE-SHA256SUMS.txt; fi
if [[ $run_bat == 1 ]]; then sha256sum assets/running/*.TGA assets/running/manifest.json >> build/SOURCE-SHA256SUMS.txt; fi
if [[ $combat == 1 ]]; then
    combat_dir=assets/combat-animation
    if [[ $momentum == 1 ]]; then combat_dir=assets/bat-momentum; fi
    if [[ $sequence == 1 ]]; then combat_dir=assets/attack-sequence; fi
    sha256sum "$combat_dir"/*.TGA "$combat_dir"/manifest.json >> build/SOURCE-SHA256SUMS.txt
fi
if [[ $visual == 1 ]]; then sha256sum assets/running-bat-visual/*.TGA assets/running-bat-visual/manifest.json >> build/SOURCE-SHA256SUMS.txt; fi
sha256sum build/hq-jump-mode.txt >> build/SOURCE-SHA256SUMS.txt
if [[ $hq_jump == 1 ]]; then sha256sum assets/hq-jump/*.TGA assets/hq-jump/manifest.json >> build/SOURCE-SHA256SUMS.txt; fi
sha256sum build/hq-torch-mode.txt >> build/SOURCE-SHA256SUMS.txt
if [[ $hq_torch == 1 ]]; then sha256sum assets/hq-torch/*.TGA assets/hq-torch/manifest.json >> build/SOURCE-SHA256SUMS.txt; fi
if [[ $cphq == 1 ]]; then
    sha256sum assets/corporate-punk-hq-combat/*.TGA assets/corporate-punk-hq-combat/manifest.json build/corporate-hq-mode.txt >> build/SOURCE-SHA256SUMS.txt
fi
if [[ $player_hurt == 1 ]]; then sha256sum assets/player-hurt/*.TGA assets/player-hurt/manifest.json build/player-hurt-mode.txt >> build/SOURCE-SHA256SUMS.txt; fi
if [[ $player_death == 1 ]]; then sha256sum assets/player-death/*.TGA assets/player-death/manifest.json build/player-death-mode.txt >> build/SOURCE-SHA256SUMS.txt; fi
if [[ $denim == 1 ]]; then sha256sum assets/chuck-denim-cleanup/*.TGA assets/chuck-denim-cleanup/manifest.json build/chuck-denim-mode.txt >> build/SOURCE-SHA256SUMS.txt; fi
if [[ $waist == 1 ]]; then sha256sum assets/run-waist-seam/*.TGA assets/run-waist-seam/manifest.json build/run-waist-mode.txt >> build/SOURCE-SHA256SUMS.txt; fi
if [[ $fast_bat == 1 ]]; then sha256sum build/fast-bat-mode.txt >> build/SOURCE-SHA256SUMS.txt; fi
if [[ $combo == 1 ]]; then sha256sum build/punch-combo-mode.txt assets/punch-combo/*.TGA assets/punch-combo/manifest.json >> build/SOURCE-SHA256SUMS.txt; fi
sha256sum build/city-neon-mode.txt >> build/SOURCE-SHA256SUMS.txt
if [[ $city == 1 ]]; then sha256sum assets/city-neon/*.BIN assets/city-neon/manifest.json tools/build-city-neon.py >> build/SOURCE-SHA256SUMS.txt; fi
sha256sum build/city-cleanup-mode.txt >> build/SOURCE-SHA256SUMS.txt
if [[ $cleanup == 1 ]]; then sha256sum assets/city-cleanup/* tools/build-city-cleanup.py >> build/SOURCE-SHA256SUMS.txt; fi
sha256sum build/live-city-mode.txt >> build/SOURCE-SHA256SUMS.txt
if [[ $live == 1 ]]; then sha256sum assets/city-gameplay-parallax/* >> build/SOURCE-SHA256SUMS.txt; fi
sha256sum build/arcade-fx-mode.txt assets/arcade-fx/* >> build/SOURCE-SHA256SUMS.txt
source_hash=$(sha256sum build/SOURCE-SHA256SUMS.txt | cut -d' ' -f1)
printf '#define MF_BUILD_SOURCE "%s"\n' "$source_hash" >> build/build-info.h
printf 'Game: MULLET FORCE\nScene: Neon District playable prototype\nCommit: %s\nBranch: %s\nSDK: 556d081146211b6a1cfa6591d70f9487d406758b\n' \
    "$build_commit" "$build_branch" > build/BUILD-INFO.txt
printf 'Source SHA256: %s\n' "$source_hash" >> build/BUILD-INFO.txt
printf 'Level 1 stage clear: %s\n' "$stage_clear" >> build/BUILD-INFO.txt
printf 'Arcade dual FX: %s\n' "$arcade_fx" >> build/BUILD-INFO.txt
printf 'City neon candidate: %s\n' "$city" >> build/BUILD-INFO.txt
printf 'Live gameplay parallax: %s\n' "$live" >> build/BUILD-INFO.txt
printf 'City cleanup candidate: %s\n' "$cleanup" >> build/BUILD-INFO.txt
printf 'Sprite gallery: %s\n' "$gallery" >> build/BUILD-INFO.txt
printf 'VDP2 street: %s\n' "$vdp2" >> build/BUILD-INFO.txt
printf 'Legacy display check (expected failure): %s\n' "$legacy" >> build/BUILD-INFO.txt
printf 'Parallax preview: %s\n' "$parallax" >> build/BUILD-INFO.txt
printf 'Animation preview: %s\n' "$animation" >> build/BUILD-INFO.txt
printf 'Playable animation: %s\n' "$playable" >> build/BUILD-INFO.txt
cp docs/animation/playable.md build/PLAYABLE-ANIMATION.md
printf 'Swagger walk: %s\n' "$swagger" >> build/BUILD-INFO.txt
cp docs/animation/swagger.md build/SWAGGER-WALK.md
cp docs/animation/original-three.md build/ORIGINAL-THREE-WALK.md
cp docs/animation/knee-lift.md build/KNEE-LIFT.md
printf 'Double-tap dash: %s\nDash preset: %s (%s/10)\n' "$dash" "$dash_preset" "$dash_num" >> build/BUILD-INFO.txt
cp docs/double-tap-dash.md build/DASH-README.md
printf 'Running animation / running bat: %s\n' "$run_bat" >> build/BUILD-INFO.txt
rm -f build/cd/RN[0-9][0-9].TGA
if [[ $run_bat == 1 ]]; then
    cp assets/running/*.TGA build/cd/
    cp docs/running-bat.md build/RUNNING-BAT-README.md
    cp docs/alternating-stride.md build/STRIDE-README.md
    cp docs/leg-artifact-fix.md build/LEG-ARTIFACT-README.md
fi
rm -rf build/cd/COMBAT
if [[ $combat == 1 ]]; then
    mkdir -p build/cd/COMBAT
    cp "$combat_dir"/*.TGA build/cd/COMBAT/
    cp docs/combat-animation-prototype.md build/COMBAT-ANIMATION-README.md
fi
if [[ $momentum == 1 ]]; then cp docs/bat-strike-momentum.md build/BAT-MOMENTUM-README.md; fi
if [[ $sequence == 1 ]]; then cp docs/combat-attack-sequencing.md build/ATTACK-SEQUENCE-README.md; fi
if [[ $jab == 1 ]]; then cp docs/jab-cohesion-input-bat-cleanup.md build/JAB-COHESION-README.md; fi
printf 'Jab cohesion/repeat: %s\nPreserved audio (not regenerated): %s\n' "$jab" "$preserve_audio" >> build/BUILD-INFO.txt
printf 'Attack sequencing: %s\n' "$sequence" >> build/BUILD-INFO.txt
printf 'Planted bat momentum: %s\n' "$momentum" >> build/BUILD-INFO.txt
printf 'Combat key-pose prototype: %s\n' "$combat" >> build/BUILD-INFO.txt
printf 'Running bat visuals: %s\n' "$visual" >> build/BUILD-INFO.txt
rm -f build/cd/RBV*.TGA
if [[ $visual == 1 ]]; then
    cp assets/running-bat-visual/*.TGA build/cd/
    cp docs/running-bat-visual.md build/RUNNING-BAT-VISUAL-README.md
fi
printf 'Corporate Punk integration: %s\nCorporate Punk refined: %s\nCorporate Punk soft lighting: %s\n' "$corporate" "$refined" "$lighting" >> build/BUILD-INFO.txt
rm -f build/cd/CP[0-9][0-9].TGA
rm -rf build/corporate-punk-review
if [[ $corporate == 1 ]]; then
    if [[ $lighting == 1 ]]; then cp assets/corporate-punk-lighting/*.TGA build/cd/; elif [[ $refined == 1 ]]; then cp assets/corporate-punk-refined/*.TGA build/cd/; else cp assets/corporate-punk-animation/*.TGA build/cd/; fi
fi
printf 'Walk knee lift: %s\n' "$knee" >> build/BUILD-INFO.txt
printf 'Original three walk: %s\nOriginal slow timing: %s\n' "$original" "$slow" >> build/BUILD-INFO.txt
if [[ $cphq == 1 ]]; then
    cp assets/corporate-punk-hq-combat/*.TGA build/cd/
fi
printf 'Corporate Punk HQ combat: %s\n' "$cphq" >> build/BUILD-INFO.txt
rm -f build/cd/PH[0-9][0-9].TGA build/cd/RC[01].TGA
rm -rf build/cd/HQHURT
if [[ $player_hurt == 1 ]]; then
    mkdir -p build/cd/HQHURT
    cp assets/player-hurt/PH*.TGA build/cd/HQHURT/
    cp assets/player-hurt/RC*.TGA build/cd/
    cp assets/player-hurt/CT*.TGA build/cd/COMBAT/
fi
printf 'HQ player hurt / Chuck cleanup: %s\n' "$player_hurt" >> build/BUILD-INFO.txt
rm -rf build/cd/HQDEATH
rm -f build/cd/RD[01].TGA build/cd/COMBAT/DT[01].TGA
if [[ $player_death == 1 ]]; then
    mkdir -p build/cd/HQDEATH
    cp assets/player-death/PD*.TGA build/cd/HQDEATH/
    cp assets/player-death/RD*.TGA build/cd/
    cp assets/player-death/DT*.TGA build/cd/COMBAT/
fi
printf 'HQ player death / final Chuck fix: %s\n' "$player_death" >> build/BUILD-INFO.txt
if [[ $denim == 1 ]]; then
    cp assets/chuck-denim-cleanup/RD*.TGA assets/chuck-denim-cleanup/RN22.TGA build/cd/
    cp assets/chuck-denim-cleanup/DT*.TGA assets/chuck-denim-cleanup/CA55.TGA build/cd/COMBAT/
fi
printf 'Chuck denim cleanup: %s\n' "$denim" >> build/BUILD-INFO.txt
if [[ $waist == 1 ]]; then
    cp assets/run-waist-seam/RN*.TGA build/cd/
    cp assets/run-waist-seam/CA*.TGA build/cd/COMBAT/
fi
if [[ $combo == 1 ]]; then
    mkdir -p build/cd/COMBO
    cp assets/punch-combo/XC*.TGA build/cd/COMBO/
fi
printf 'Jab jab cross combo: %s\n' "$combo" >> build/BUILD-INFO.txt
printf 'Player running waist seam: %s\nFast horizontal running bat: %s\n' "$waist" "$fast_bat" >> build/BUILD-INFO.txt
cp src/*.c src/*.h build/
cp docs/native-music.md build/NATIVE-MUSIC.md
cp docs/custom-combat-sfx.md build/CUSTOM-COMBAT-SFX.md
printf "Custom combat SFX: original WAVs; independent player ports 5/6; preserved music\n" >> build/BUILD-INFO.txt
cp docs/torch-update.md build/UPDATE-NOTES.md
cp assets/music/report.json build/music-report.json
cp assets/music/config.json build/music-mapping.json
cp third_party/mid2seq/LICENSE build/MID2SEQ-LICENSE.txt
cp assets/music/drum-diagnosis.json build/drum-diagnosis.json
printf "HQ jump: %s\n" "$hq_jump" >> build/BUILD-INFO.txt
rm -rf build/cd/HQJUMP
if [[ $hq_jump == 1 ]]; then mkdir -p build/cd/HQJUMP; cp assets/hq-jump/*.TGA build/cd/HQJUMP/; fi
printf "HQ torch: %s\n" "$hq_torch" >> build/BUILD-INFO.txt
rm -rf build/cd/HQTORCH
if [[ $hq_torch == 1 ]]; then mkdir -p build/cd/HQTORCH; cp assets/hq-torch/*.TGA build/cd/HQTORCH/; fi
# Original runtime TGA and PCM assets.
if [[ -d assets/cd ]]; then cp -a assets/cd/. build/cd/; fi
for name in GB0 GB1 GB2 GC0 GC1 GC2; do rm -f "build/cd/$name.TGA"; done
if [[ $gallery == 1 ]]; then cp assets/gallery/*.TGA build/cd/; fi
for name in STCELLS STMAP STPAL; do rm -f "build/cd/$name.BIN"; done
if [[ $vdp2 == 1 ]]; then cp assets/vdp2/*.BIN build/cd/; fi
for name in PCHUNK PSKY PSMAP; do rm -f "build/cd/$name.BIN"; done
rm -f build/PARALLAX-README.md build/PARALLAX-RUNTIME.json
if [[ $parallax == 1 ]]; then
    cp assets/parallax/*.BIN build/cd/
    cp docs/parallax-demo.md build/PARALLAX-README.md
    cp docs/parallax-runtime-validation.json build/PARALLAX-RUNTIME.json
fi
# City candidate is a separate VDP2-only override. Keep original ST assets and
# immutable manifests intact; translated preview chunks use the same map layout.
rm -f build/cd/CICELL.BIN build/cd/CIMAP.BIN build/cd/CIPAL.BIN
if [[ $city == 1 ]]; then
    cp assets/city-neon/CICELL.BIN assets/city-neon/CIMAP.BIN assets/city-neon/CIPAL.BIN build/cd/
    if [[ $parallax == 1 ]]; then
        cp assets/city-neon/CICHUNK.BIN build/cd/PCHUNK.BIN
        cp assets/city-neon/CISKY.BIN build/cd/PSKY.BIN
    fi
fi
if [[ $cleanup == 1 ]]; then
    cp assets/city-cleanup/CICELL.BIN assets/city-cleanup/CIMAP.BIN assets/city-cleanup/CIPAL.BIN build/cd/
    cp assets/city-cleanup/DR*.TGA build/cd/
    if [[ $parallax == 1 ]]; then
        cp assets/city-cleanup/CICHUNK.BIN build/cd/PCHUNK.BIN
        cp assets/city-cleanup/CISKY.BIN build/cd/PSKY.BIN
    fi
fi
rm -f build/cd/LCSKY.BIN build/cd/LCMAP.BIN
if [[ $live == 1 ]]; then cp assets/city-gameplay-parallax/*.BIN build/cd/; fi
rm -f build/cd/AB*.TGA build/cd/AC*.TGA build/cd/P[0-9][0-9][0-9].TGA
rm -f build/cd/S[0-9][0-9][0-9].TGA
if [[ $swagger == 1 ]]; then cp assets/swagger-walk/*.TGA build/cd/; fi
rm -rf build/animation-review
if [[ $animation == 1 ]]; then
    cp assets/animation-study/*.TGA assets/animation-polish/*.TGA build/cd/
    if [[ $knee == 1 ]]; then cp assets/knee-lift/overrides/*.TGA build/cd/; fi
fi
rm -f build/cd/EXPLODE.TGA
if [[ $arcade_fx == 1 ]]; then cp assets/arcade-fx/EXPLODE.TGA build/cd/; fi
make -C build -f ../make/saturn.mk MAKEFILE=../make/saturn.mk -j2 MF_LEVEL1_STAGE_CLEAR="$stage_clear" MF_PUNCH_COMBO="$combo" MF_FAST_RUNNING_BAT="$fast_bat" MF_JAB_COHESION="$jab" MF_ATTACK_SEQUENCE="$sequence" MF_BAT_MOMENTUM="$momentum" MF_COMBAT_ANIMATION="$combat" MF_RUNNING_BAT_VISUALS="$visual" MF_RUN_BAT="$run_bat" MF_DASH_ENABLED="$dash" MF_DASH_PRESET="$dash_num" game.iso
cp build/game.iso build/mullet-force.bin
cat > build/mullet-force.cue <<'CUE'
FILE "mullet-force.bin" BINARY
  TRACK 01 MODE1/2048
    INDEX 01 00:00:00
    POSTGAP 00:02:00
CUE
test -s build/game.elf
test "$(head -c 16 build/mullet-force.bin)" = 'SEGA SEGASATURN '
cmp build/game.raw build/cd/0.bin
isoinfo -i build/mullet-force.bin -f | grep -Fx '/0.BIN;1'
(cd build && sha256sum mullet-force.bin mullet-force.cue game.elf > SHA256SUMS.txt)
printf 'Built build/mullet-force.cue and build/mullet-force.bin\n'
