import sys, json, csv, os
root = sys.argv[1]
sys.path.insert(0, root); sys.path.insert(0, os.path.join(root, "evaluacion"))
os.chdir(root)
from inference_engine.rules.law_5_antijailbreak import Law5AntiJailbreak
L = Law5AntiJailbreak(); m = L._matcher; t = L.semantic_threshold
dev = json.load(open("evaluacion/dev/dev_set.json", encoding="utf-8"))["ley5"]
for k in ("positivos", "negativos"):
    s = [float(x) for x in m.scores(dev[k])]
    print(k, "n", len(s), "hits", sum(x >= t for x in s), "max %.4f" % max(s))
mj = list(csv.DictReader(open("evaluacion/datasets/multijail.csv", encoding="utf-8")))
for lang in ("en", "zh", "sw"):
    s = sorted(float(x) for x in m.scores([r[lang] for r in mj if r.get(lang)]))
    print(lang, "umbral %.4f" % t, "max %.4f p95 %.4f mediana %.4f" % (s[-1], s[int(.95 * len(s))], s[len(s) // 2]))
