# Why the serializer moved: AES vs MVS cartridge architecture

On MVS the sprite serializer sits on the motherboard. On AES it sits inside the
cartridge. This is the difference that makes MVS-to-AES converters active
devices, and the reason there is no such thing as a dumb ROM-only AES cart that
can display sprites.

Nobody appears to have written down *why*. This document is our attempt.

**Everything below marked `[UNVERIFIED]` is inference from the hardware, not
from any SNK source.** We looked for a primary statement of SNK's reasoning and
did not find one. If you have one — an interview, a service manual, a developer
account — please open an issue. **If you think we are wrong, please open an
issue for that too.** Being corrected in public is the fastest way this project
gets accurate.

---

## First, a correction to the question

SNK did not *change* the architecture. Both were proposed together. Takashi
Nishiyama, who joined SNK from Capcom, "proposed the concept of an arcade system
that uses ROM cartridges like a game console, and also proposed a home console
version of the system." `[VERIFIED: Wikipedia, Neo Geo]`

They shipped ten days apart: **MVS 16 April 1990, AES 26 April 1990** (Japan).
`[VERIFIED: Wikipedia, Neo Geo]` MVS was first, but not by enough to make AES a
derivative — and the hardware is identical by design, so that home users could
"play the games exactly as they were in the arcades."

The real question is why one chipset got two different placement decisions —
and the answer is that the two products had almost opposite cost structures.

---

## 1. Pin count — the strongest argument, and it is quantifiable

The serializer's job fixes what has to cross the cartridge connector. From
`neo_zmc2.v`: `[VERIFIED: NeoGeoFPGA-sim, Video/neo_zmc2.v]`

```verilog
module neo_zmc2(
    input  [31:0] CR,          // 32 lines in  — raw C ROM data
    output [3:0]  GAD, GBD,    //  8 lines out — packed pixels
    output        DOTA, DOTB   //  2 lines out — opacity
);
```

Thirty-two lines in, ten lines out. So:

- **Serializer on the motherboard (MVS):** the cartridge must expose the full
  32-bit C ROM data bus at the edge connector.
- **Serializer in the cartridge (AES):** only ten lines cross.

**A saving of 22 pins.**

Now the connectors: `[VERIFIED: wiki MVS cartridge, wiki AES cartridge]`

| | Pins |
|---|---|
| MVS cartridge | 2 × 2 × 60 = **240** |
| AES cartridge | 2 × 2 × 50 = **200** |
| Difference | **40** |

The serializer placement accounts for **more than half** of the entire pin-count
difference between the two formats.

A smaller edge connector is cheaper, physically smaller, and has fewer contacts
to oxidise or misalign. In a consumer product sold into living rooms and handled
by children, all three matter considerably more than they do on an arcade PCB
inside a locked cabinet. `[UNVERIFIED]`

## 2. Multi-slot economics — this explains the MVS side by itself

MVS boards shipped in 1, 2, 4 and 6-slot configurations, and only one game runs
at a time.

With the serializer on the motherboard, **one** chip serves every slot. Put it
in the cartridge instead and an operator running a 6-slot board with twenty
games has bought twenty serializers to use one at a time.

For an arcade format where cartridges vastly outnumber motherboards, on the
board is not a close call. `[UNVERIFIED]`

## 3. Where the cost lands

**Revised 2026-09-06.** An earlier version of this section argued from the AES's
later retail pricing — roughly $650 with $200 games. That was anachronistic. The
real situation at design time was considerably more extreme.

The AES did not launch as a product SNK sold. It launched as a **rental**:

> "The Neo Geo AES was originally released solely as a rental console for video
> game stores in Japan called the Neo Geo Rental System, with its high
> manufacturing costs causing SNK not to release it for retail sale."
> `[VERIFIED: Wikipedia, Neo Geo]`

Retail came later, after demand forced the reversal.

So the constraint on the AES console was not "keep it competitively priced." It
was that **SNK could not manufacture it cheaply enough to sell at all.** A
console whose bill of materials defeats its own business model is under about as
much cost pressure as hardware ever gets.

And a rental model sharpens it further: SNK owns every unit it builds, so
console BOM is capital the company carries directly rather than a cost passed to
a buyer. Every part removed from the console is money SNK does not have to
front, multiplied by every unit in the field.

Moving a chip out of that console and into the cartridge is exactly the move
that pressure produces.

MVS inverts the whole picture. The operator buys one board and many cartridges.
There SNK wants the *cartridge* bill of materials low, and the board absorbs
cost because it is amortised across every game that operator ever buys.

Same chipset. Opposite incentives. Opposite placement. `[UNVERIFIED — the
inference; the manufacturing-cost and rental facts are verified]`

---

## The anti-piracy theory, and why we do not believe it

The intuitive explanation is that SNK separated the formats to stop cheap arcade
cartridges migrating into homes, where the price gap was largest. We think this
is wrong, for two reasons.

**The connectors already do that job.** 240 pins versus 200, different physical
cartridges, different shells. Whatever market separation SNK wanted was already
guaranteed by the connector. Serializer placement adds nothing as a lockout.

**SNK's real anti-piracy work looks nothing like this.** We know what it looks
like because it is documented: PRO-CT0 used as a challenge-response security
device on PROG-G2 boards for *Fatal Fury 2* and *Super Sidekicks*, and Altera
MAX CPLDs (EPM7128SQC100-15) on *KOF '98* and *Metal Slug X*.
`[VERIFIED: wiki PRO-CT0, wiki MVS cartridge, MAME chip notes]`

When SNK wanted protection, they added dedicated logic whose only purpose was
protection. The serializer is not shaped like that. It is a chip with a real job
that had to be physically located somewhere, and both locations have defensible
engineering arguments.

**That said, the friction was real regardless of intent**, and it is hard to
imagine SNK minding. It is exactly why MVS-to-AES converters cannot be passive
devices. A convenient side effect is not the same as a design goal — but it is
not evidence against one either. We simply have no source. `[UNVERIFIED]`

---

## What would change our minds

Stated up front so this is falsifiable rather than merely plausible:

- **Any primary SNK source** — interview, internal document, service manual,
  developer recollection — stating the reasoning. That would settle it either
  way and we would rewrite this page.
- ~~**Evidence that AES was designed after MVS rather than alongside it.**~~
  **Tested 2026-09-06 — did not fire.** Raised by the maintainer on the
  intuition that MVS was the primary product and AES an afterthought. Half
  right, and the half that was right improved the page: AES did ship second and
  was indeed too expensive to sell, launching as a rental. But Nishiyama
  proposed both systems together, so it is not a derivative. The parallel-design
  framing survives and now has a source rather than being an assumption.
  Argument 3 was rewritten as a result — see the revision note there.
- **A pin-count analysis showing the 22 lines were needed elsewhere anyway.** If
  the AES connector is pin-limited for reasons unrelated to the C bus, argument
  1 weakens.
- **Any other SNK system placing a chip to enforce market separation.** A
  pattern would change how we read this instance.

## What we are confident about

Only the mechanism, not the motive. The pin arithmetic is arithmetic; the
32-to-10 reduction is in the HDL and the connector counts are in the wiki. The
*reasons* are our reading of it.

---

## Consequences for NeoForge

Not merely historical — the placement is the project's central constraint:

- An AES cartridge must serialize its own sprite data, or hold DOTA and DOTB low
  and forgo sprites entirely. See `docs/open-questions.md` Q1.
- The 22 pins SNK saved are 22 pins of C ROM bus that NeoForge never has to
  drive across the connector, which makes the AES cartridge edge *easier* to
  build for than the MVS one. The serializer is the price of that.
- Anyone building an MVS-to-AES converter is re-adding the chip SNK removed,
  which is why `FusionConverter` exists and why it needs a CPLD.

---

## Revision history

- **2026-09-06** — Original.
- **2026-09-06** — Challenged on the parallel-design premise. Added sourced
  release dates and Nishiyama's dual proposal; rewrote argument 3 around the
  Neo Geo Rental System and the manufacturing-cost problem rather than later
  retail pricing. First falsifier tested; conclusion unchanged, reasoning
  materially better.

---

*Corrections welcome and actively wanted. Open an issue. The revision history
above is the point — this page is meant to be argued with.*
