# The measurement cartridge

A cartridge whose job is to find out how slow a cartridge is allowed to be.

**Status: designed, deliberately not scheduled.** This is a research
contribution, not a prerequisite. Read section 1 before planning any work
around it.

---

## 1. Read this first: we probably do not need it

The first version of this document argued that finding the timing limit was
necessary, and that passive approaches could not answer [Q3](open-questions.md).
**That was too strong, and the correction is worth more than the design.**

There is already a known-good envelope. The ROM models in NeoGeoFPGA-sim carry
access-time annotations — P at **120 ns**, C at 250 ns, S at 200 ns, M and V at
100 ns — and `rom_p1.v` states its part in a comment.
`[VERIFIED: NeoGeoFPGA-sim Cartridge/ROMs/*.v, as the model's annotations]`

If SNK shipped 120 ns P ROMs and every Neo Geo cartridge ever made works, then
**120 ns is sufficient by demonstration.** A board designer needs a sufficient
condition, not a limit. Design to 100 ns and there is margin over what the
hardware provably tolerates.

So the engineering path is:

1. **Design inside the envelope.** P ≤ 120 ns, ideally ≤ 100 ns.
2. **Verify the envelope by reading part numbers** off a real board — speed
   grade is in the part number. A magnifying glass, no risk.
3. **Cross-check in simulation**, which costs nothing. See section 10.

**Finding the actual limit remains worth doing** — nobody has published it, and
it is exactly the kind of measurement this project exists to produce. But it is
a contribution to make *after* there is a working board, not a reason to build
one first.

The rest of this document is the design, kept because the problem is interesting
and the constraints it works out are real.

## 2. What it would measure that observation cannot

**Watching a working cartridge tells you the mask ROM was fast enough.** It
gives you that ROM's access time — which, per section 1, is the useful number.
What it cannot give you is the *margin*: how much slower a cartridge could be
and still boot.

That matters only if a design cannot make the envelope. If our FPGA and level
translation cannot hit 120 ns, then knowing whether the real limit is 130 ns or
250 ns decides whether the approach is dead or fine. **That is the contingency
this cart is for.**

To find a limit you have to reach it — make the console fail on purpose, with a
delay we control, and find the edge.

One side benefit that does not depend on the contingency: passive capture needs
a probe between cartridge and console, and no such thing appears to exist for
AES. A cartridge that measures itself needs no interposer.

## 2. The bootstrap problem

Here is the trap in "the cart displays its own result."

If the cartridge is the thing whose timing we are breaking, and the display
depends on the cartridge working, then **at the moment the measurement
succeeds, the instrument dies.** The 68k executes from P ROM. Serve P ROM too
slowly and the CPU takes garbage as opcodes and crashes. A crashed console
cannot tell you what it crashed at.

You cannot read a result from a machine that just stopped working.

## 3. The way out: split the address space

Do not vary the timing of the code the 68k is running. Vary the timing of data
it is *reading*.

| Region | Timing | Contents |
|---|---|---|
| **Code** | always safe, generous wait states | The test program. Never varied, never fails. |
| **Probe** | swept | A known pattern. Read and compared. |

Now a timing failure is **a wrong value, not a death.** The program reads the
probe region, compares against what it knows should be there, records
pass or fail, and keeps running — because its own instruction fetches were never
at risk. It can then draw the whole table on screen at the end.

That is what makes the on-screen readout work without a laptop, without a
serial port, and without any way for the console to be reset mid-experiment.

**The two regions already exist in hardware**, which is convenient:

- `$000000`–`$0FFFFF` — wait states set by `ROMWAIT`
- `$200000`–`$2FFFFF` — wait states set by `PWAIT0`/`PWAIT1`

`[VERIFIED: docs/prom-banking.md]`

## 4. We already own the coarse knob

From the connector data: `ROMWAIT` (b28), `PWAIT0` (b30) and `PWAIT1` (b31) are
**cartridge outputs**. `[VERIFIED: docs/data/aes-cartridge-pinout.csv]`

The cartridge tells the console how long to wait for it. So the experiment has
two axes and we control both:

| Knob | Range | Source |
|---|---|---|
| **Wait states** — coarse | `ROMWAIT`: 4 or 5 clocks. `PWAIT0/1`: 4 to 7 clocks. | Drive the pins |
| **Added delay** — fine | sub-clock, our own logic | Our own delay line |

Q3 asks what access time a cartridge must meet **for zero added wait states.**
That is: hold `ROMWAIT` at zero, sweep the fine delay, find where the probe
reads wrong. Then repeat for each wait-state setting and produce the whole
table.

That table is the deliverable. Nobody has published it.

## 5. Architecture

```
    AES connector (200 pin)
              |
      level translation          <- 5V both ways; see hardware-constraints.md
              |
    +---------+---------+
    |       FPGA        |
    |                   |
    |  address decode   |        code region  -> answer immediately
    |                   |        probe region -> answer after N delay steps
    |  delay generator  |        PLL-clocked counter
    |  wait-state driver|        ROMWAIT, PWAIT0, PWAIT1
    +---------+---------+
              |
        SRAM or block RAM        code + probe pattern + fix tiles
```

Everything the 68k reads comes from the FPGA. No mask ROMs, no EPROM burning,
and the test program can be changed by reflashing rather than desoldering.

### The fine delay

We do not need picoseconds. A 68k cycle at 12 MHz is about 83 ns, and the answer
we are hunting is somewhere inside it.

- A PLL at 200 MHz gives **5 ns steps** — about 17 steps across a cycle.
- Even 100 MHz and 10 ns steps would bracket the answer usefully.

**Bracketing is the goal, not precision.** "Fails at 60 ns, passes at 50 ns" is
already the most precise public number on this, and it can be refined later.
Chasing 1 ns resolution before we have 10 ns is the wrong order.

### The positive control, again

Same lesson as the fix-layer test: **a result that can only fail one way is
worthless.** At zero added delay with generous wait states, the probe must read
correctly. If it does not, the fault is in our level translation or our decode,
not in the console's timing, and the whole sweep is meaningless.

So the first row of every run is a control at the safest setting, displayed
alongside the results. If the control fails, the run is void and says so.

## 6. What it deliberately is not

A full 200-pin cartridge sounds like Phase 7. It is much less than Phase 7,
because nearly everything expensive is absent:

| Phase 7 needs | Measurement cart needs |
|---|---|
| 65 MB on the CHA side | nothing — no C ROMs |
| 24 MB on the PROG side | kilobytes |
| The sprite serializer | nothing — fix layer only, per Q1 |
| M1 bankswitching | nothing — no Z80 program |
| V ROM and the audio path | nothing |
| Two boards, two memory systems | one small board |

What remains is **the connector, the level translation, and the mechanical
fit** — which are exactly the three things we most need to learn, and the three
that cannot be learned any cheaper.

## 7. It answers a second question for free

[`hardware-constraints.md`](hardware-constraints.md) flags an unknown we cannot
resolve by reading: driving a 5V system from 3.3V logic works only if every
receiver is TTL-threshold at 2.0 V, and the console's receivers are
undocumented SNK ASICs.

A working measurement cart **is** that experiment. If it boots and the control
passes, 3.3V drive works on the pins we drive. If it fails in a way the sweep
cannot explain, we have found the threshold problem — early, on a cheap board,
instead of late on an expensive one.

## 8. Risks, honestly

**The timing sweep itself carries no risk to the console.** Serving data slowly
makes the 68k read garbage, execute nonsense and hang. Power-cycle and it is
fine. A slow read is just a read; nothing is stressed electrically.

**Bus contention is the real risk, and it is unrelated to the experiment.** If
our board drives a line the console is also driving, two outputs fight and both
can be damaged. On a 200-pin connector whose pinout we derived from documents
rather than continuity-tested, a single wrong pin *direction* is what costs
somebody an AES — and that risk is identical whether the board sweeps timing or
merely sits there. It is a cost of building a 200-pin board at all.

Mitigations are the dull ones: series resistors on every driven line, verify
direction on every pin against the schematic *and* by continuity on a real
cartridge, and bring the board up outside the console first. This is also the
argument the roadmap already makes — keep SNK's board between us and the console
for as long as possible.

**It is still a 200-pin 5V edge connector.** That is the part of Phase 7 that
sinks projects, and doing it first means meeting it first. The trade is
deliberate: meet it on a board with nothing else on it, where a failure has one
plausible cause.

**Our own board perturbs what we measure.** Trace length and loading on the
cartridge side are ours, not SNK's. The number we get is "what this console
requires of a board like this one," which is the useful number, but it is not a
universal constant.

**The control could pass while something subtle is wrong.** A marginal signal
that works at room temperature and fails elsewhere would show as a clean pass.
This is one reason not to treat a single console's result as the answer —
Phase 11 exists for a reason.

**One console proves one console.** Everything here needs repeating on other AES
revisions before it is a specification rather than an observation.

## 9. Open questions before this can be built

- **Can the cartridge drive `RESET` (a33)?** The connector data records the pin
  and its polarity, not its direction. If the cart can assert reset, recovery
  from a hard crash becomes automatic and a much more aggressive sweep is
  possible. `[UNVERIFIED]`
- **Which FPGA?** Chosen for I/O count and 5V handling, not logic capacity —
  see `hardware-constraints.md`. Not settled.
- **How much of the connector must be correct for the console to boot at all?**
  If the BIOS probes signals we leave floating, a minimal cart may not run.
  Worth deriving from the connector data before laying out a board.
- **Does the probe region need to be in P at all?** Reading through the fix or
  sprite path would test different buses with different timing. P first, since
  Q3 is a P-ROM question.

## 10. The simulation route, which costs nothing

Most of this can be done in Verilog before any board exists.

NeoGeoFPGA-sim has a real 68000 core (TG68K) and the timing-annotated ROM models
above. Changing `#120` to `#150`, `#200`, `#250` and finding where the simulated
system stops booting is the same sweep, for free, with no hardware and no risk.

**What it can tell us:** whether our understanding of the read cycle is right,
whether 120 ns has margin, and where the *model* puts the edge.

**What it cannot:** the real limit. TG68K is not a cycle-exact 68000, and the
model is schematic-derived — it encodes its author's understanding, which is
part of what we would be testing.

### The harness must run on open inputs

The full system model wants a BIOS and a P ROM. Both are available to us openly:

- **`nullbios`** — ngdevkit's open BIOS replacement, LGPL-3.0-or-later. We
  already use it: the `aes.zip` and `neogeo.zip` our ROM builds copy out of
  ngdevkit's share directory *are* nullbios.
- **Our own P ROMs** — `rom/` and `rom-sound/`.

This is not a workaround for lacking dumps. **It is the point.** A harness that
needs a BIOS dump and a commercial cartridge produces a number nobody can check;
a harness that runs on nullbios and a ROM in this repository produces one anyone
can rerun. Phase 5's value is a measurement the community can use, and
reproducibility is most of that value.

A contributor's own legally obtained dumps are a legitimate *private*
cross-check once the open harness works — validating it against something SNK
actually made. Private input, public conclusion. The dumps still never enter
this repository. See `contributing.md`.

**Caveat:** nullbios does not do everything the real BIOS does — the cartridge
probe, the eye-catcher sequence, the full Z80 handshake. A nullbios simulation
says more about steady-state bus timing than about whether a marginal cartridge
survives startup.

---

## Why it is still worth building eventually

It would produce a number nobody has published, test the level-translation
approach Phase 7 depends on, and answer the ASIC threshold question — on a board
carrying no memory, no serializer and no audio.

But it answers a question the project can route around, and it requires the one
thing most likely to go wrong. **Build the board that works first; measure the
edge afterwards.**

---

*Corrections welcome and actively wanted. Open an issue.*
