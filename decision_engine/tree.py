"""Rooted, multi-stage decision trees with additive branch adjustments."""
from math import fsum
from typing import Any

from .matrix import ModelError, fmt, number, optimum, probabilities, winners


def solve_tree(data: Any, objective: str = "profit") -> dict:
    """Evaluate a strict tree from the leaves up; report all tied branches and reachable policy edges."""
    if objective not in ("profit", "cost"):
        raise ModelError("Choose either profit or cost as the tree objective.")
    direction = "max" if objective == "profit" else "min"
    if not isinstance(data, dict) or not isinstance(data.get("nodes"), list) or not 1 <= len(data["nodes"]) <= 80:
        raise ModelError("A tree must contain 1–80 nodes.")
    raw, root = data["nodes"], data.get("root")
    nodes: dict[str, dict] = {}
    parents: dict[str, int] = {}
    for n in raw:
        if not isinstance(n, dict):
            raise ModelError("Every node must be an object.")
        key, name, kind = n.get("id"), n.get("name"), n.get("type")
        if not isinstance(key, str) or not 1 <= len(key) <= 70 or key in nodes:
            raise ModelError("Node IDs must be nonempty and unique.")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 70:
            raise ModelError("Each node needs a name of 1–70 characters.")
        if kind not in ("decision", "chance", "terminal"):
            raise ModelError(f"Unknown node type at {name}.")
        branches = n.get("branches", [])
        if not isinstance(branches, list):
            raise ModelError(f"Branches for {name} must be a list.")
        if kind == "terminal" and branches:
            raise ModelError(f"Terminal node {name} must not have branches.")
        if kind != "terminal" and not branches:
            raise ModelError(f"{name} needs at least one branch.")
        children = []
        for b in branches:
            if not isinstance(b, dict) or not isinstance(b.get("to"), str):
                raise ModelError(f"Each branch from {name} needs a child ID.")
            child = b["to"]
            parents[child] = parents.get(child, 0) + 1
            label = b.get("label", "")
            if not isinstance(label, str) or len(label) > 70:
                raise ModelError(f"Branch labels from {name} must be at most 70 characters.")
            children.append(dict(to=child, label=label.strip(), immediate=number(b.get("immediate", 0), f"Adjustment from {name}")))
        if kind == "chance":
            p = probabilities([b.get("probability") for b in branches], len(children), field=f"Branches from {name}")
            for b, q in zip(children, p):
                b["probability"] = q
        nodes[key] = dict(id=key, name=name.strip(), type=kind, branches=children)
        if kind == "terminal":
            nodes[key]["payoff"] = number(n.get("payoff"), f"Terminal payoff at {name}")
    if not isinstance(root, str) or root not in nodes:
        raise ModelError("The root must refer to a node in the tree.")
    if any(child not in nodes for child in parents):
        raise ModelError("A branch refers to a child that does not exist.")
    if parents.get(root, 0) or any(parents.get(k, 0) != 1 for k in nodes if k != root):
        raise ModelError("The root has no parent; every other node must have exactly one parent.")
    results: dict[str, dict] = {}
    visiting: set[str] = set()

    def evaluate(key: str) -> float:
        if key in visiting:
            raise ModelError("A decision tree may not contain cycles.")
        visiting.add(key)
        node = nodes[key]
        kind = node["type"]
        assigned = []
        if kind == "terminal":
            value = node["payoff"]
            step = f"Terminal value = {fmt(value)}"
        else:
            terms = []
            for edge in node["branches"]:
                child_value = evaluate(edge["to"])
                total = fsum([edge["immediate"], child_value])
                edge.update(childValue=child_value, total=total)
                terms.append(f"({fmt(edge['immediate'])} + ({fmt(child_value)}))")
            totals = [b["total"] for b in node["branches"]]
            if kind == "decision":
                assigned = winners(totals, direction)
                value = optimum(totals, direction)
                step = f"{direction}({', '.join(terms)}) = {direction}({', '.join(map(fmt, totals))}) = {fmt(value)}"
            else:
                p = [b["probability"] for b in node["branches"]]
                products = [q*t for q,t in zip(p,totals)]
                value = fsum(products)
                step = " + ".join(f"{fmt(q)} × {t}" for q,t in zip(p,terms)) + " = " + " + ".join(f"({fmt(v)})" for v in products) + f" = {fmt(value)}"
        visiting.remove(key)
        results[key] = dict(node, value=value, step=step, chosen=assigned)
        return value

    value = evaluate(root)
    if len(results) != len(nodes):
        raise ModelError("Every node must be reachable from the root; check for disconnected cycles.")
    policy: list[dict] = []

    def mark(key: str) -> None:
        n = results[key]
        for i, b in enumerate(n["branches"]):
            if (n["type"] == "decision" and i in n["chosen"]) or (n["type"] == "chance" and b["probability"] > 0):
                policy.append(dict(source=key, target=b["to"]))
                mark(b["to"])

    mark(root)
    return dict(root=root, objective=objective, direction=direction, value=value, policy=policy,
                evaluationOrder=list(results), nodes=[results[n] for n in nodes])
