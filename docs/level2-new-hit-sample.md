# New non-lethal Hit sample

Parent/merge-base: f27333b1422c0a24cb5fe0f52f9557649b820941, owner-WebRetro
approved. Branch audio/level2-new-hit-sample. No game C/header/build/staging source
changes. Every startup, scheduling and event-routing byte remains frozen.

Hit.wav SHA256601f85a59b5284cb4cb09fc37be29396ec573b1b9bb194201962d55e1b584b4d:
44100Hz stereo signedPCM16,18798 frames,0.4262585s. Deterministic mean L/R with
symmetric half ties away from zero; signed big-endian monoPCM16; no normalization,
compression, pitch/time change, effects or trimming. Runtime37596 bytes.

Only bank0/program1 is used for Hit (control2/channel8). Approved Fire selects
bank2/program0 on controls2/3; no other playback uses old Shot. Replace old44806
PCM bytes at180832 with37596 new bytes and7210 zero bytes; change only the tone
end frame22403->18798. Do not repack the bank: all other addresses and bytes,
including Explosion/Flame PCM and tone parameters, remain identical. The old
Shot waveform is removed, not duplicated. Unused7210 bytes remain reserved to
preserve subsequent Flame addresses. Allocated SCSP delta0; high-water485812,
free38476. PCM payload decreases7210 bytes; allocation does not shrink.

Hit remains one voice, Hit-only retrigger,34-tick conservative retirement,
eight pending events, one start per VBlank, newest excess dropped. Routing stays
surviving projectile damage only; lethal/dead/miss/Flame damage remain silent
for Hit. Fire retrigger, Explosion5-tick/eight-event scheduling, Music, both
Flames and the repaired56-byte/28-word/60-byte-backing bootstrap followed by
64-byte Fire map publication and041a readiness are unchanged.

WFIRE.MAP/TON and all other resources remain byte-identical. VDP1 remains33792B/
28 definitions/81 commands; VDP2 remains65792 payload/434176 reserved; CRAM32.

Authoring WAV stays private under AGENTS.md. WDEATH.TON, new-hit.json provenance,
and tools/import-level2-hit.py are committed; clean builds need no external WAV.
The importer is optional for repeating the import. Validation reconstructs the
allowed delta against the preserved original bank and rejects ANY other bank
change. Exact parent preservation locks retain every executable source byte.
Existing full transport, routing, startup/mutation, gameplay/camera and native
allocator tests remain active, alongside the new sample-identity check.

Release: clean checkout, bash tools/verify-canonical-build.sh. Build source only,
never substitute a preserved executable. Manual Actions: workflow from main,
profile stage-default, exact delivered source SHA. No automatic Actions or tag
changes. Owner WebRetro testing remains required for sample approval.
