"""JSON stdin/stdout bridge for the web workspace; no web framework is needed."""
import json
import sys

from .bayesian import bayes
from .criteria import certainty, risk, uncertainty
from .examples import example
from .matrix import Matrix, ModelError, probabilities
from .tree import solve_tree


def dispatch(body):
    if not isinstance(body, dict):
        raise ModelError("Send a decision analysis request object.")
    action = body.get("action")
    if action == "tree":
        return solve_tree(body.get("tree"), body.get("objective", "profit"))
    if action == "example":
        return example(body.get("id"), body.get("options"), solve=body.get("solve") is True, answer=body.get("answer"))
    if action not in ("validate", "certainty", "uncertainty", "normalize", "risk", "bayes", "comparison"):
        raise ModelError("Unknown analysis type.")
    matrix = Matrix.from_dict(body.get("matrix"))
    if action == "validate":
        return matrix.to_dict()
    if action == "certainty":
        return certainty(matrix, body.get("state",0))
    if action == "uncertainty":
        return uncertainty(matrix, body.get("alpha",0.5))
    if action == "normalize":
        return probabilities(body.get("probabilities"), len(matrix.states), normalize=True)
    if action == "risk":
        return risk(matrix, body.get("probabilities"), price=body.get("price",0))
    if action == "bayes":
        return bayes(matrix, body.get("prior"), body.get("evidence"), body.get("likelihoods"), body.get("price",0))
    result = dict(certainty=certainty(matrix,body.get("state",0)), uncertainty=uncertainty(matrix,body.get("alpha",0.5)))
    try:
        result["risk"] = risk(matrix,body.get("probabilities"))
    except ModelError as exc:
        result["riskError"] = str(exc)
    return result


def main() -> None:
    try:
        result = {"data":dispatch(json.load(sys.stdin))}
    except (ModelError, json.JSONDecodeError) as exc:
        result = {"error":str(exc)}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(",",":")))


if __name__ == "__main__":
    main()
