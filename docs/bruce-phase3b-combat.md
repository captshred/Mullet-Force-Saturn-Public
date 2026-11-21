# Bruce Phase 3B playtest

Approach the MEGA ARCADE lot after clearing the downhill ambush. The existing bank safe point waits for all street slots to become absent. The arcade approach preserves both hero draws during the handoff and suppresses the invulnerability blink while keeping the invulnerability timer and damage rules. The bank drains its old suffix before reuse and holds the completed framebuffer through the synchronous disc reads.

Bruce launches from beyond the right side of the camera, travels left along a 48-tick arc with a 62-pixel apex, and lands at lane Y 203 between world X 2838 and 3015. The entrance uses the existing slam and charge poses and impact spark. It deals zero damage. The grounded world pivot supplies depth and shadow placement throughout the entrance.

| Initial tuning | Value |
| --- | --- |
| Health | 30 |
| Heavy punch | 24 damage, 26-tick windup, 5-tick strike |
| Shoulder charge | 18 damage, 27-tick windup, up to 30 active ticks |
| Ground slam | 24 damage, 18-tick windup, 32-tick flight, 52-pixel horizontal and 26-pixel lane radii at impact |
| Player damage to Bruce | Jab/kick 1, airborne strike 2, bat 3, torch contact 1 |
| Bruce hit protection | 12 ticks, with flinch resistance during attack commitment |

Defeat holds the approved face-down pose. Camera scrolling and regular progression remain available. Stage progression, arcade entry, footage of physical hardware, and balance approval are separate from this playtest.

The suffix keeps 19 textures at 162,240 bytes. The twentieth sprite definition references existing idle boot rows for the split punch, charge and hit frames and uses zero texture bytes. The persistent prefix remains 239,360 bytes. Peak resident texture use is 401,600 bytes, leaving 7,736 bytes beyond the protected 49,152-byte hero reserve.

## Phase 3B.1 ground slam

The combat slam commits to the nearest living player at the start of its windup. Bruce launches when the clamped target is 72–140 pixels away horizontally and within 42 pixels along the lane axis. His ground position crosses both axes while his render height traces a 44-pixel arc over 32 NTSC simulation ticks. The landing point remains fixed after commitment. The impact applies damage once at touchdown and keeps the existing jump clearance and recovery cooldown.
