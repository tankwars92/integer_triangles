#!/usr/bin/env python3
"""
Usage:
    python3 benchmark.py                 # default: p = 10^e+7, e = 6..9, baseline up to e = 8
    python3 benchmark.py --quick         # about a minute: e = 6..7
    python3 benchmark.py --max-exp 11    # new method up to 10^11+7 (about 2 minutes for e = 11)
    python3 benchmark.py --max-exp 9 --baseline-max-exp 9   # baseline at 10^9+7 takes ~5 minutes
"""
import argparse
import csv
import gc
import json
import os
import platform
import random
import statistics
import sys
import time

import hull
import integer_triangles_perimeter as tri
from integer_triangles_baseline import baseline_tri

SEED_SMALL = 12345      # random p in [400, 2500]
SEED_LARGE = 20261019   # random p in [1e5, 2e6]
EVEN_P = [510510, 360360, 720720, 1000000, 999998, 1234568]


def brute(p):
    ob = ac = rt = 0
    for a in range(1, p):
        for b in range(a, p):
            c = p - a - b
            if c < b:
                break
            if a + b <= c:
                continue
            d = a * a + b * b - c * c
            if d < 0:
                ob += 1
            elif d > 0:
                ac += 1
            else:
                rt += 1
    return ob, rt, ac, ob + rt + ac


def row_sum_total(p):
    t = 0
    for a in range(1, p // 3 + 1):
        blo = max(a, (p - 2 * a) // 2 + 1)
        bhi = (p - a) // 2
        if bhi >= blo:
            t += bhi - blo + 1
    return t


def environment():
    return {
        "python": sys.version.replace("\n", " "),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "perf_counter_resolution": time.get_clock_info("perf_counter").resolution,
        "seed_small": SEED_SMALL,
        "seed_large": SEED_LARGE,
        "direct_sum_threshold": 30000,
    }


def check(name, ok, log):
    log.append({"check": name, "passed": bool(ok)})
    print("  [%s] %s" % ("PASS" if ok else "FAIL", name), flush=True)
    return ok


def correctness(quick):
    log = []
    ok = True
    # 1. All p < 400 against direct enumeration.

    bad = [p for p in range(1, 400) if tri.tri_counts(p) != brute(p)]
    ok &= check("p = 1..399 equals direct enumeration (bad: %s)" % bad[:5], not bad, log)

    # 2. 150 random p in [400, 2500] against direct enumeration.
    rng = random.Random(SEED_SMALL)
    ps = [rng.randint(400, 2500) for _ in range(150 if not quick else 40)]
    bad = [p for p in ps if tri.tri_counts(p) != brute(p)]
    ok &= check("%d random p in [400,2500] equal direct enumeration (bad: %s)" % (len(ps), bad[:5]), not bad, log)

    # 3. Closed form of the total against the exact row sum, p < 6000.
    bad = [p for p in range(1, 6000) if tri.total_tri(p) != row_sum_total(p)]
    ok &= check("closed form for total number of triangles, p < 6000 (bad: %s)" % bad[:5], not bad, log)

    # 4. Large p against the O(p) baseline (kernel is used above ~1e5).
    rng = random.Random(SEED_LARGE)
    ps = [10 ** 5, 10 ** 5 + 1, 123457, 200000, 333333, 500000, 10 ** 6, 10 ** 6 + 3]
    ps += [rng.randint(10 ** 5, 2 * 10 ** 6) for _ in range(20 if not quick else 6)]
    bad = [p for p in ps if tri.tri_counts(p) != baseline_tri(p)]
    ok &= check("%d values 1e5 <= p <= 2e6 equal the O(p) baseline (bad: %s)" % (len(ps), bad[:5]), not bad, log)

    # 5. Even p with right triangles.
    ev = EVEN_P if not quick else EVEN_P[:3]
    bad = [p for p in ev if tri.tri_counts(p) != baseline_tri(p)]
    rights = {p: tri.tri_counts(p)[1] for p in ev}
    ok &= check("even p %s equal the baseline; right-triangle counts %s" % (ev, rights), not bad, log)

    return ok, log


def timed(fn, p, repeats):
    gc.disable()
    try:
        times = []
        res = None
        for _ in range(repeats):
            t = time.perf_counter()
            res = fn(p)
            times.append(time.perf_counter() - t)
    finally:
        gc.enable()
    return res, times


def repeats_for(e):
    return 5 if e <= 7 else (3 if e == 8 else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-exp", type=int, default=6)
    ap.add_argument("--max-exp", type=int, default=9, help="largest e for the new method, p = 10^e + 7")
    ap.add_argument("--baseline-max-exp", type=int, default=8, help="largest e for the O(p) baseline")
    ap.add_argument("--quick", action="store_true", help="fewer checks, e up to 7")
    ap.add_argument("--skip-checks", action="store_true")
    ap.add_argument("--out", default="benchmark_results")
    args = ap.parse_args()
    if args.quick:
        args.max_exp = min(args.max_exp, 7)
        args.baseline_max_exp = min(args.baseline_max_exp, 7)

    env = environment()
    print("Environment:")
    for k, v in env.items():
        print("  %s: %s" % (k, v))
    print()

    checks = []
    if not args.skip_checks:
        print("Correctness checks:")
        ok, checks = correctness(args.quick)
        print("All checks passed.\n" if ok else "SOME CHECKS FAILED.\n", flush=True)
        if not ok:
            sys.exit(1)

    rows = []
    print("Timing (p = 10^e + 7):")
    print("%4s %14s %12s %12s %9s %12s" % ("e", "baseline,s", "new,s", "new min,s", "speedup", "ops(new)"))
    for e in range(args.min_exp, args.max_exp + 1):
        p = 10 ** e + 7
        rep = repeats_for(e)
        tri.OPS[0] = 0
        hull.STEPS[0] = 0
        res_new, tn = timed(tri.tri_counts, p, 1)
        ops = tri.OPS[0]
        if rep > 1:
            _, more = timed(tri.tri_counts, p, rep - 1)
            tn += more
        row = {"e": e, "p": p, "obtuse": res_new[0], "right": res_new[1], "acute": res_new[2], "total": res_new[3],
               "new_median_s": statistics.median(tn), "new_min_s": min(tn), "new_repeats": rep, "ops_terms_plus_steps": ops}
        if e <= args.baseline_max_exp:
            res_b, tb = timed(baseline_tri, p, rep)
            row.update({"baseline_median_s": statistics.median(tb), "baseline_min_s": min(tb),
                        "baseline_repeats": rep, "match_baseline": res_b == res_new})
            if res_b != res_new:
                print("MISMATCH at p=%d: baseline %s new %s" % (p, res_b, res_new))
                sys.exit(1)
        rows.append(row)
        bs = ("%.4f" % row["baseline_median_s"]) if "baseline_median_s" in row else "-"
        sp = ("%.1fx" % (row["baseline_median_s"] / row["new_median_s"])) if "baseline_median_s" in row else "-"
        print("%4d %14s %12.4f %12.4f %9s %12d" % (e, bs, row["new_median_s"], row["new_min_s"], sp, ops), flush=True)

    print("\nGrowth per decade (new method): time ratio, ops ratio")
    for a, b in zip(rows, rows[1:]):
        if a["new_median_s"] > 0:
            print("  e %d -> %d: time x%.2f, ops x%.2f" % (a["e"], b["e"], b["new_median_s"] / a["new_median_s"],
                                                           b["ops_terms_plus_steps"] / max(1, a["ops_terms_plus_steps"])))


if __name__ == "__main__":
    main()
