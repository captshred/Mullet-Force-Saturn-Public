#!/usr/bin/env bash
# Rootless fallback for this Debian cloud image; retains the pinned Saturn SDK.
set -euo pipefail
cd "$(dirname "$0")/.."
bash tools/setup.sh
host_tools=/workspace/mf-host-tools
if ! command -v genisoimage >/dev/null && [[ ! -x $host_tools/usr/bin/genisoimage ]]; then
    # Use signed Debian metadata and apt's package hash verification. No sudo,
    # trust bypass, system package database changes or replacement compiler.
    . /etc/os-release
    [[ $ID == debian && $VERSION_CODENAME == trixie ]] || {
        echo 'Use tools/bootstrap.sh on other Debian/Ubuntu hosts.' >&2; exit 1;
    }
    mkdir -p "$host_tools/lists/partial" "$host_tools/cache/archives/partial" "$host_tools/packages"
    printf '%s\n' 'deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian trixie main' > "$host_tools/sources.list"
    apt_options=(-o Dir::Etc::main=- -o Dir::Etc::parts=-
        -o "Dir::Etc::sourcelist=$host_tools/sources.list" -o Dir::Etc::sourceparts=-
        -o "Dir::State::lists=$host_tools/lists" -o "Dir::Cache=$host_tools/cache"
        -o "APT::Sandbox::User=$(id -un)")
    /usr/bin/apt-get "${apt_options[@]}" update
    (cd "$host_tools/packages" && /usr/bin/apt-get "${apt_options[@]}" download genisoimage)
    for package in "$host_tools"/packages/genisoimage_*.deb; do dpkg-deb -x "$package" "$host_tools"; done
fi
export PATH="$host_tools/usr/bin:$PATH"
genisoimage --version
.deps/joengine/Compiler/LINUX/bin/sh-none-elf-gcc-8.2.0 --version | head -n 1
printf 'Use PATH=/workspace/mf-host-tools/usr/bin:$PATH make native on this host.\n'
