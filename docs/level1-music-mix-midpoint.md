# Level 1 midpoint mix

This branch implements the approved offline midpoint audition after pass 1 (`fa6d4fed15b753f9038ec70bb44dba94d1df7521`). The audition adjusted captured instrument gains at higher precision. The playable mix approximates those gains using the existing Saturn bank formats.

- The ten mapped drum tones return to their original TL values. Their existing signed PCM is multiplied by 0.957745 and rounded to the original bit depth, since the native driver cannot apply a uniform half-step in tone attenuation. Measured RMS changes across the packed samples range from −0.24 to −0.38 dB versus the original PCM. Sample formats, guard bytes, pitch, timing, envelopes, and sequence data are preserved.
- The bass uses a revised dedicated velocity curve. CC7 and CC11 remain 127 and TL remains 0. The bass PCM, sustain loop, tuning, and performance data are preserved.
- Both guitars, all SFX including POOWAH, Level 2 audio, E108 handling, and all gameplay and rendering files are preserved. Level 1 still uses 478,000 of 524,288 SCSP bytes, leaving 46,288 bytes free.

[Approved offline audition](https://raw.githubusercontent.com/captshred/Mullet-Force-Saturn-Public/0ad50dd4d7e435fb1a0f2fc1ed07c39b4d06a7d6/docs/audio-previews/level1-music-mix-midpoint.wav)
