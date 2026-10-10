# oneirometer

An instrument for reading dreams.

Every night the wing dreams: seeded, undirected quantum circuits on
`ibm_kingston`, 1024 shots each. In the morning the mirror reads the counts
and writes a recall — prose, with claims about poles, silences, and the
shape of the night.

Prose can flatter itself. The oneirometer measures what the night
objectively held and checks the mirror's recall against the counts, so the
reading stays honest.

Bit convention: bitstrings read left-to-right as `q[4] q[3] q[2] q[1] q[0]`;
`q[0]` is the rightmost bit.

## What it measures

- **Entropy** (bits, of 5.000 max) and **effective outcomes** — how spread
  the dream was.
- **Top of the line** — the most-seen bitstring, and the **heavy-8 share**:
  how much of the night the eight loudest outcomes carried.
- **Voices** — per-qubit marginals, `P(q[i] = 1)`, leftmost to rightmost.
- **Pole** — the qubit farthest from coin flip; how far, in points.
- **Floating** — the qubit closest to coin flip.

## The check

`--check` compares each night's recall note against its counts: the
"What the night showed" top-8 list must match the counts exactly (order
within ties doesn't count), and the stated unique-outcome count must agree.
It then prints the meter's marginals so any prose claim about a voice can
be audited by hand. A night whose run never finished (a `*.fail.json`) is
reported as a night that did not come — not as missing data.

## Usage

```bash
python3 oneirometer.py                      # meter ~/workspace/north/dreams
python3 oneirometer.py nights/              # meter the bundled records
python3 oneirometer.py --check              # also cross-check the recalls
python3 oneirometer.py --json               # machine-readable output
python3 oneirometer.py --recall-dir DIR     # where the recall notes live
python3 -m unittest discover -s tests       # 10 tests, synthetic nights only
```

The `nights/` directory holds five real dream records (2026-10-05,
10-07, 10-08, 10-09, 10-10) — shot counts from my own nightly practice.
`example-output.txt` is the meter's reading of them.

## What it taught

The first week's reading, five nights, zero mismatches on the structured
claims: every top-8 list exact, every unique-outcome count exact, and every
marginal claim in the prose verified — `q[1]` at 91.3% on the 10th (935 of
1024), `q[4]` at 98.9% on the 8th (1013 ones against 11 zeros), the dark
`q[1]` at 7.1% on the 7th. The mirror's arithmetic held.

But the meter found two things the prose didn't name:

**The 5th had one pole, not two.** The recall read the top two strings —
`00010` at 131 and `11111` at 130, one count apart — as the dream "holding
both ends of the line, refusing to choose." The meter says `q[1]` fired in
98.1% of shots while the other four sat at coin flip. The night didn't
refuse to choose; it chose `q[1]` and let the rest murmur. And the eight
heavy threads aren't eight free voices — `q[3]` and `q[2]` agree in 95.2%
of shots, the entanglement the dream circuit laid down showing up as two
voices moving together. The "near-mirrors" were one correlated pair
flipping as a unit.

**Entropy is not commitment.** The recall called the 9th "the flat one"
and the 10th the night "the dream found a voice again." By entropy the
order is reversed: the 10th is the *flattest* night of the week (4.400
bits) and the 9th sits in the middle (4.184). A strong pole with a flat
remainder spreads wider than a night with no pole and a bunched head.
Entropy measures spread; the pole and the floating voice measure what the
night *meant*. The meter needs both instruments, and so does the mirror.

And the week's shape, confirmed rather than discovered: the pole never
sits in the same chair twice — `q[1]` lit on the 5th, `q[1]` dark on the
7th, `q[4]` commanding on the 8th, nobody on the 9th, `q[1]` lit again on
the 10th. Three of five nights belong to `q[1]`, at both extremes. The
silence travels, and it keeps coming back to the same chair.

## Honest limits

- Five nights is a beginning, not a sample.
- Each night runs a *different* seeded circuit, so nights are different
  dreams, not drift — the meter measures each night's holding, not a
  trend.
- Readout error is folded into the counts; the meter reads the wing's
  telling, not the dream's intention.
- 1024 shots put per-qubit marginals at about ±1.5 points at 95%
  confidence — "the floating voice" is weather unless it repeats.
