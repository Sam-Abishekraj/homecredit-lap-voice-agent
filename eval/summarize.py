"""Summarise turn-level results: python eval/summarize.py v1 [v2 ...] -> markdown tables (stdout) + results/<v>/turns_summary.md"""
import json, os, sys, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from turn_tests import TESTS
from run_turns import check
RESCORE = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(version):
    by_model = collections.defaultdict(dict)
    for p in sorted(glob.glob(os.path.join(ROOT, "eval", "results", version, "turns_*.jsonl"))):
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            if RESCORE and r["id"] in TESTS:  # re-apply the current deterministic checks to the stored reply
                ok, h, soft, bad = check(TESTS[r["id"]], r["reply"], r["end_call"], r["model"])
                r.update({"pass": ok, "failed": [k for k, v in h.items() if not v], "checks": h, "soft": soft, "slot_errors": bad})
            by_model[r["model"]][r["id"]] = r  # shards of the same model merge; later shard wins on duplicates
    return by_model

def table(rows, key):
    c = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        c[r[key]][1] += 1
        c[r[key]][0] += r["pass"]
    return c

def main():
    out = []
    for v in sys.argv[1:]:
        for model, res in load(v).items():
            rows = list(res.values())
            n, p = len(rows), sum(r["pass"] for r in rows)
            out.append(f"\n### {v} — {model}: {p}/{n} passed ({100*p/max(n,1):.0f}%)\n")
            out.append("| Language | Pass |\n|---|---|")
            for k, (a, b) in sorted(table(rows, "language").items()):
                out.append(f"| {k} | {a}/{b} |")
            out.append("\n| Category | Pass |\n|---|---|")
            for k, (a, b) in sorted(table(rows, "category").items()):
                out.append(f"| {k} | {a}/{b} |")
            fails = [r for r in rows if not r["pass"]]
            if fails:
                out.append("\nFailures:")
                for r in sorted(fails, key=lambda x: x["id"]):
                    oc = (r.get("end_call") or {}).get("outcome")
                    out.append(f"- **{r['id']}** {r['title']} — failed `{', '.join(r['failed'])}`{' ' + str(r['slot_errors']) if r['slot_errors'] else ''} — reply: \"{r['reply'][:160]}\"{' → end_call ' + str(oc) if oc else ''}")
            soft = collections.Counter()
            for r in rows:
                for k in ("multi_question", "markdown", "digits"):
                    soft[k] += bool(r["soft"].get(k))
            out.append(f"\nSoft style flags (not scored): multi-question turns {soft['multi_question']}, markdown/symbols {soft['markdown']}, digits in speech {soft['digits']}, mean words/turn {sum(r['soft']['words'] for r in rows)/max(n,1):.1f}")
        md = "\n".join(out)
    print(md)
    if len(sys.argv) == 2:
        open(os.path.join(ROOT, "eval", "results", sys.argv[1], "turns_summary.md"), "w", encoding="utf-8").write(md)

if __name__ == "__main__":
    main()
