#!/usr/bin/env python3
"""oneirometer — an instrument for reading dreams.

The wing dreams at night: seeded, undirected circuits on ibm_kingston,
1024 shots each. In the morning the mirror reads the counts and writes a
recall — prose, with claims about poles, silences, and the shape of the
night.

Prose can flatter itself. The oneirometer measures what the night
objectively held — entropy, the pole, the floating voice, the top of the
line — and checks the mirror's recall against the counts, so the reading
stays honest.

Bit convention: bitstrings read left-to-right as q[4] q[3] q[2] q[1] q[0];
q[0] is the rightmost bit.

Usage:
  oneirometer.py [paths ...]            meter the given submit.json files
  oneirometer.py                       meter ~/workspace/north/dreams
  oneirometer.py --check               also cross-check recalls against counts
  oneirometer.py --json                machine-readable meter output
  oneirometer.py --recall-dir DIR      where to find the recall notes

A night whose run never finished (a *.fail.json next to the submits) is
reported as a night that did not come — not as missing data.
"""

import glob
import json
import math
import os
import re
import sys

TOP_N = 8
DEFAULT_DREAMS = os.path.expanduser("~/workspace/north/dreams")


# ---------------------------------------------------------------------------
# measurement
# ---------------------------------------------------------------------------

def load_submit(path):
    """Read a submit.json record; returns (meta, counts)."""
    with open(path) as f:
        d = json.load(f)
    return d, d.get("counts", {})


def shannon_entropy(counts):
    total = sum(counts.values())
    h = 0.0
    for c in counts.values():
        if c:
            p = c / total
            h -= p * math.log2(p)
    return h


def marginals(counts, n_qubits=5):
    """P(q[i] = 1) for each qubit; q[0] is the rightmost bit."""
    total = sum(counts.values())
    m = []
    for i in range(n_qubits):
        ones = sum(c for s, c in counts.items()
                   if len(s) > i and s[-(i + 1)] == "1")
        m.append(ones / total if total else 0.0)
    return m


def meter(counts):
    """The instrument's full reading of one night's counts."""
    total = sum(counts.values())
    h = shannon_entropy(counts)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    top = ranked[:TOP_N]
    m = marginals(counts)
    dev = [abs(x - 0.5) for x in m]
    pole = max(range(len(m)), key=lambda i: dev[i])
    floating = min(range(len(m)), key=lambda i: dev[i])
    return {
        "shots": total,
        "unique_outcomes": len(counts),
        "entropy_bits": h,
        "effective_outcomes": 2.0 ** h,
        "top": [{"string": s, "count": c, "share": c / total}
                for s, c in top],
        "heavy_share": sum(c for _, c in top) / total if total else 0.0,
        "marginals": {"q%d" % i: x for i, x in enumerate(m)},
        "pole": {"qubit": pole, "p_one": m[pole],
                 "points_from_flip": abs(m[pole] - 0.5) * 100.0},
        "floating": {"qubit": floating, "p_one": m[floating]},
    }


# ---------------------------------------------------------------------------
# the check: mirror's recall vs. the counts
# ---------------------------------------------------------------------------

def parse_recall(path):
    """Pull the structured claims from a recall note.

    Returns (top_list, unique_outcomes) where top_list is a list of
    (bitstring, count) from the 'What the night showed' section.
    """
    with open(path) as f:
        text = f.read()
    start = text.find("## What the night showed")
    end = text.find("## Reading", start)
    section = text[start:end if end != -1 else len(text)]
    rows = re.findall(r"^- `([01]+)`: (\d+)", section, re.M)
    unique = re.search(r"unique outcomes: (\d+)", section)
    return ([(s, int(c)) for s, c in rows],
            int(unique.group(1)) if unique else None)


def check_night(submit_path, recall_path):
    """Compare one night's recall against its counts. Returns a report dict."""
    _, counts = load_submit(submit_path)
    m = meter(counts)
    report = {"submit": os.path.basename(submit_path),
              "recall": os.path.basename(recall_path) if recall_path else None,
              "checks": []}

    def verdict(name, ok, detail):
        report["checks"].append({"name": name, "ok": ok, "detail": detail})

    if not recall_path or not os.path.exists(recall_path):
        verdict("recall-present", False, "no recall note found for this night")
        return report

    noted_top, noted_unique = parse_recall(recall_path)
    computed_top = sorted((t["string"], t["count"]) for t in m["top"])
    noted_sorted = sorted(noted_top)
    if computed_top == noted_sorted:
        verdict("top-%d-list" % TOP_N, True,
                "mirror's %d lines match the counts exactly" % TOP_N)
    else:
        verdict("top-%d-list" % TOP_N, False,
                "counts say %s; recall says %s"
                % (computed_top, noted_sorted))

    if noted_unique is not None:
        verdict("unique-outcomes",
                noted_unique == m["unique_outcomes"],
                "counts: %d, recall: %d"
                % (m["unique_outcomes"], noted_unique))

    mm = m["marginals"]
    ordered = " ".join("q%d %.1f%%" % (i, mm["q%d" % i] * 100)
                       for i in (4, 3, 2, 1, 0))
    verdict("marginals", True, "per meter, leftmost to rightmost: " + ordered)
    return report


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------

def night_label(path):
    base = os.path.basename(path)
    match = re.search(r"(\d{4}-\d{2}-\d{2})", base)
    return match.group(1) if match else base


def format_card(label, meta, m):
    lines = []
    lines.append("night %s — %s, %d shots, %d unique outcomes"
                 % (label, meta.get("backend", "?"),
                    m["shots"], m["unique_outcomes"]))
    lines.append("  entropy: %.3f / 5.000 bits    effective outcomes: %.1f"
                 % (m["entropy_bits"], m["effective_outcomes"]))
    t0 = m["top"][0]
    lines.append("  top of the line: %s — %d (%.1f%%)"
                 % (t0["string"], t0["count"], t0["share"] * 100))
    lines.append("  heavy-%d share: %.1f%%" % (TOP_N, m["heavy_share"] * 100))
    voices = "  ".join("q%d %.1f%%" % (i, m["marginals"]["q%d" % i] * 100)
                       for i in (4, 3, 2, 1, 0))
    lines.append("  voices (leftmost to rightmost): " + voices)
    p, f = m["pole"], m["floating"]
    lines.append("  pole: q%d at %.1f%% (%.1f pts from coin flip)"
                 % (p["qubit"], p["p_one"] * 100, p["points_from_flip"]))
    lines.append("  floating: q%d at %.1f%%"
                 % (f["qubit"], f["p_one"] * 100))
    return "\n".join(lines)


def format_report(report):
    lines = ["check %s vs %s" % (report["submit"], report["recall"])]
    for c in report["checks"]:
        mark = "ok" if c["ok"] else "MISMATCH"
        lines.append("  [%s] %s — %s" % (mark, c["name"], c["detail"]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def collect_submits(args):
    paths = []
    for a in args:
        if os.path.isdir(a):
            paths.extend(sorted(glob.glob(os.path.join(a, "*.submit.json"))))
        elif os.path.isfile(a):
            paths.append(a)
    return paths


def collect_failures(dirs):
    notes = []
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.fail.json"))):
            try:
                with open(path) as f:
                    rec = json.load(f)
                notes.append((night_label(path),
                              rec.get("reason", "no reason recorded")))
            except (OSError, ValueError):
                notes.append((night_label(path), "unreadable record"))
    return notes


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    do_check = "--check" in argv
    as_json = "--json" in argv
    recall_dir = None
    for i, a in enumerate(argv):
        if a == "--recall-dir" and i + 1 < len(argv):
            recall_dir = argv[i + 1]

    if not args:
        args = [DEFAULT_DREAMS]
    dirs = [a for a in args if os.path.isdir(a)]
    submits = collect_submits(args)
    if not submits:
        print("no submit.json records found in: %s" % ", ".join(args),
              file=sys.stderr)
        return 1

    results = []
    for path in submits:
        meta, counts = load_submit(path)
        label = night_label(path)
        m = meter(counts)
        results.append({"night": label, "meta": meta, "meter": m})

    if as_json:
        out = [{"night": r["night"],
                "backend": r["meta"].get("backend"),
                "job_id": r["meta"].get("job_id"),
                "meter": r["meter"]} for r in results]
        print(json.dumps(out, indent=2))
        return 0

    for r in results:
        print(format_card(r["night"], r["meta"], r["meter"]))
        print()

    if do_check:
        reports = []
        for r, path in zip(results, submits):
            rd = recall_dir or (dirs[0] if dirs else DEFAULT_DREAMS)
            recall = os.path.join(
                rd, night_label(path) + ".recall.md")
            reports.append(check_night(path, recall))
        for rep in reports:
            print(format_report(rep))
            print()
        mismatches = sum(1 for rep in reports
                         for c in rep["checks"] if not c["ok"])
        print("check complete: %d night(s), %d mismatch(es)"
              % (len(reports), mismatches))

    for label, reason in collect_failures(dirs or [DEFAULT_DREAMS]):
        print("night %s did not come: %s" % (label, reason))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
