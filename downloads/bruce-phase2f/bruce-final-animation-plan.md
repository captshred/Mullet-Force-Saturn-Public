# Bruce · Final knockdown, get-up and defeat art plan

The approved bank uses **135,936 aligned VDP1 bytes**, leaving **34,040**
below the reserve-safe ceiling of 169,976. The 49,152-byte hero reserve
stays protected. If a future stagger is needed, review reuse of the
approved hit reactions before allocating dedicated art.

| Clip | Planned poses and reuse | Estimated new bytes |
| --- | --- | ---: |
| Knockdown | A committed fall and a grounded down pose | 12,608 |
| Get-up | Start on the exact down pose, add a braced rise, then return to idle | 7,296 |
| Defeat | Reuse the fall and the same grounded down pose, with a longer terminal hold | 0 |
| **Total** | **Three new texture payloads** | **19,904** |

Projected complete bank is **155,840 bytes**, leaving **14,136 bytes**.
If playtest review calls for a distinct 128 × 40 defeat settle, it
would add 5,120 bytes and leave 9,016 bytes. Start with the shared fall
and down textures so the get-up and defeat tests have the same ground
contact reference.

Supply the right-facing fall, down and braced-rise poses together as
144 × 120 transparent RGBA PNGs. Preserve pivot (64, 112), align the down
silhouette to the existing ground row, and keep dust and other effects
separate. Review one-shots at native scale and inspect any reused frame
in both sequences before approving the bank. This plan allocates no
new assets and changes no runtime behavior.
