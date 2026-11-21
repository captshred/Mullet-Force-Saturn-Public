# Bruce · Remaining reaction and defeat art plan

The approved bank through the airborne ground slam uses **119,808 aligned
VDP1 texture bytes**. That leaves **50,168 bytes** under Bruce's 169,976-byte
ceiling after protecting the 49,152-byte hero reserve. The existing art
and ground anchors are fixed inputs to the next review.

| Clip | Timing poses and handoff | New estimated bytes |
| --- | --- | ---: |
| Hit reaction | Two recoil uppers, then return to neutral. Reuse planted idle boots where the stance fits. | 13,312 |
| Stun | Two contrasting head tilts over a shared body. Review native head/collar seams before approving the split. | 3,584 |
| Knockdown | One committed fall and one planted down pose. Preserve the body silhouette and establish the final contact row for get-up and defeat. | 12,608 |
| Get-up | Hold the down pose, add one braced rise, reuse neutral idle to complete it. | 7,296 |
| Defeat | Reuse the fall and add one distinctive final settle. If a distinct settle reads weakly, review the existing down pose with a longer hold. | 5,120 |
| **Projected additions** | **Upper bound from Phase 1 trim targets** | **41,920** |
| **Projected complete bank** | | **161,728** |
| **Projected reserve-safe margin** | | **8,248** |

Author right-facing PNGs at 144 × 120 with hard alpha and the common
(64, 112) pivot. Let knockdown width increase while keeping ground
contact consistent. Keep stars, impact flashes, and dust separate.
Assess existing game effects before budgeting new textures. Match the
existing RGB555 palette. Crop and pad only during export, and audit
aligned bytes and any shared texture views before each approval.

Suggested review order is hit and stun, then knockdown and get-up together,
then defeat. Request the down and rise poses in the same artwork handoff
so the ground contact and silhouette match. First test the shared idle
boot view for hit, and verify that a mirrored head does not break the
earring or collar silhouette in stun. If the estimates expand, prioritize
sharing the down pose across knockdown, get-up and defeat. A shared
128 × 40 defeat settle would save 5,120 bytes if it still reads clearly.
No runtime sprite hooks, timings, or encounter behavior are specified here.
