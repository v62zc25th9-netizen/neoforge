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

### The validity check fired, and I read it backwards `[wrong — corrected below]`

§3 says `width + gap` must equal the pitch, and calls it "a free validity check".
It fired.

| Measured directly, on PROG | |
|---|---|
| Finger width | **1.6–1.65 mm** |
| Gap between fingers | **1.4 mm** |
| **Implied pitch** | **3.00–3.05 mm** |
| Finger length | 10.8 mm |

**Two independent routes now agree on ~3.0 mm, and neither is 2.54.** The
second route also resolves the unreadable digit from the previous attempt: the
span was **30.08**, not 38.08, because `30.08 / 10 = 3.008` matches the
width-plus-gap figure while 38.08 matches nothing. A ten-finger span is what had
been asked for, and ten is what it was.

So the long-unsourced claim in [`aes-connector.md`](aes-connector.md) is
**probably wrong** — and wrong in the direction that would have been expensive.
A board drawn at 2.54 mm would have accumulated 0.46 mm of error per position
and been unusable within a few fingers of the end.

**It is only "probably", because a third measurement disagrees.** Two earlier
spans across the finger field read **120.83** and **121.83 mm**. With 50
positions those imply a pitch of **2.486 mm**, not 3.0. The three numbers cannot
all be right:

| Pitch | 49 gaps spans | Consistent with |
|---|---|---|
| 2.486 mm | 121.8 mm | the field spans, not the finger geometry |
| **3.00 mm** | **147.0 mm** | the finger geometry and the 10-gap span, not the field spans |

The field spans were taken before there was any agreed definition of where the
jaws go, and they are the only readings here whose endpoints were never written
down — so they are the weakest of the three, not the tie-breaker. **But 49 gaps
at 3.0 mm needs a 147 mm finger field to exist**, and a 121.8 mm reading is not a
rounding error away from that.

**The deciding measurement is therefore the full field**: first finger to
fiftieth, in one span, with the count of 50 confirmed by eye rather than assumed
from the silkscreen.

- **~147 mm** → pitch is 3.0 mm, and the earlier spans did not cover the whole row
- **~122 mm** → the finger geometry is over-measured and something is wrong with
  how a 1.4 mm gap and a 1.6 mm finger are being read
- anything else → the row is not 50 evenly spaced positions, which would be the
  most interesting outcome of the three

150 mm calipers reach 147 mm with almost nothing to spare, so it may want a steel
rule or the scan in §7 instead.

### Correction, same evening: the pitch is 2.54 mm after all `[MEASURED: 2026-09-28]`

The span was **38.08 mm**, and it covered **16 fingers — 15 gaps.**

| | |
|---|---|
| 38.08 / 15 | **2.5387 mm** |
| against 0.1 in (2.54 mm) | **−0.0013 mm per gap** |
| the same span in inches | **1.4992 in**, against 1.5000 for fifteen 0.1 in gaps |

**The original claim in [`aes-connector.md`](aes-connector.md) was right.** The
inch test from the previous section also passes, cleanly — it only ever needed
the reading, which is what it was designed not to depend on, and then the
reading is what decided it anyway.

**Everything above this heading is my error, and it is a specific one: I
inverted the reliability ordering.** A fifteen-gap span divides caliper error by
fifteen; a 1.4 mm gap and a 1.6 mm finger are the two smallest features on the
board measured with the least suitable instrument. The whole reason §2 says to
span many fingers is that spanning many fingers is more trustworthy than
measuring one. I then let the two single-feature readings overturn the
multi-gap span — and, worse, wrote "nothing should be drawn at 2.54 mm" into the
connector document on that basis. Had a board been ordered in between, it would
have been ordered wrong, from a correction rather than from the original claim.

### And the mini finger explains the discrepancy exactly

**The mini fingers split the big fingers at their midpoint and are part of the
same pad** — so they are a shape, not extra contacts, and contact pitch *is*
finger pitch. The earlier worry that "every number above is describing the wrong
thing" is retired.

But the shape is the whole explanation for `width + gap = 3.0`. **Each pad is
wide at one part of its length and narrow at another, so width and gap are only
complementary if both are measured at the same cross-section**, and they were
not:

| Measured where | Width | Gap | Sum |
|---|---|---|---|
| across the wide section | **1.6** | 0.94 | 2.54 |
| across the mini-finger section | 1.14 | **1.4** | 2.54 |
| **what was actually recorded** | **1.6** (wide) | **1.4** (narrow) | **3.0** ✗ |

So `width + gap = pitch` never failed. It was applied across two different
cross-sections of a pad that is not a plain rectangle, which is a real trap and
now a documented one: **measure width and gap at the same distance from the
board edge, and say which distance.**

Two falsifiable predictions fall out, both cheap:

- gap between the **wide** sections ≈ **0.94 mm**
- width of the **mini-finger** section ≈ **1.14 mm**

If those hold, the footprint has its full profile and §2 is closed.

### What is now settled, and what the numbers predict

| | |
|---|---|
| Pitch | **2.54 mm (0.1 in)** `[MEASURED: 2026-09-28]` |
| Substrate thickness | 1.55 mm bare, **1.65 mm across a finger** — order 1.6 mm |
| Finger length | 10.8 mm |
| Pad profile | wide section + a narrower "mini finger" at the midpoint, one pad |
| **Predicted full field**, finger 1 to finger 50 | **124.46 mm** |

That last line is the remaining check. The two earlier undefined spans read
120.83 and 121.83 mm; **121.83 / 2.54 = 47.96, which is 48 gaps** — one gap short
of the full row, exactly what you would expect from jaws landing inside the wide
GND pad at one end instead of on its outer edge. Consistent, and no longer a
contradiction.

### Closed by a second source, and one of my verdicts was wrong `[VERIFIED: 2026-10-06]`

`Board-Folk/NeoGeoAES-3.5` is a recreation of the AES **motherboard**, and it is
readable (see [`../contributing.md`](../contributing.md)). Its `CN4-5` footprint
is the cartridge slot connector, and it answers three of this file's questions
outright:

| | Reference design | Ours |
|---|---|---|
| Pitch, row a | **2.5400 mm** | 2.5387 measured |
| Pitch, row b | **2.5400 mm** | |
| `a1` → `a50` span | **124.46 mm** | 124.46 **predicted** |
| `a1` vs `b1` x position | **identical** | rows aligned, §5 answered |

**The predicted full field was exactly right**, to the hundredth. That is our
caliper work and an independent reconstruction agreeing on a number neither
derived from the other.

And a third source agrees: the connector is an **EDAC `395-100-524-204`**
`[VERIFIED: Board-Folk BOM, Mouser 587-395-100-524-204]`, and the EDAC 345/395
ordering guide states **0.100 in (2.54 mm) contact spacing**. Pitch is now
confirmed from calipers, from a reconstruction, and from the mating connector's
own datasheet.

**The correction I owe.** When the slot spacing came back as "8 mm at the
separator, 10 mm far edge to far edge", I said the pair was impossible because
it implied a 1.00 mm slot for a 1.65 mm board. The reference says the two
connectors sit **10.03 mm centre to centre**. With a 1.65 mm board that puts the
inner faces **8.38 mm** apart — so **both readings were good measurements**, and
what was wrong was my assumption that "far edge to far edge" meant outer face to
outer face. The pair differ by one board thickness, not two, which is the
signature of an inner-face-to-centre measurement. The arithmetic check in §4 was
fine; the endpoint definition I applied it with was not.

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
