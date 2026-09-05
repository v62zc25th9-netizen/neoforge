# Contributing to NeoForge

NeoForge is an open-source Neo Geo **AES** cartridge research and development
project. It is early, it is small, and the most useful contributions right now
are corrections rather than code.

## The one rule that matters

**Every technical claim carries an evidence marker.** Neo Geo hardware is old,
thinly documented in mainstream sources, and surrounded by confident
misinformation — Wikipedia's explanation of MVS/AES cartridge incompatibility
is simply wrong. So:

- `[VERIFIED: <source>]` — backed by wiki.neogeodev.org, a schematic, published
  vendor specs, or reverse-engineered source
- `[ANECDOTAL: <source>]` — forum reports, single-user experience
- `[UNVERIFIED]` — inference or reasoning not yet externally confirmed
- `[MEASURED: <date>]` — our own scope capture or bench test

Reasoning your way to a conclusion does not promote it to `[VERIFIED]`. If you
are not sure, mark it `[UNVERIFIED]` and say so in the PR — that is a
contribution, not a weakness.

See `CLAUDE.md` for the full convention.

## Highest-value contributions right now

1. **Corrections.** If something in `docs/` is wrong, open an issue even
   without a fix. Being wrong in public is how this project stays honest.
2. **Prior art we missed.** `docs/prior-art.md` is a living directory. An
   `[UNVERIFIED]` one-line entry for a project we have not heard of is worth
   more than a polished paragraph about one we have.
3. **Measurements.** If you own AES hardware and a logic analyzer, captures of
   real cartridge bus activity are the single thing this project most needs and
   least has. See roadmap Phase 5.
4. **Hardware review.** If you have designed for a 5V edge connector or worked
   with SNK silicon, telling us what is about to go wrong saves months.
5. **Emulator and toolchain work.** Phases 1 and 2 are pure software and need
   no hardware at all.

## What we cannot accept

- **ROM data of any kind.** No copyrighted ROMs, no fragments, no encrypted
  blobs, no "just for testing." Development uses homebrew, public-domain
  software, or contributors' own legally obtained dumps, and none of it lives
  in this repository.
- **Code copied from closed products** or from decompiled commercial firmware.
- **Reused open-source code without license review.** Much relevant work is
  GPL-2.0 or GPL-3.0, which is not automatically compatible with this repo's
  current license. Flag the origin and license of anything you derive from, and
  we will sort out compatibility before merging rather than after.

## Licensing note

The repository is currently MIT. That is appropriate for HDL, firmware and
tooling, and a poor fit for PCB files, where CERN-OHL-S or CERN-OHL-W is the
norm. **This split has not been made yet.** If you intend to contribute
hardware design files, open an issue first so we resolve licensing before your
work lands.

## Workflow

1. Open an issue describing what you want to change, unless it is a typo.
2. Fork, branch, and open a pull request.
3. Keep pull requests to one topic.
4. In the PR description, state your sources — and state where you are guessing.

## Tone

Say "I don't know." Say "the wiki and this forum thread disagree." Say "this
worked on my board and I have not tested another." A project built on measured
uncertainty will outlast one built on confident guesses.
