"""Validated input types, preference direction, and probability distributions."""
from dataclasses import dataclass
from math import fsum, isclose, isfinite
from typing import Any, Sequence

try:
    import numpy as np
except ImportError:  # The browser server can use the portable standard-library engine.
    np = None

MAX_DIMENSION = 24
PROB_TOL = 1e-9


class ModelError(ValueError):
    """A user-correctable error in a decision problem."""


def number(value: Any, field: str = "Value") -> float:
    try:
        if isinstance(value, bool):
            raise TypeError
        if isinstance(value, str):
            value = value.strip().replace("−", "-").replace("٫", ".")
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        raise ModelError(f"{field} must be a number.") from None
    if not isfinite(result) or abs(result) > 1e100:
        raise ModelError(f"{field} must be finite and no larger than 10¹⁰⁰ in magnitude.")
    return result


def label_names(values: Sequence[Any], field: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)) or not 1 <= len(values) <= MAX_DIMENSION:
        raise ModelError(f"Provide between 1 and {MAX_DIMENSION} {field.lower()} names.")
    if any(not isinstance(x, str) or not x.strip() or len(x.strip()) > 70 for x in values):
        raise ModelError(f"Each {field.lower()} name must be 1–70 characters.")
    names = tuple(x.strip() for x in values)
    if len(set(names)) != len(names):
        raise ModelError(f"{field} names must be unique.")
    return names


@dataclass(frozen=True)
class Matrix:
    alternatives: tuple[str, ...]
    states: tuple[str, ...]
    values: tuple[tuple[float, ...], ...]
    objective: str = "profit"

    def __post_init__(self) -> None:
        rows = label_names(self.alternatives, "Alternative")
        cols = label_names(self.states, "State")
        if self.objective not in ("profit", "cost"):
            raise ModelError("Choose either profit or cost as the objective.")
        if not isinstance(self.values, (list, tuple)) or len(self.values) != len(rows):
            raise ModelError("The number of payoff rows must match the number of alternatives.")
        if any(not isinstance(row, (list, tuple)) or len(row) != len(cols) for row in self.values):
            raise ModelError("Every alternative must have one payoff per state.")
        numeric = tuple(tuple(number(x, f"Payoff for {r} / {c}") for c, x in zip(cols, row))
                        for r, row in zip(rows, self.values))
        object.__setattr__(self, "alternatives", rows)
        object.__setattr__(self, "states", cols)
        object.__setattr__(self, "values", numeric)

    @classmethod
    def from_dict(cls, data: Any) -> "Matrix":
        if not isinstance(data, dict):
            raise ModelError("A decision matrix is required.")
        return cls(data.get("alternatives"), data.get("states"), data.get("values"), data.get("objective", "profit"))

    def to_dict(self) -> dict:
        return dict(alternatives=list(self.alternatives), states=list(self.states),
                    values=[list(row) for row in self.values], objective=self.objective)

    @property
    def direction(self) -> str:
        return "max" if self.objective == "profit" else "min"

    def best_by_state(self) -> list[float]:
        if np is not None:
            reducer = np.max if self.objective == "profit" else np.min
            return reducer(np.asarray(self.values, dtype=float), axis=0).tolist()
        return [optimum(col, self.direction) for col in zip(*self.values)]

    def row_extremes(self) -> tuple[list[float], list[float]]:
        """Most and least desirable outcome per row, in that order."""
        if np is not None:
            data = np.asarray(self.values, dtype=float)
            lowest, highest = np.min(data, axis=1).tolist(), np.max(data, axis=1).tolist()
        else:
            lowest, highest = list(map(min, self.values)), list(map(max, self.values))
        return (highest, lowest) if self.direction == "max" else (lowest, highest)


def probabilities(values: Any, count: int, *, normalize: bool = False, field: str = "Probabilities") -> list[float]:
    if not isinstance(values, (list, tuple)) or len(values) != count or count < 1:
        raise ModelError(f"{field} must contain exactly {count} values.")
    result = [number(x, f"{field}, entry {j + 1}") for j, x in enumerate(values)]
    if any(not 0 <= x <= 1 for x in result):
        raise ModelError(f"{field} must each lie between 0 and 1.")
    total = fsum(result)
    if normalize:
        if total <= 0:
            raise ModelError(f"{field} cannot be normalized because the total is zero.")
        return [x / total for x in result]
    if not isclose(total, 1.0, rel_tol=0, abs_tol=PROB_TOL):
        raise ModelError(f"{field} must sum to 1 (current total: {total:.12g}).")
    return result


def optimum(scores: Sequence[float], direction: str) -> float:
    return (max if direction == "max" else min)(scores)


def winners(scores: Sequence[float], direction: str) -> list[int]:
    best = optimum(scores, direction)
    return [i for i, v in enumerate(scores) if isclose(v, best, rel_tol=1e-12, abs_tol=1e-9)]


def fmt(x: float) -> str:
    return f"{x:.10g}" if x else "0"


def weighted(values: Sequence[float], weights: Sequence[float]) -> tuple[float, str]:
    terms = [v*p for v, p in zip(values, weights)]
    result = fsum(terms)
    return result, " + ".join(f"{fmt(p)}({fmt(v)})" for v, p in zip(values, weights)) + \
        " = " + " + ".join(f"({fmt(v)})" if v < 0 else fmt(v) for v in terms) + " = " + fmt(result)


def regret_matrix(matrix: Matrix) -> tuple[list[float], list[list[float]]]:
    best = matrix.best_by_state()
    if np is not None:
        return best, np.abs(np.asarray(matrix.values, dtype=float) - np.asarray(best)).tolist()
    return best, [[abs(x-y) for x, y in zip(row, best)] for row in matrix.values]
