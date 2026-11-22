"""Worked course models: assignment, cyclic staffing, and Poisson spare-part cost."""
from itertools import permutations
from math import exp, factorial, fsum
from typing import Any

from .matrix import MAX_DIMENSION, Matrix, ModelError, number


def assignment(times: Any) -> dict:
    if not isinstance(times, list) or not 1 <= len(times) <= 4:
        raise ModelError("The assignment example supports 1–4 technicians and devices.")
    n = len(times)
    devices = [chr(65+j) for j in range(n)]
    input_matrix = Matrix([f"T{i+1}" for i in range(n)], devices, times, "cost")
    if any(x < 0 for row in input_matrix.values for x in row):
        raise ModelError("Repair times cannot be negative.")
    options = list(permutations(range(n)))
    summands = [[input_matrix.values[i][j] for i,j in enumerate(order)] for order in options]
    labels = [f"a{k+1} · " + ", ".join(f"T{i+1}→{devices[j]}" for i,j in enumerate(order)) for k,order in enumerate(options)]
    model = Matrix(labels, ["Total repair time"], [[fsum(row)] for row in summands], "cost")
    return dict(matrix=model.to_dict(), times=input_matrix.to_dict(), summands=summands)


def _staff_dp(d: list[int]) -> list[int]:
    """Exact portable dynamic program, using suffix minima for cyclic coverage."""
    cap = max(d)
    best = (6*cap+1, ())
    for first in range(cap+1):
        paths = [(first, (first,)) if i == first else (6*cap+1, ()) for i in range(cap+1)]
        for j in range(1,6):
            suffix = list(paths)
            for k in range(cap-1, -1, -1):
                suffix[k] = min(suffix[k], suffix[k+1])
            paths = [(suffix[max(0, d[j]-x)][0]+x, suffix[max(0, d[j]-x)][1]+(x,)) for x in range(cap+1)]
        best = min(best, min(paths[max(0,d[0]-first):]))
    return list(best[1])


def staffing(demands: Any) -> dict:
    if not isinstance(demands, (list, tuple)) or len(demands) != 6:
        raise ModelError("Provide six four-hour staffing requirements.")
    vals = [number(x, f"Workers required in period {i+1}") for i,x in enumerate(demands)]
    if any(not x.is_integer() or not 0 <= x <= 60 for x in vals):
        raise ModelError("Each staffing requirement must be an integer between 0 and 60.")
    d = list(map(int, vals))
    # This cyclic even-length coverage model has integral optima; enforce integrality directly.
    try:
        import numpy as np
        from scipy.optimize import LinearConstraint, milp
    except ImportError:
        starts = _staff_dp(d)
    else:
        coverage = np.eye(6) + np.roll(np.eye(6), -1, axis=1)
        result = milp(c=np.ones(6), integrality=np.ones(6), constraints=LinearConstraint(coverage, d, np.inf))
        starts = np.rint(result.x).astype(int).tolist() if result.success else _staff_dp(d)
    actual = [starts[j-1]+starts[j] for j in range(6)]
    printed = [6,8,4,5,9,8]
    return dict(demands=d, starts=starts, coverage=actual, total=sum(starts), printed=printed,
                printedAlternating=[sum(printed[::2]), sum(printed[1::2])])


def spare_parts(rate: Any = 2, cutoff: Any = 6, upfront: Any = 10000, replacement: Any = 40000) -> dict:
    lam = number(rate, "Poisson rate λ")
    limit = number(cutoff, "Maximum breakages")
    upfront, replacement = number(upfront, "Upfront unit cost"), number(replacement, "Shortage unit cost")
    if not 0 <= lam <= 120 or not limit.is_integer() or not 0 <= limit < MAX_DIMENSION:
        raise ModelError(f"Use a rate between 0 and 120 and an integer cutoff from 0 to {MAX_DIMENSION-1}.")
    if not 0 <= upfront <= 1e98 or not 0 <= replacement <= 1e98:
        raise ModelError("Unit costs must be nonnegative and at most 10⁹⁸.")
    interval = range(int(limit)+1)
    raw = [exp(-lam)*lam**k/factorial(k) for k in interval]
    mass = fsum(raw)
    p = [x/mass for x in raw]
    matrix = Matrix([f"a{i} · Buy {i}" for i in interval], [f"{j} breaks" for j in interval],
                    [[upfront*i+replacement*max(j-i,0) for j in interval] for i in interval], "cost")
    return dict(matrix=matrix.to_dict(), probabilities=p, raw=raw, mass=mass, omitted=max(0.0, 1-mass),
                rate=lam, cutoff=int(limit), upfront=upfront, replacement=replacement)
