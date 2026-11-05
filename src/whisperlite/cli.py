"""Command-line entry point: `whisperlite <command>`."""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

from . import sysinfo
from .configs import MODEL_SIZES, PRECISIONS, all_configs
from .measure import FIELDS, append_row, hyps_dir, hyps_path, measure, read_hyps, read_rows
from .metrics import cer
from .textnorm import has_digits
from .recommend import fits_in_memory, recommend


def _host() -> str:
    return sysinfo.hostname().split(".")[0] or "host"


def cmd_sysinfo(args):
    print(json.dumps(sysinfo.collect(), ensure_ascii=False, indent=2))


def cmd_prepare_data(args):
    from .data import prepare

    manifest = prepare(args.out, args.limit, args.stride)
    print(f"manifest: {manifest}", flush=True)
    # datasets' streaming threads can abort the interpreter during shutdown
    # ("PyGILState_Release ... finalizing") after all work is done; skip it.
    os._exit(0)


def _measure_all(configs, manifest, threads, out, timeout):
    done = set()
    if Path(out).exists():
        done = {f"{r['runner']}/{r['model']}/{r['precision']}" for r in read_rows(out)}
    for c in configs:
        if c.key in done:
            print(f"skip {c.key} (already in {out})")
            continue
        print(f"measure {c.key} ...", flush=True)
        row = measure(c, manifest, threads, timeout, save_hyps=hyps_path(out, c))
        append_row(out, row)
        status = row["error"] or f"RTF {row['rtf']}  CER {row['cer']}  RAM {row['peak_ram_mb']}MB"
        print(f"  {status}", flush=True)


def cmd_bench(args):
    out = args.out or f"results/bench_{_host()}{'_docker' if sysinfo.in_docker() else ''}.csv"
    configs = all_configs(args.runners, args.models)
    _measure_all(configs, args.manifest, args.threads, out, args.timeout)
    print(f"results: {out}")


def cmd_recommend(args):
    reference = read_rows(args.reference)
    available_mb = sysinfo.available_memory() / 2**20
    if args.quick_csv:
        quick_path = args.quick_csv
    else:
        quick_path = f"results/quick_{_host()}.csv"
        configs = fits_in_memory(all_configs(args.runners, args.models), reference, available_mb)
        print(f"사용 가능한 메모리 {available_mb:.0f}MB → 후보 {len(configs)}개 측정")
        _measure_all(configs, args.sample, args.threads, quick_path, args.timeout)

    best, candidates = recommend(reference, read_rows(quick_path), args.max_cer, args.max_rtf, available_mb)
    print(f"\n{'설정':<28}{'RTF':>8}{'CER':>8}{'RAM(MB)':>10}  비고")
    for c in candidates:
        note = "추천" if c is best else ", ".join(c.rejected)
        print(f"{c.key:<28}{c.rtf:>8.3f}{c.cer:>8.3f}{c.peak_ram_mb:>10.0f}  {note}")
    if best is None:
        print("\n조건을 모두 만족하는 설정이 없습니다. 허용 오류율이나 목표 속도를 완화해 보세요.")
        return 1
    print(f"\n추천 설정: {best.key}")
    return 0


def cmd_rescore(args):
    """Recompute CER from saved transcripts, e.g. after a normalization rule changes."""
    rows = read_rows(args.csv)
    folder = hyps_dir(args.csv)
    updated = missing = 0
    for r in rows:
        if r.get("error"):
            continue
        path = folder / f"{r['runner']}_{r['model']}_{r['precision']}.jsonl"
        if not path.exists():
            r["cer"] = ""  # old rule: blank it rather than mix rules in one table
            missing += 1
            continue
        items = read_hyps(path)
        old = r["cer"]
        r["cer"] = round(cer([i["ref"] for i in items], [i["hyp"] for i in items]), 4)
        r["hyps_with_digits"] = sum(has_digits(i["hyp"]) for i in items)
        print(f"{r['runner']}/{r['model']}/{r['precision']}: CER {old} → {r['cer']}")
        updated += 1
    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in FIELDS} for r in rows)
    print(f"updated {updated}, no transcripts (CER cleared) {missing}")


def cmd_compare(args):
    """Same PC, Docker vs. native: RTF ratio and RAM difference per configuration."""
    a = {f"{r['runner']}/{r['model']}/{r['precision']}": r for r in read_rows(args.a) if r.get("rtf")}
    b = {f"{r['runner']}/{r['model']}/{r['precision']}": r for r in read_rows(args.b) if r.get("rtf")}
    rows = []
    for key in sorted(a.keys() & b.keys()):
        ra, rb = float(a[key]["rtf"]), float(b[key]["rtf"])
        rows.append({"config": key, "rtf_a": ra, "rtf_b": rb, "rtf_ratio_b_over_a": round(rb / ra, 3),
                     "ram_diff_mb": round(float(b[key]["peak_ram_mb"]) - float(a[key]["peak_ram_mb"]), 1)})
    w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]) if rows else ["config"])
    w.writeheader()
    w.writerows(rows)


def cmd_plot(args):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [r for r in read_rows(args.csv) if r.get("rtf") and r.get("cer")]
    fig, ax = plt.subplots(figsize=(7, 5))
    for runner in PRECISIONS:
        pts = [r for r in rows if r["runner"] == runner]
        ax.scatter([float(r["rtf"]) for r in pts], [float(r["cer"]) for r in pts], label=runner)
        for r in pts:
            ax.annotate(f"{r['model']}/{r['precision']}", (float(r["rtf"]), float(r["cer"])), fontsize=7)
    ax.set_xlabel("RTF (lower is faster)")
    ax.set_ylabel("CER (lower is better)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"plot: {args.out}")


def build_parser():
    p = argparse.ArgumentParser(prog="whisperlite")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("sysinfo", help="CPU, RAM, Docker 여부 출력")
    s.set_defaults(func=cmd_sysinfo)

    s = sub.add_parser("prepare-data", help="Zeroth-Korean 테스트셋을 WAV와 manifest로 준비")
    s.add_argument("--out", default="data/zeroth_test")
    s.add_argument("--limit", type=int, help="N개만 받기 (내장 샘플용)")
    s.add_argument("--stride", type=int, default=1, help="k개마다 하나씩 (화자가 고르게 섞이도록)")
    s.set_defaults(func=cmd_prepare_data)

    def common(s, manifest_flag, manifest_default, runners_default):
        s.add_argument("--runners", nargs="+", choices=list(PRECISIONS), default=runners_default)
        s.add_argument("--models", nargs="+", choices=MODEL_SIZES, default=MODEL_SIZES)
        s.add_argument("--threads", type=int, default=sysinfo.default_threads())
        s.add_argument("--timeout", type=float, help="설정 하나당 최대 초")
        s.add_argument(manifest_flag, default=manifest_default)

    s = sub.add_parser("bench", help="전체 측정 (사전 측정, Docker 권장)")
    common(s, "--manifest", "data/zeroth_test/manifest.csv", list(PRECISIONS))
    s.add_argument("--out")
    s.set_defaults(func=cmd_bench)

    s = sub.add_parser("recommend", help="이 PC에서 짧게 측정하고 설정 추천")
    common(s, "--sample", "data/sample/manifest.csv", ["faster", "whispercpp"])
    s.add_argument("--reference", required=True, help="CER 표로 쓸 bench 결과 CSV")
    s.add_argument("--max-cer", type=float, required=True, help="허용 오류율, 예: 0.15")
    s.add_argument("--max-rtf", type=float, help="목표 속도, 예: 0.5 (음성 길이의 절반 시간)")
    s.add_argument("--quick-csv", help="이미 측정한 결과로 추천만 실행")
    s.set_defaults(func=cmd_recommend)

    s = sub.add_parser("rescore", help="저장된 전사문으로 CER 다시 계산 (정규화 규칙이 바뀐 뒤)")
    s.add_argument("csv")
    s.set_defaults(func=cmd_rescore)

    s = sub.add_parser("compare", help="같은 PC의 두 결과 비교 (예: Docker vs 직접 실행)")
    s.add_argument("a")
    s.add_argument("b")
    s.set_defaults(func=cmd_compare)

    s = sub.add_parser("plot", help="RTF-CER 산점도")
    s.add_argument("csv")
    s.add_argument("--out", default="results/rtf_cer.png")
    s.set_defaults(func=cmd_plot)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
