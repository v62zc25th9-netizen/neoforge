#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate the test sample for the NeoForge V ROM test.

No audio file ships in this repository. The sample is synthesised here, for
the same reason tiles.py draws its own graphics: a borrowed asset carries a
licence question, and a generated one does not.

The YM2610's ADPCM-A decoder runs at a fixed rate of about 18.5 kHz, which is
why vromtool's own examples resample to 18500 Hz mono before encoding. We
generate at that rate directly.

What it makes: a two-tone chirp, 440 Hz then 880 Hz, with a short click at the
front. Chosen to be unmistakable rather than pleasant - the question this ROM
asks is "did any sample data reach the YM2610", and an octave jump answers it
even through a small television speaker in a noisy room. A pure sine would be
easy to confuse with hum; noise would be easy to confuse with a fault.

    python3 sample.py out.wav
"""

import math
import struct
import sys
import wave

RATE = 18500        # YM2610 ADPCM-A playback rate
TONE_MS = 180       # per tone
CLICK_MS = 6
AMPLITUDE = 0.7     # leave headroom; ADPCM-A is lossy and clipping is ugly
FADE_MS = 8         # anti-click ramp on each tone edge


def tone(freq, ms, fade_ms=FADE_MS):
    """One tone with short raised-cosine fades, as signed 16-bit samples."""
    n = int(RATE * ms / 1000)
    fade = max(1, int(RATE * fade_ms / 1000))
    out = []
    for i in range(n):
        v = math.sin(2 * math.pi * freq * i / RATE)
        # Fade in and out so the tone boundaries do not themselves click -
        # otherwise a working sample and a broken one both start with a pop
        # and the test gets harder to read.
        if i < fade:
            v *= i / fade
        elif i > n - fade:
            v *= (n - i) / fade
        out.append(int(v * AMPLITUDE * 32767))
    return out


def click(ms=CLICK_MS):
    """A short square burst, so playback has an unambiguous onset."""
    n = int(RATE * ms / 1000)
    return [int(AMPLITUDE * 32767) if (i // 8) % 2 == 0
            else int(-AMPLITUDE * 32767) for i in range(n)]


def main(path):
    samples = click() + tone(440, TONE_MS) + tone(880, TONE_MS)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)       # vromtool rejects stereo
        w.setsampwidth(2)       # signed 16-bit
        w.setframerate(RATE)
        w.writeframes(struct.pack("<%dh" % len(samples), *samples))
    ms = len(samples) * 1000 // RATE
    print("wrote %s - %d frames, %d ms at %d Hz mono"
          % (path, len(samples), ms, RATE))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "chirp.wav")
