# Proposed VDP1 fighter/enemy animation cache (not implemented)

## Current residency and reusable references

With VDP2 scenery, current runtime VDP1 use is 291,552 bytes. Original Buck-group
textures consume 109,920 aligned bytes (including shared lower halves); Chuck
79,872; enemies 56,960; flames/embers/cue 10,624; RGB props/shadow/hit 12,416;
runtime HUD 21,760. Gallery adds 10,784. The study adds 53,472 and keeps every
original texture resident. Current simulation supports two enemies; adding
more enemy instances is future gameplay work, not part of this branch.

All 15 normal poses, 7 bat upper poses and 3 torch upper poses per fighter are
useful geometric references. The 15 normal, 1 ground-bat and 3 air lower textures
are already shared by both players. Bat grips/tips and air-lower mappings are
especially valuable. Those pixels were authored for narrower anatomy and a
simpler palette; recoloring does not reproduce the new leather/denim, anatomy,
hair or shading. Reuse timing, silhouettes, sockets and choreography, not a
claim that the old lower halves are finished high-detail art. The approved
three-piece idle can be reused exactly as a neutral pose, head/color reference
and rig template. It cannot produce occluded surfaces for all moves by itself.

## Budget example after approved replacement

A future renderer can reserve indexed texture slots once, keeping stable Jo
sprite descriptors. Example conservative caps, **after** explicitly approved
retirement of the old fighter/enemy banks:

| Class | Capacity | Bytes |
|---|---|---:|
| Existing HUD/props/shadow/hit/fire effects | Fixed | 44,800 |
| Fighter frame slots | 2 actors x 3 slots x 16KiB | 98,304 |
| Enemy frame slots | Up to 6 actors x current+next x 8KiB | 98,304 |
| Additional weapon/effect reserve | Fixed | 32,768 |
| **Total** | | **274,176** |
| **Free of current 458,488-byte texture arena** | | **184,312** |

These are caps and a design scenario, not measured costs of uncreated moves.
Body + weapon pieces must fit their declared class; a 192x128 untrimmed 8bpp
frame is 24,576 bytes and would exceed a 16KiB body slot. Pack weapon pieces
separately or budget larger slots. Six enemy instances require twelve worst-case
current/next slots even when not synchronized; instances can share an immutable
resident frame when IDs match. Do not budget only one frame per enemy type.
The optional approved gallery would add 10,784 if retained. This budget is not
added on top of all original banks: retaining them too would double-count a
future replacement and can overflow. The study intentionally does not retire any.

The current arena ends at 0x7FEF8, starts at 0x10000, and assumes Gouraud tables
are not enabled. If future Gouraud shading uses the SDK table at 0x70000,
texture capacity must fall to 393,216 bytes: the example then leaves 119,040.
Do not spend that table space twice.

## Ownership, scheduling and synchronization

Key residency by actor costume/type, move, frame, piece format and palette.
Pin every piece referenced by submitted commands until VDP1 completes it.
One fighter slot is current, one prepared next, and one spare for transitions;
enemy pools pin current and next references per independent instance, with
refcounts allowing shared frames. Submit all piece descriptors as one frame
transaction, so a head from one pose cannot pair with legs from another.

Preallocate through indexed Jo sprite creation. Do not use jo_sprite_replace
as an assumed indexed in-place updater: its public API accepts RGB jo_img, and
allocation/format behavior is unsuitable as an unexamined cache primitive.
Use a narrow audited indexed-upload adapter to fixed raw addresses, with 8px
width, valid color mode, 32-byte allocations and bounded DMA/copy size. Publish
new descriptors only after the transfer completes. Use a verified VDP1 completion
fence / SGL submission contract; VBlank alone does not prove VDP1 has stopped
reading a texture. Never overwrite current or in-flight slots. Measure maximum
upload time and skip optional visual prefetch on overload. A miss must not stall
combat, read the CD on attack input or change attack timing/hitboxes.

Mandatory, immediately reachable moves must have source data resident in work
RAM before combat begins. CD prefetch handles future encounters/costumes only.
Decompress into an unused staging buffer, preflight size/end codes/palette,
then upload to a free slot. Keep a last-valid visual frame as an error fallback
without advancing or delaying simulation; log the miss for fixing, rather than
silently claiming such a presentation glitch is acceptable final behavior.

## CPU RAM and palette constraints

25 current logical upper/body poses per fighter at an illustrative 5,400 packed
bytes each need about **270,000 bytes** for both fighters' complete source banks.
Three enemy types x 12 poses x 5,000 bytes add **180,000**. Combined **450,000**
exceeds the entire existing 393,216-byte Jo heap before staging, loader, and other
allocations. Untrimmed 128x96 bodies cost 12,288 each, making it worse. More
animations increase these figures. Lossless compression may help, but its ratio
and SH-2 decode time must be measured on actual final art. Do not assume 50%.

Before implementation audit the low 1MiB work-RAM ownership, CD/GFS/SGL buffers,
stack bounds and current heap high-water/fragmentation. An explicitly owned low
RAM asset arena is a possible next step, not established free memory. Reserve
two 16KiB CD sectors/staging windows and bounded decode scratch in that audit;
these are not magically included in the texture budget. Stage streaming needs
preloaded mandatory move banks and a loading corridor/encounter scheduler.

The gallery currently fills all eight 512-byte palette banks. The study shares
its existing combined 253-color fighter palette read-only. A future replacement
could assign that combined palette to an existing fighter bank, retiring the
other old bank only when no old pieces reference it. Enemy palettes must be
shared/canonical across types or assigned per encounter within eight banks;
burn-flash remaps also need consistent index roles. Multiple enemy types do not
imply unlimited new palettes. 4bpp subpalettes could reduce texture cost later,
but require new color/cluster review and seam checks. No such conversion is
applied to these high-detail candidates.

## Suggested next steps after visual approval

1. Manually clean the six walk poses, establish pelvis/foot/socket landmarks,
   then approve idle breathing and final locomotion palette clusters.
2. Measure packed sizes of one punch, air pose and widest bat pose to validate
   the proposed slot caps before producing dozens of frames.
3. Audit work RAM and VDP1 completion fences; implement/test a small bounded
   current/next cache with no gameplay substitution first.
4. Only after cache stress tests and hardware profiling, replace one complete
   approved move bank at a time behind a separate feature flag.
