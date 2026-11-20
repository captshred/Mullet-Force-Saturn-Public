# Level 1 Phase 4A.2 · MEGA ARCADE composition

Source starts at `9301bd2831371f03461debf1a404a12441c5a896`. The definitive
downhill baseline remains `dce0d49cbba8da61b90df7b42ed446d47a54c41a`. Every
approved downhill pixel through world X 2559 is preserved.

| Geometry | Range |
| --- | --- |
| World art | X 0–3199, Y 0–367 |
| Player centers, subject to the existing tether | X 26–3130 |
| Camera origin | X 0–2880 |
| Native final view | X 2880–3199, 320 × 240 |
| Original slope | X 1920–2560 |
| Open lot to doorway | Approximately X 2758–3130 |
| Main entrance center | Approximately X 3095 |
| Arena combat lanes | Simulation Y 168–229, panorama Y 296–357 |

The annex is 128 pixels shorter. The garaged cars, deck geometry and garage
lighting are retained. The gold and blue lot cars are independently reduced
from the concept at uniform scales. The red car uses the same uniform scale
as the frontage. All remain behind the main combat lanes. The facade
includes the complete marquee and doors in the final camera view. The
remaining right-hand pixels frame the building, with the walking limit on
the entrance apron. The original sky patch behind the facade was replaced
with clear concept sky to remove the superseded roof and marquee.

The downhill asphalt's dominant approved RGB555 swatch (index 220) sets the
lot's pavement base. The transition retains its existing curb, railing and
trash cans. Cracks, parking paint and wet neon accents remain distinct
against the darker road. The renderer, RGB555 palette, follow behavior,
Y projection, combat controls and original MF-88 encounter are reused.

| Resource | Usage |
| --- | --- |
| VDP1 texture use | 386,432 bytes, with 49,152-byte hero reserve protected |
| VDP2 allocation | 434,176 bytes, including 106,496 bytes of street cells |
| Packed background low work RAM | 440,176 of 524,288 bytes |
| CD staging peak | 65,540 bytes, with reads confined to startup |
| Retained background heap | 112,765 bytes |

The indexed artwork uses 10,250 unique source tiles and the existing 1,664
resident street cells. Audio assets and SCSP allocation are unchanged.

To reproduce with the approved 2172 × 724 concept PNG available locally:

```sh
git show 9301bd2831371f03461debf1a404a12441c5a896:assets/level1-intersection/IXPIX.BIN > /tmp/mega-previous.bin
python3 tools/recompose-mega-arcade.py "/path/to/concept.png" /tmp/mega-previous.bin --output /tmp/mega-panorama.bin
python3 tools/pack-level1-panorama.py /tmp/mega-panorama.bin
```

The master concept remains outside the repository.
