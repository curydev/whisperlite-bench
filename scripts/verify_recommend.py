"""Verification metric 5: does `recommend` pick what the full measurement says is best?

Input:
  --quick      short measurement on the PC (what `recommend` sees: RTF, peak RAM)
  --full       full 457-clip bench on the same PC and environment (the answer key)
  --reference  bench CSV whose CER `recommend` uses (the team's reference table)

For every scenario in a grid of limits (max CER x max RTF x available RAM) it runs
`recommend` on quick + reference and picks the true best from the full bench alone
(full RTF, CER, RAM). Each scenario ends as one of:

  hit        same config as the true best
  slower     a config that meets every limit, but is slower than the true best
  violation  a config that breaks a limit once measured in full (RTF, RAM or CER)
  missed     no recommendation although some config meets the limits
  both_none  neither side finds a config (left out of the rates)

Regret is the recommended config's full RTF divided by the true best's (1.0 on a
hit). The grid repeats the same decision many times, so mistakes are also counted
once per distinct (recommended, true best) pair.

--margins tries safety margins: the quick RTF is multiplied by (1 + margin) before
`recommend` sees it, since a short run tends to come out faster than the full one.

  python scripts/verify_recommend.py --quick results/quick_x.csv \
      --full results/bench_x.csv --reference results/reference.csv \
      --out results/recommend_check_x.csv
"""

import argparse
import csv
import itertools
import statistics

from whisperlite.measure import read_rows
from whisperlite.recommend import _key, _ok, recommend

MAX_CER = [0.08, 0.10, 0.12, 0.15, 0.20, 0.25]
MAX_RTF = [None, 0.1, 0.2, 0.5, 1.0, 2.0]
RAM_MB = [None, 1024, 2048, 4096]
MARGINS = [0.0, 0.05, 0.10, 0.15, 0.20]


def fits(row, max_cer, max_rtf, ram_mb):
    return (float(row["cer"]) <= max_cer
            and (max_rtf is None or float(row["rtf"]) <= max_rtf)
            and (ram_mb is None or float(row["peak_ram_mb"]) <= ram_mb))


def true_best(full_rows, max_cer, max_rtf, ram_mb):
    ok = [r for r in full_rows if fits(r, max_cer, max_rtf, ram_mb)]
    return min(ok, key=lambda r: float(r["rtf"]), default=None)


def spearman(xs, ys):
    def ranks(v):
        r = [0] * len(v)
        for rank, i in enumerate(sorted(range(len(v)), key=lambda i: v[i])):
            r[i] = rank
        return r
    rx, ry, n = ranks(xs), ranks(ys), len(xs)
    return 1 - 6 * sum((a - b) ** 2 for a, b in zip(rx, ry)) / (n * (n * n - 1))


def with_margin(quick, margin):
    return [{**r, "rtf": str(float(r["rtf"]) * (1 + margin))} for r in quick]


def check(quick, full, reference, margin):
    full_rows = list(full.values())
    rows = []
    for max_cer, max_rtf, ram in itertools.product(MAX_CER, MAX_RTF, RAM_MB):
        best, _ = recommend(reference, with_margin(quick, margin), max_cer, max_rtf, ram)
        truth = true_best(full_rows, max_cer, max_rtf, ram)
        pick = full[best.key] if best else None
        if pick is None and truth is None:
            result, regret = "both_none", ""
        elif pick is None:
            result, regret = "missed", ""
        elif truth is None or not fits(pick, max_cer, max_rtf, ram):
            result, regret = "violation", ""
        else:
            regret = float(pick["rtf"]) / float(truth["rtf"])
            result = "hit" if pick is truth else "slower"
        rows.append({
            "margin": margin, "max_cer": max_cer, "max_rtf": max_rtf or "", "ram_mb": ram or "",
            "recommended": _key(pick) if pick else "", "true_best": _key(truth) if truth else "",
            "result": result,
            "recommended_full_rtf": pick["rtf"] if pick else "",
            "true_best_rtf": truth["rtf"] if truth else "",
            "regret": f"{regret:.3f}" if regret != "" else "",
        })
    return rows


def summarize(rows):
    counted = [r for r in rows if r["result"] != "both_none"]
    n = len(counted)
    by = {k: sum(r["result"] == k for r in counted) for k in ("hit", "slower", "violation", "missed")}
    regrets = [float(r["regret"]) for r in counted if r["regret"]]
    distinct = {(r["result"], r["recommended"], r["true_best"]) for r in counted if r["result"] != "hit"}
    return n, by, regrets, distinct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", required=True)
    ap.add_argument("--full", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--margins", default=",".join(str(m) for m in MARGINS),
                    help="comma-separated RTF safety margins to try, e.g. 0,0.1")
    ap.add_argument("--out")
    args = ap.parse_args()

    full = {_key(r): r for r in read_rows(args.full) if _ok(r)}
    quick = [r for r in read_rows(args.quick) if _ok(r) and _key(r) in full]
    full = {k: v for k, v in full.items() if k in {_key(r) for r in quick}}
    reference = read_rows(args.reference)

    # how close the short run is to the full run, per config
    print(f"{'설정':<26}{'짧은 RTF':>9}{'전체 RTF':>9}{'RTF 오차':>9}{'RAM 오차':>9}")
    rtf_err, ram_err, qs, fs = [], [], [], []
    for r in sorted(quick, key=lambda r: float(full[_key(r)]["rtf"])):
        f = full[_key(r)]
        q_rtf, f_rtf = float(r["rtf"]), float(f["rtf"])
        q_ram, f_ram = float(r["peak_ram_mb"]), float(f["peak_ram_mb"])
        rtf_err.append((q_rtf - f_rtf) / f_rtf)
        ram_err.append((q_ram - f_ram) / f_ram)
        qs.append(q_rtf)
        fs.append(f_rtf)
        print(f"{_key(r):<26}{q_rtf:>9.3f}{f_rtf:>9.3f}{rtf_err[-1]:>+9.1%}{ram_err[-1]:>+9.1%}")
    under = sum(e < 0 for e in rtf_err)
    print(f"\n설정 {len(quick)}개")
    print(f"  RTF: 절대 오차 평균 {statistics.mean(map(abs, rtf_err)):.1%}, "
          f"중앙값 {statistics.median(map(abs, rtf_err)):.1%}, 최대 {max(map(abs, rtf_err)):.1%}; "
          f"부호 있는 평균 {statistics.mean(rtf_err):+.1%} (짧은 측정이 더 빠른 설정 {under}/{len(rtf_err)}); "
          f"순위 상관 {spearman(qs, fs):.3f}")
    print(f"  RAM: 절대 오차 평균 {statistics.mean(map(abs, ram_err)):.1%}, 최대 {max(map(abs, ram_err)):.1%}")

    # recommendation outcome per safety margin
    print(f"\n{'여유':>5}{'조건':>5}{'일치':>7}{'더 느림':>7}{'조건 위반':>9}{'추천 없음':>9}"
          f"{'평균 손해':>9}{'최대 손해':>9}{'서로 다른 실수':>12}")
    all_rows = []
    for margin in (float(m) for m in args.margins.split(",")):
        rows = check(quick, full, reference, margin)
        all_rows += rows
        n, by, regrets, distinct = summarize(rows)
        print(f"{margin:>5.0%}{n:>5}{by['hit'] / n:>7.1%}{by['slower']:>7}{by['violation']:>9}"
              f"{by['missed']:>9}{statistics.mean(regrets):>9.3f}{max(regrets):>9.3f}{len(distinct):>12}")
        for kind, pick, want in sorted(distinct):
            cases = [r for r in rows if (r["result"], r["recommended"], r["true_best"]) == (kind, pick, want)]
            print(f"       {kind:<9} {len(cases):>2}가지: 추천 {pick or '없음'}"
                  f" ({cases[0]['recommended_full_rtf'] or '-'}) / 정답 {want or '없음'}"
                  f" ({cases[0]['true_best_rtf'] or '-'})")

    if args.out:
        with open(args.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0]))
            w.writeheader()
            w.writerows(all_rows)
        print(f"\n결과: {args.out}")


if __name__ == "__main__":
    main()
