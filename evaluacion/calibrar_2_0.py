"""
Calibra los umbrales de Aletheia 2.0 usando SOLO evaluacion/dev/dev_set.json.

Reglas fijadas antes de ejecutar (y antes de ver datos de prueba):
- ley5_semantico y proposito_danino: el menor umbral cuya tasa de falsos positivos en los
  negativos de desarrollo sea <= 5 %.
- categoria_min: (mínima confianza entre herramientas de desarrollo bien clasificadas) - 0.02.
  Por debajo, la herramienta se trata como de efecto desconocido (falla cerrada).
- capacidad_semantica: 1.01 (planificador semántico deshabilitado; la 2.0 usa el planificador
  con LLM y, si no hay LLM, no concede capacidades).

    python evaluacion/calibrar_2_0.py
"""
import json
import math
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from inference_engine import semantic  # noqa: E402
from inference_engine.config_2_0 import prototipos, UMBRALES_PATH  # noqa: E402
from inference_engine.rules.law_5_antijailbreak import Law5AntiJailbreak  # noqa: E402

FPR_MAX = 0.05


def umbral_fpr(neg_scores):
    s = sorted(neg_scores, reverse=True)
    permitidos = math.floor(FPR_MAX * len(s))
    return float(s[permitidos]) + 1e-6  # todo lo estrictamente mayor que este valor es positivo


def main():
    if not semantic.available():
        sys.exit(f"Modelo semántico no disponible: {semantic.load_error()}")
    dev = json.load(open(os.path.join(BASE, "evaluacion", "dev", "dev_set.json"), encoding="utf-8"))
    protos = prototipos()
    informe = {"modelo_embeddings": semantic.MODEL_NAME, "regla_fpr_max": FPR_MAX}

    # --- Ley 5
    m5 = semantic.PrototypeMatcher(protos["ley5_reescritura_directrices"])
    pos = [float(x) for x in m5.scores(dev["ley5"]["positivos"])]
    neg = [float(x) for x in m5.scores(dev["ley5"]["negativos"])]
    t5 = umbral_fpr(neg)
    lex = Law5AntiJailbreak(use_semantic=False)
    comb_pos = [lex.lexical_hit(t) or s >= t5 for t, s in zip(dev["ley5"]["positivos"], pos)]
    comb_neg = [lex.lexical_hit(t) or s >= t5 for t, s in zip(dev["ley5"]["negativos"], neg)]
    informe["ley5"] = {
        "umbral": t5,
        "tpr_semantico_dev": sum(s >= t5 for s in pos) / len(pos),
        "fpr_semantico_dev": sum(s >= t5 for s in neg) / len(neg),
        "tpr_lexico_dev": sum(lex.lexical_hit(t) for t in dev["ley5"]["positivos"]) / len(pos),
        "fpr_lexico_dev": sum(lex.lexical_hit(t) for t in dev["ley5"]["negativos"]) / len(neg),
        "tpr_combinado_dev": sum(comb_pos) / len(pos),
        "fpr_combinado_dev": sum(comb_neg) / len(neg),
    }

    # --- Propósito dañino (misma segmentación que ContextPolicy)
    from inference_engine.context_policy import purpose_contrast
    mp = semantic.PrototypeMatcher(protos["proposito_danino_a_terceros"])
    mb = semantic.PrototypeMatcher(protos["proposito_benigno"])

    def pscore(t):
        return purpose_contrast(t, mp, mb)

    ppos = [pscore(t) for t in dev["proposito"]["positivos"]]
    pneg = [pscore(t) for t in dev["proposito"]["negativos"]]
    tp = umbral_fpr(pneg)
    informe["proposito"] = {"umbral": tp,
                            "tpr_dev": sum(s >= tp for s in ppos) / len(ppos),
                            "fpr_dev": sum(s >= tp for s in pneg) / len(pneg)}

    # --- Categorías de herramientas
    from inference_engine.action_gate import ActionGate
    gate = ActionGate()
    gate.min_confianza = -1.0
    aciertos, confs, detalle = 0, [], []
    for t in dev["categorias"]:
        cat, conf = gate.categorize(t["herramienta"], t["descripcion"])
        ok = cat == t["categoria"]
        aciertos += ok
        if ok:
            confs.append(conf)
        detalle.append({**t, "predicha": cat, "confianza": round(conf, 4)})
    tcat = (min(confs) - 0.02) if confs else 0.0
    informe["categorias"] = {"umbral_min": tcat, "exactitud_dev": aciertos / len(dev["categorias"]),
                             "detalle": detalle}

    umbrales = {"ley5_semantico": t5, "proposito_danino": tp, "categoria_min": tcat,
                "capacidad_semantica": 1.01, "modelo_embeddings": semantic.MODEL_NAME}
    with open(UMBRALES_PATH, "w", encoding="utf-8") as f:
        json.dump(umbrales, f, indent=2)
    with open(os.path.join(BASE, "evaluacion", "dev", "calibracion.json"), "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in informe.items() if k != "categorias"}, ensure_ascii=False, indent=2))
    print("categorias:", {k: v for k, v in informe["categorias"].items() if k != "detalle"})
    for d in detalle:
        if d["predicha"] != d["categoria"]:
            print("  error:", d["herramienta"], d["categoria"], "->", d["predicha"])


if __name__ == "__main__":
    main()
