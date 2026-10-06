# Getting boards made

**Status:** reference · opened 2026-10-06 · nothing ordered yet

How a design becomes physical boards, what we send, and which of the two
manufacturing models board zero should use.

---

## 1. The two models

**Bare PCB fabrication.** You upload Gerber files and a drill file; they ship
blank boards. No components are fitted. This is what JLCPCB, PCBWay, OSH Park
and everyone else does cheaply, in 5-piece minimums, in about a week.

**PCB assembly (PCBA).** The same fab also places and solders the parts. Two
variants, and the difference matters:

| | Who supplies the parts | Good for |
|---|---|---|
| **Fab-sourced** | they pull from their own component library | common passives and jellybean ICs |
| **Consigned** | **you ship them your components** | anything they do not stock |

So yes — the thing you guessed at is real. **Consigned assembly is a normal
service**, and it is how anyone building a board around an unusual part gets it
assembled. It costs more per board and carries handling and minimum fees.

## 2. For board zero: bare PCB, assembled by hand

**Recommendation, and it is not close.**

[`board-zero.md`](board-zero.md) §6 is two flash chips in **through-hole PLCC
sockets**, four 0805 resistors, two 0805 capacitors and one bulk cap. Against
that:

- **Assembly setup costs dwarf the bill of materials.** A stencil and feeder
  setup is tens of dollars before a single board; the parts are about $20.
- **The sockets are the point.** The flash has to come *out* to be
  reprogrammed, so the chips go in by hand whatever happens. An assembly house
  would solder two sockets and seven passives.
- **A first board gets reworked.** Hand assembly means a mistake is a
  desoldering job, not a new order.
- It is, deliberately, about the friendliest board anyone could learn to solder
  on: nothing fine-pitch, nothing with hidden joints, no BGA.

**Assembly becomes worth paying for later** — a revision carrying an FPGA or
CPLD in TQFP, or a run of kits to sell. At that point consigned parts matter,
because neither a Furrtek replacement board nor anything SNK ever made is in a
fab's component library.

## 3. What we actually send

From KiCad, once the board is laid out:

| File set | KiCad menu |
|---|---|
| **Gerbers** — one per layer, plus solder mask, silkscreen and board outline | File → Plot |
| **Drill file** (Excellon) | File → Plot → Generate Drill Files |

Zip them together and upload. Most fabs now also accept the `.kicad_pcb`
directly, but Gerbers are the thing every fab agrees on and the thing we should
keep in the repository as the released artifact.

**Their DFM review is a free second pair of eyes** — it catches clearance
violations, a missing outline, drill sizes below their minimum. It will **not**
catch a wrong connector pitch. Nothing catches that except
[`card-edge.md`](card-edge.md).

## 4. Gold fingers: the rules, which we did not have

`[VERIFIED: JLCPCB gold-finger documentation, read 2026-10-06]` —
[`board-zero.md`](board-zero.md) §9 listed these as `[UNVERIFIED]`.

| Rule | Consequence for us |
|---|---|
| Gold fingers require **ENIG**. HASL will just tin them | order ENIG |
| Bevel available at **30°** or **45°**; **30° is recommended** for easier insertion | measure the real cartridge's bevel before choosing — [`card-edge.md`](card-edge.md) §4 |
| A bevel removes about **1/3 to 1/2 of board thickness** | on 1.6 mm that is 0.53–0.8 mm, a figure our own measurement can check |
| **Chamfering is unavailable on boards smaller than 50 × 50 mm**, and a board with gold fingers must be at least 50 mm on a side | fine — our finger field alone is ~124 mm |
| The gold finger area must have the **solder mask fully opened** | a footprint detail, easy to get wrong |
| **No copper in the bevel region** — it gets machined away | constrains how far the fingers run to the edge |
| Not available where v-cut scoring would put fingers mid-board | we are not panelising |

Pricing is not published; gold fingers are a paid option and the quote shows it
at order time.

## 5. The order, for board zero

| Parameter | Value |
|---|---|
| Layers | 2 |
| Thickness | **1.6 mm** `[MEASURED: 1.55 mm bare, 1.65 mm across a finger]` |
| Surface finish | **ENIG** (required by gold fingers) |
| Gold fingers | **yes** |
| Bevel | **30°**, pending the measurement |
| Quantity | 5 — the minimum, and more than we need |
| Panelising | none |

## 6. Sequencing: do not order yet

Three things come first, and the first two are free:

1. **The remaining card-edge numbers** — [`card-edge.md`](card-edge.md) §2, and
   the full 124.46 mm field check. A board ordered on a wrong pitch is scrap.
2. **The two connector spacings** —
   [`teardown-aes-console.md`](teardown-aes-console.md) §4. Board zero is
   PROG-only so it needs just one edge, but the outline still has to clear the
   shell.
3. **The footprint generated from the CSV**, so it cannot drift from the
   measurements, the way the symbol and schematic already are.

**Order 5, expect to use 2 or 3.** The first article is for checking against the
cartridge and the console slot *without any chips fitted* — it either slides in
or it does not, and that costs nothing to find out.
