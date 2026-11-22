"""Input fixtures and dynamically evaluated exercises."""
import json
from pathlib import Path
from math import isclose

from .bayesian import bayes
from .course_models import assignment, spare_parts, staffing
from .criteria import certainty, risk, uncertainty
from .matrix import Matrix, ModelError, number
from .tree import solve_tree


def fixtures() -> list[dict]:
    return json.loads((Path(__file__).resolve().parents[1] / "examples" / "problems.json").read_text(encoding="utf-8"))


def example(key: str, options=None, *, solve: bool = False, answer=None) -> dict:
    try:
        item = next(x for x in fixtures() if x["id"] == key)
    except StopIteration:
        raise ModelError("Choose an available example.") from None
    mode = item["mode"]
    options = options if isinstance(options, dict) else {}
    if mode == "assignment":
        item.update(assignment(options.get("times", item["times"])))
    if mode == "poisson":
        item.update(spare_parts(*(options.get(k,item[k]) for k in ("rate","cutoff","upfront","replacement"))))
    if mode == "staffing":
        item["demands"] = options.get("demands",item["demands"])
    if mode == "tree":
        root = next(n for n in item["tree"]["nodes"] if n["id"] == item["tree"]["root"])
        item["answerChoices"] = [b["label"] for b in root["branches"]]
    elif mode not in ("bayes", "staffing", "poisson") and item.get("criterion") != "evpi":
        item["answerChoices"] = item["matrix"]["alternatives"]
    if not solve and answer is None:
        return item
    matrix = Matrix.from_dict(item["matrix"]) if "matrix" in item else None
    if mode in ("certainty", "assignment"):
        result = certainty(matrix, item.get("state",0))
        target = result["winners"]
    elif mode == "uncertainty":
        result = uncertainty(matrix, item.get("alpha",0.5))
        target = next(c["winners"] for c in result["criteria"] if c["key"] == item["criterion"])
    elif mode in ("risk", "poisson"):
        result = risk(matrix, item["probabilities"])
        target = result["evpi"] if item.get("criterion") == "evpi" else result["emv"]["winners"]
    elif mode == "bayes":
        result = bayes(matrix, item["probabilities"], item["evidence"], item["likelihoods"], item["samplePrice"])
        target = result["evsi"]
    elif mode == "tree":
        result = solve_tree(item["tree"])
        target = next(n["chosen"] for n in result["nodes"] if n["id"] == result["root"])
    else:
        result = staffing(item["demands"])
        target = result["total"]
    if answer is not None:
        num = number(answer, "Your answer")
        item["correct"] = (num in target) if isinstance(target,list) else isclose(num,target,rel_tol=1e-5,abs_tol=1e-5)
    if solve:
        item["solution"] = result
    return item
