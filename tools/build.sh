#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $(uname -m) == x86_64 ]] || { echo 'The pinned compiler requires x86-64 Linux.' >&2; exit 1; }
bash tools/setup.sh
export MF_BUILD_COMMIT="$(git rev-parse --verify HEAD 2>/dev/null || printf source-archive)"
export MF_BUILD_BRANCH="${GITHUB_HEAD_REF:-$(git symbolic-ref -q --short HEAD 2>/dev/null || printf source-archive)}"
if [[ ${1:-} == --native ]]; then
    bash tools/build-native.sh
    exit
fi
[[ $# == 0 ]] || { echo 'Usage: bash tools/build.sh [--native]' >&2; exit 1; }
command -v docker >/dev/null && docker info >/dev/null 2>&1 || {
    echo 'Docker daemon unavailable. Run bash tools/bootstrap.sh, then make native.' >&2; exit 1;
}
# Retain inherited Docker credentials, proxy settings and certificate verification.
build_hosts=()
if [[ -n ${HTTP_PROXY:-} ]]; then
    proxy_host=${HTTP_PROXY#*://}; proxy_host=${proxy_host##*@}; proxy_host=${proxy_host%%:*}
    proxy_ip=$(getent ahostsv4 "$proxy_host" | awk 'NR == 1 {print $1}')
    if [[ -n "$proxy_ip" ]]; then build_hosts+=(--add-host "$proxy_host:$proxy_ip"); fi
fi
docker build "${build_hosts[@]}" --build-arg HTTP_PROXY --build-arg HTTPS_PROXY --build-arg NO_PROXY \
    -t mullet-force-build -f tools/Dockerfile .
docker run --rm -e MF_LIVE_CITY_PARALLAX -e MF_CITY_CLEANUP -e MF_CITY_NEON -e MF_PUNCH_COMBO -e MF_FAST_RUNNING_BAT -e MF_BUILD_COMMIT -e MF_BUILD_BRANCH -e MF_SPRITE_GALLERY -e MF_VDP2_STREET -e MF_STREET_LEGACY_CHECK -e MF_PARALLAX_DEMO -e MF_ANIMATION_PREVIEW -e MF_PLAYABLE_ANIMATION -e MF_SWAGGER_WALK -e MF_ORIGINAL_THREE_WALK -e MF_ORIGINAL_WALK_SLOW -e MF_WALK_KNEE_LIFT -e MF_CORPORATE_PUNK -e MF_CORPORATE_REFINED -e MF_CORPORATE_LIGHTING -e MF_PLAYER_RUN_WAIST -e MF_CHUCK_DENIM_CLEANUP -e MF_PLAYER_DEATH -e MF_PLAYER_HURT -e MF_CP_HQ_COMBAT -e MF_HQ_JUMP -e MF_HQ_TORCH -e MF_JAB_COHESION -e MF_PRESERVE_AUDIO -e MF_ATTACK_SEQUENCE -e MF_BAT_MOMENTUM -e MF_COMBAT_ANIMATION -e MF_RUNNING_BAT_VISUALS -e MF_RUN_BAT -e MF_DASH_ENABLED -e MF_DASH_PRESET --user "$(id -u):$(id -g)" \
    -v "$PWD:/work" mullet-force-build bash tools/build-native.sh
