# The AES card edge: measuring it

[`aes-connector.md`](aes-connector.md) has all 200 pins verified end to end. That
is the *electrical* half. This is the other half — the physical card edge, which
no pinout table contains and which [`board-zero.md`](board-zero.md) §9 names as
the only thing blocking a board file.

**Status:** protocol written, numbers not yet taken · Opened 2026-09-27

Numbers go in [`data/aes-card-edge-dimensions.csv`](data/aes-card-edge-dimensions.csv).
Nothing here is `[MEASURED]` until that file has values in it.

---

## 0. Before touching anything

- **Use the board that is not warped.** A warped board gives thickness and
  flatness readings that are about the warp, not about the design. Note in the
  CSV which board each number came from.
- **Do not drag steel caliper jaws along the gold fingers.** Close gently,
  perpendicular to the surface. Gold plating on a 1990s cartridge is thin and
  the fingers are the one part of this board that cannot be replaced.
- **Zero the calipers before starting and re-zero every few measurements.**
  Cheap calipers drift, and drift looks exactly like a real dimension.
- **Three readings per dimension, and record the spread**, not just the mean.
  The spread is what tells us later whether a number is trustworthy.
- Work on a hard non-carpet surface; hold the boards by their edges.

## 1. Orient the board first — and on CHA, SNK already did it for you

**`[MEASURED: 2026-09-27]` The pin numbering is silkscreened on the board.**
`NEO-AEG CHA42G-4` carries **`A1`** at one end of the finger row and **`A50`** at
the other, printed on the same face as the fingers. `A1` is the `NEO-273` end;
`A50` is the `MADE IN JAPAN` end. No continuity testing is needed to orient it.

**And the pinout is visible in the copper.** Row `a` on CHA has GND at `a1`,
`a2`, `a49`, `a50` and VCC at `a25`, `a26`, `a27`. The board shows **wide pads at
both ends of the row and a wide group in the middle**, which is exactly that
pattern and nothing else — power and ground made wide for current, with the
signal fingers a uniform width between them. That is our CSV confirmed against
physical copper, for free, from a photograph.

One thing this does *not* settle: whether SNK's silkscreened `A` row is our
CSV's row **`a`** or our row **`b`**. The pad pattern above is symmetric between
the two rows (both have GND at 1/2/49/50 and VCC at 25-27), so it cannot
distinguish them. **One continuity check still does:** on row `a`, `a48` is
`24M`; on row `b` the equivalent position is a `CR` line. Simpler still, probe
`a5` (`12M`) — a clock, not a data line. Worth the two minutes.

### The multimeter method, for PROG, or as a cross-check

Getting the numbering backwards would silently invalidate every dimension
afterwards, so establish orientation before measuring anything.

Our CSV calls row **a** "top" and row **b** "bottom". That is a *label* inherited
from the pinout source. What it means on a physical board in a physical console
is not yet established, and is what this step settles.

**Three independent checks, using the P mask ROM as the reference:**

| Check | Expected | What it proves |
|---|---|---|
| Continuity from the ROM's **GND** pin to the fingers | hits **8** fingers — the outermost two at *each* end of *both* rows (`a1`, `a2`, `a49`, `a50`, `b1`, `b2`, `b49`, `b50`) | you have found the edge and both rows |
| Continuity from the ROM's **VCC** pin | hits **6** fingers, in a cluster near the **middle** (`a25`–`a27`, `b25`–`b27`) | confirms the numbering scheme, and that you are on a PROG board |
| Continuity from the ROM's **A0** pin | a single finger, **third from one end**, on the row that carries addresses | **that end is pin 1 and that row is `b`** — because `A1` is `b3` |

The third check is the one that orients it. Cross-check it with the ROM's **D0**
pin, which should land on `a3` — third from the *same* end, on the *other* face.
If A0 and D0 come out third-from-*opposite*-ends, something is wrong with our
assumption and we should stop and work out what before measuring.

Then **write down and photograph** which physical face is row `a`: the side with
the silkscreen, the side with the chips, or however it is most reliably
described. And note which way the cartridge goes into the console, if the shell
makes that obvious.

## 2. Pitch — the one number worth getting right

Every other dimension has slack. Pitch does not: a pitch error of 0.05 mm
accumulates to 2.5 mm across fifty fingers, which is a board that does not fit.

**Do not measure one gap.** Measure the whole row and divide:

- Jaws from the **left edge of finger 1** to the **left edge of finger 50**.
- That span is **49 × pitch**.
- Divide by 49. Caliper error is divided by 49 along with it.

**Hypothesis to test: 2.54 mm (0.1 inch)** — and this is not a guess from
nowhere. [`aes-connector.md`](aes-connector.md) has asserted "pin pitch 0.1 in
(2.54 mm) · board thickness 1.6 mm" since the day it was written, **with no
source attached**. It is the only unsourced claim on a page where everything else
is cross-checked three ways, and it is exactly the kind of number that could have
been carried over from an *MVS* page — which is how this project got pin
numbering wrong once already, MVS being 2 x 120 pins where AES is 2 x 100. So
§2 and §4 are not gathering new facts so much as **auditing the two oldest
unaudited numbers in the repository.**

If so, that span reads **124.46 mm**. This is a decisive test rather than a confirmation — a 2.0 mm
pitch would read 98.0 mm, and 1.27 mm would read 62.2 mm. You will know
immediately which it is, and 150 mm calipers reach all three.

**Cross-check:** left edge of finger 1 to the **right** edge of finger 50 equals
`49 × pitch + finger width`. Subtract the first measurement and you have the
finger width, independently of trying to measure one 1.5 mm finger.

### The trap in the whole-row span, found the hard way `[MEASURED: 2026-09-27]`

First attempt on CHA gave **120.83 mm** and **121.83 mm** across the finger
field. Those do not settle the pitch, and the reason is worth recording because
the §2 instruction above is what caused it:

| Assumed gaps spanned | 120.83 gives | 121.83 gives |
|---|---|---|
| 49 | 2.466 mm | 2.486 mm |
| 48 | 2.517 mm | **2.538 mm** |

2.538 is within 0.002 mm of 2.54. So the reading is *consistent* with a 0.1 inch
pitch — if the span was 48 gaps. It is also consistent with a 2.5 mm pitch over
49. **A measurement that supports two answers is not a measurement**, and the
fault is in the method: at both ends of the row the outermost pads are wide GND
pads rather than ordinary fingers, so "the edge of finger 1" is not a
well-defined feature to put a jaw against.

**Fix: span a counted number of ordinary fingers in the middle of the row.**
Left edge of one finger to the left edge of the finger **ten positions** along,
somewhere in the uniform stretch away from both ends and away from the VCC
group. That span is exactly `10 × pitch`:

| Pitch | 10-gap span reads |
|---|---|
| 2.54 mm | **25.40 mm** |
| 2.50 mm | **25.00 mm** |
| 2.45 mm | 24.50 mm |

0.4 mm apart on a 25 mm span, with both endpoints being the same feature on the
same kind of pad. Do it twice, at two different places in the row. If both read
25.4, the pitch claim holds and the whole-row span was 48 gaps; if both read
25.0, the claim in `aes-connector.md` is wrong and always has been.

### Better: stop counting, and read it in inches `[2026-09-28]`

The counted span above has two ways to go wrong, and the second attempt hit both
at once. A span on PROG read either **30.08** or **38.08 mm** — the middle
segment of a seven-segment digit is not reliably legible in a photograph — and
the number of gaps it covered could not be counted from the same photograph.
The arithmetic is unhelpfully symmetric:

| If the reading is | over | pitch |
|---|---|---|
| 38.08 mm | 15 gaps | **2.539 mm** — 2.54 to within 0.02 |
| 30.08 mm | 12 gaps | **2.507 mm** — 2.50 to within 0.08 |

Two unknowns, one equation. Each reading lands cleanly on a *different* answer,
which is the worst possible outcome and a sign the method is still wrong.

**The method that has neither problem: switch the caliper to inches.**

If the pitch is 0.1 inch, then **any** span of N gaps reads as exactly
**N/10 inches** — 1.200, 1.500, 0.900 — dead round, to as many decimals as the
display has. If the pitch is 2.5 mm, the same spans read **1.1811** and
**1.4764**: ragged, and never round.

| Span | at 2.54 mm | at 2.50 mm |
|---|---|---|
| 12 gaps | **1.200 in** | 1.1811 in |
| 15 gaps | **1.500 in** | 1.4764 in |
| any N gaps | **N/10 exactly** | never round |

**So you do not have to count the fingers, and you do not have to read the
number precisely.** You only have to see whether it is round. Put the jaws
anywhere across the uniform part of the row, press `inch/F` until it shows
decimal inches rather than fractions, and look at the last two digits. Round
means imperial means 2.54 mm. Ragged means metric means the claim in
`aes-connector.md` has been wrong since the day it was written.

That is a yes/no question answered by glancing at a display, instead of two
measurements that have to be right simultaneously. It should have been the first
thing suggested: SNK were building in 1990 to a card-edge standard, and card-edge
standards of that era are imperial by default — which makes "is it round in
inches" the natural discriminator rather than an afterthought.

## 3. Finger geometry

| Quantity | How |
|---|---|
| Finger width | from the cross-check in §2, then confirm directly on three separate fingers at different places along the row |
| Gap between fingers | directly, on three separate gaps. **`width + gap` must equal pitch** — that is a free validity check on all three numbers |
| Finger length | from the insertion edge inward to where the copper ends / the solder mask starts. Caliper depth blade, or jaw tips |
| Copper reaches the edge? | yes/no. It should. Note if it stops short |

## 4. Thickness, and whether there is a bevel

- **Substrate thickness** at a bare spot *away* from the fingers. Expect 1.6 mm
  nominal; some retro boards are 1.2 mm, and guessing wrong here means a
  cartridge that is loose or will not insert.
- **Thickness across a finger** — substrate plus plating on both faces. The
  difference from the above, halved, is roughly the plating build-up.
- **Bevel:** measure thickness *at the extreme insertion edge* and again ~2 mm
  in. If the edge is thinner, the board is chamfered. Then measure how far the
  chamfer runs back from the edge; that distance plus the thickness gives the
  angle. Fabs offer 20°, 30° and 45°, so the answer should land near one of them.

## 5. Where the fingers sit on the outline

A footprint needs the fingers placed relative to the board, not just spaced
relative to each other.

- Board's **left side edge** to the **centre of finger 1**.
- Board's **right side edge** to the **centre of finger 50**.
- If those two differ, the asymmetry may be the key that stops the board going
  in backwards — measure it carefully and say so.
- **Overall width** and **overall height** (insertion edge to the far edge).
- Any **notch, keyway, cutout, mounting hole or chamfered corner**: position from
  a named corner, plus its own dimensions.
- **Row registration:** is `a1` directly opposite `b1`, or offset by half a
  pitch? Measure side-edge-to-first-finger on *both* faces. Equal means aligned.
  This is easy to overlook and expensive to get wrong.

## 6. Do it twice: CHA is a second board with its own edge

`CN4` is CHA and `CN5` is PROG, and they are **separate boards, each with its own
card edge** `[VERIFIED: docs/data/aes-cartridge-pinout.csv; confirmed on the
Fatal Fury Special teardown, where S1 and M1 sit on the CHA board]`.

They are almost certainly geometrically identical. "Almost certainly" is exactly
the kind of assumption this project writes down and then checks, so **measure
pitch, finger width, finger length and thickness on both** and record them as
separate rows. If they match, that is a finding worth one line. If they do not,
it is a finding worth a great deal more.

## 7. Scan it as a second, re-checkable source

A flatbed scan at **1200 dpi with a steel ruler laid alongside the fingers** in
the same plane gives an independent measurement of pitch and finger geometry that
can be re-measured later, by anyone, without the cartridge. At 1200 dpi one pixel
is 0.021 mm, which is finer than the calipers.

This is the cheapest way to make the measurement *reproducible* rather than
merely recorded, and it costs one scan while the cartridge is already open. Save
it as a lossless PNG. It is a photograph of our own hardware, not ROM data, so it
can live in the repository.

## 8. What happens to these numbers

1. They fill in `data/aes-card-edge-dimensions.csv`.
2. That becomes a KiCad footprint — generated from the CSV by a script, the same
   way `gen-kicad-symbol.py` and `gen-kicad-sch.py` generate from the pinout CSV,
   so the footprint cannot drift from the measurements.
3. `neoforge-netcheck` already verifies the schematic against the pinout. The
   footprint gets the equivalent check: every pad's number and position derived
   from the same CSV that the fingers were measured into.
4. Board zero becomes a board file.

---

Sources: direct measurement of a Fatal Fury Special AES cartridge — see
[`teardown-fatal-fury-special.md`](teardown-fatal-fury-special.md) for what is on
those boards. Pin assignments from
[`data/aes-cartridge-pinout.csv`](data/aes-cartridge-pinout.csv).
