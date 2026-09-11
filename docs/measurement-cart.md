# The measurement cartridge

A cartridge whose job is to find out how slow a cartridge is allowed to be.

This is NeoForge's answer to [Q3](open-questions.md) and the first board the
project builds. It is a design on paper — nothing here has been made.

---

## 1. Why the obvious approach does not work

The roadmap's Phase 5 says: instrument a working cartridge, capture read cycles,
measure access times. That is a reasonable thing to do and it will not answer
the question.

**Watching a working cartridge tells you the mask ROM was fast enough.** It
gives you that ROM's access time. It does not tell you how slow a cartridge
could be and still boot — which is the number a board designer needs, because it
is the budget everything else is spent from.

To find a limit you have to reach it. That means **making the console fail on
purpose**, with a delay we control, and finding the edge.

There is a second problem with passive capture, which
[`hardware-constraints.md`](hardware-constraints.md) raised: it needs a probe
that sits between cartridge and console, and no such thing appears to exist for
AES. A cartridge that measures itself needs no interposer at all.

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

---

## Why this is the right first board

It produces the measurement Phase 5 exists for, tests the level-translation
approach Phase 7 depends on, and answers the ASIC threshold question — on a
board carrying no memory, no serializer and no audio.

If the project stopped after it, the published timing table would still be
worth more to the community than anything else NeoForge has made.

---

*Corrections welcome and actively wanted. Open an issue.*
