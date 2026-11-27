#!/usr/bin/env python3
"""Run the Noah boot sprite loader against staged files with host Jo mocks."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    loader = (ROOT / "src/main.c").read_text().split("static int depth_key", 1)[0]
    with tempfile.TemporaryDirectory(prefix="mf-production-resources-") as directory:
        work = Path(directory)
        source = work / "loader.c"
        source.write_text("#include <assert.h>\n" + loader + """
void audit_finish(void);
#ifndef MF_PRODUCTION_RESOURCE_CLEANUP
#define MF_PRODUCTION_RESOURCE_CLEANUP 0
#endif
int main(void)
{
    load_assets();
    assert(!asset_error && mf_enemy_bank_current() == &mf_ricky_bank_spec);
    assert(mf_enemy_bank_diagnostics()->peak_bytes ==
           (MF_PRODUCTION_RESOURCE_CLEANUP ? 380992u : 388928u));
    assert(jo_get_last_sprite_id() + 1 ==
           (MF_PRODUCTION_RESOURCE_CLEANUP ? 176 : 178));
    for (int pose = 0; pose < 25; ++pose)
        assert(mf_ricky_draw_pose(pose, 1, 100, 200, 200) ==
               (pose < (MF_PRODUCTION_RESOURCE_CLEANUP ? 23 : 25)));
    for (int actor = 0; actor < 2; ++actor)
        for (int pose = 18; pose < 22; ++pose)
            assert(mf_animation_draw_actor(actor, pose, 100, 200, -1, 200));
    audit_finish();
    return 0;
}
""")
        header = ROOT / "build/build-info.h"
        executable = work / "loader"
        subprocess.run([
            "cc", "-std=c99", "-ffunction-sections", "-fdata-sections",
            "-fsanitize=undefined", "-fno-sanitize-recover=all",
            "-include", str(header), "-Ibuild", "-Itests/enemy_banks", "-Isrc",
            str(source), "tests/enemy_banks/trace.c", "src/enemy_sprite_bank.c",
            "src/corporate_animation.c", "src/ricky_animation.c",
            "src/animation_preview.c", "src/gallery.c",
            "-Wl,--gc-sections", "-o", str(executable),
        ], cwd=ROOT, check=True)
        result = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(result.stderr)
        uploads = [line.split("|") for line in result.stdout.splitlines()
                   if line.startswith("TEXTURE|")]
        assert all(not fields[2].startswith("RN") for fields in uploads), "legacy RUN uploaded"
        assert any(fields[2] == "RBV00.TGA" for fields in uploads), "RBV00 removed"
        assert sum(int(fields[6]) for fields in uploads) in (380992, 388928)
        print(f"PASS Noah boot loader, live combat files, Ricky pose bounds and RUN draws: {result.stderr.strip()}")


if __name__ == "__main__":
    main()
