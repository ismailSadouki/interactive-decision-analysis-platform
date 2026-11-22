"""Course-verified decision criteria, with traceable evaluation steps."""
from math import fsum, isclose, sqrt
from typing import Any, Sequence

from .matrix import Matrix, ModelError, fmt, number, optimum, probabilities, regret_matrix, weighted, winners


def evaluation(key: str, label: str, arabic: str, direction: str, formula: str, interpretation: str,
               scores: Sequence[float], steps: Sequence[str]) -> dict:
    return dict(key=key, label=label, arabic=arabic, direction=direction, formula=formula,
                interpretation=interpretation, scores=list(scores), steps=list(steps),
                winners=winners(scores, direction), best=optimum(scores, direction))


def certainty(matrix: Matrix, state: Any = 0) -> dict:
    j = number(state, "Known state index")
    if not j.is_integer() or not 0 <= j < len(matrix.states):
        raise ModelError("Select a state that exists in the matrix.")
    j = int(j)
    scores = [row[j] for row in matrix.values]
    fn = matrix.direction
    return evaluation("certainty", "Known-state criterion", "القرار في حالة التأكد", fn,
                      rf"a^*\in\operatorname*{{arg{fn}}}_i\;r_{{i,{j + 1}}}",
                      "Only the known column matters. Compare every alternative under that state.",
                      scores, [f"r({i+1},{j+1}) = {fmt(x)}" for i, x in enumerate(scores)])


def hurwicz_intervals(best: Sequence[float], worst: Sequence[float], direction: str) -> list[dict]:
    """Intersect pairwise linear inequalities to get each action's closed optimal interval."""
    slopes = [b - w for b, w in zip(best, worst)]
    sign = 1 if direction == "max" else -1
    lines = []
    for i, (b, w, s) in enumerate(zip(best, worst, slopes)):
        low, high = 0.0, 1.0
        impossible = False
        comparisons = []
        for k, (other_w, other_s) in enumerate(zip(worst, slopes)):
            if i == k:
                continue
            c, d = sign * (w - other_w), sign * (s - other_s)
            step = f"H{i+1} {'≥' if sign == 1 else '≤'} H{k+1}: ({fmt(c)}) + ({fmt(d)})α ≥ 0"
            if d > 0:
                bound = -c/d
                low = max(low, bound)
                step += f" ⇒ α ≥ {fmt(bound)}"
            elif d < 0:
                bound = -c/d
                high = min(high, bound)
                step += f" ⇒ α ≤ {fmt(bound)}"
            else:
                impossible = impossible or c < 0
                step += " ⇒ fails for every α" if c < 0 else " ⇒ holds for every α"
            comparisons.append(step)
        interval = None
        if not impossible:
            if low <= high:
                interval = [low, high]
            elif low-high <= 1e-12 and 0 <= (low+high)/2 <= 1:
                interval = [(low+high)/2, (low+high)/2]
        lines.append(dict(best=b, worst=w, intercept=w, slope=s, interval=interval, comparisons=comparisons))
    return lines


def uncertainty(matrix: Matrix, alpha: Any = 0.5) -> dict:
    a = number(alpha, "Optimism coefficient α")
    if not 0 <= a <= 1:
        raise ModelError("The optimism coefficient α must lie between 0 and 1.")
    m = len(matrix.states)
    best, worst = matrix.row_extremes()
    benchmark, regret = regret_matrix(matrix)
    direction = matrix.direction
    b_fn, w_fn = ("max", "min") if direction == "max" else ("min", "max")
    laplace = [fsum(row) / m for row in matrix.values]
    savage = list(map(max, regret))
    hurwicz = [fsum([a*b, (1-a)*w]) for b, w in zip(best, worst)]

    def extrema_step(fn: str, row: Sequence[float], x: float) -> str:
        return f"{fn}({', '.join(map(fmt, row))}) = {fmt(x)}"

    criteria = [
        evaluation("laplace", "Laplace", "معيار لابلاس", direction,
                   rf"\bar r_i=\frac{{1}}{{m}}\sum_{{j=1}}^m r_{{ij}},\quad a^*\in\operatorname*{{arg{direction}}}_i\bar r_i",
                   "Give each state weight 1/m as a modeling convention; no measured probabilities are assumed.", laplace,
                   [f"({' + '.join(f'({fmt(x)})' if x < 0 else fmt(x) for x in row)}) / {m} = {fmt(v)}" for row, v in zip(matrix.values, laplace)]),
        evaluation("wald", "Wald (pessimistic)", "معيار والد (التشاؤم)", direction,
                   rf"a^*\in\operatorname*{{arg{direction}}}_i\;\{w_fn}_j r_{{ij}}",
                   "Choose the most desirable worst-case outcome, protecting against the least favorable state.", worst,
                   [extrema_step(w_fn, row, v) for row, v in zip(matrix.values, worst)]),
        evaluation("maximax", "Maximax (optimistic)" if direction == "max" else "Minimin (optimistic)", "معيار التفاؤل", direction,
                   rf"a^*\in\operatorname*{{arg{direction}}}_i\;\{b_fn}_j r_{{ij}}",
                   "Compare each alternative's best possible outcome. This models complete optimism.", best,
                   [extrema_step(b_fn, row, v) for row, v in zip(matrix.values, best)]),
        evaluation("savage", "Savage (minimax regret)", "معيار سافاج (الندم)", "min",
                   r"\ell_{ij}=|r_{ij}-r_j^*|,\quad a^*\in\operatorname*{argmin}_i\max_j\ell_{ij}",
                   "Minimize the largest missed opportunity. The benchmark is the best feasible payoff within each state.", savage,
                   ["[" + ", ".join(f"|{fmt(x)} − {fmt(y)}| = {fmt(gap)}" for x,y,gap in zip(row,benchmark,loss)) + "] → " + extrema_step("max", loss, v) for row, loss, v in zip(matrix.values,regret,savage)]),
        evaluation("hurwicz", "Hurwicz", "معيار هورفيتز", direction,
                   r"H_i(\alpha)=\alpha r_i^{\mathrm{best}}+(1-\alpha)r_i^{\mathrm{worst}},\quad 0\leq\alpha\leq 1",
                   "α is the weight of the more desirable outcome. At α = 0 use Wald; at α = 1 use full optimism.", hurwicz,
                   [f"{fmt(a)}({fmt(b)}) + (1 − {fmt(a)})({fmt(w)}) = {fmt(a*b)} + ({fmt((1-a)*w)}) = {fmt(v)}" for b,w,v in zip(best,worst,hurwicz)]),
    ]
    return dict(alpha=a, criteria=criteria, bestByState=benchmark, regret=regret,
                lines=hurwicz_intervals(best, worst, direction))


def expected_values(matrix: Matrix, p: Sequence[float]) -> dict:
    """Evaluate EMV for a probability vector already validated by the caller."""
    rows = [weighted(row, p) for row in matrix.values]
    return evaluation("emv", "Expected monetary value", "القيمة النقدية المتوقعة", matrix.direction,
                      r"\operatorname{EMV}(a_i)=\sum_{j=1}^{m}p_jr_{ij}",
                      "EMV is a probability-weighted average, not a guaranteed outcome. " + (
                          "Choose the largest expected profit." if matrix.direction == "max" else "Choose the smallest expected cost."),
                      [x[0] for x in rows], [x[1] for x in rows])


def should_buy(price: float, value: float) -> bool:
    """The course's strict price inequality, allowing for decimal/binary conversion."""
    return price < value and not isclose(price, value, rel_tol=4e-15, abs_tol=0)


def risk(matrix: Matrix, distribution: Any, *, normalize: bool = False, price: Any = 0) -> dict:
    p = probabilities(distribution, len(matrix.states), normalize=normalize)
    price = number(price, "Information price")
    if price < 0:
        raise ModelError("Information price cannot be negative.")
    emv = expected_values(matrix, p)
    best_by_state, regret = regret_matrix(matrix)
    losses = [weighted(row, p) for row in regret]
    eol = evaluation("eol", "Expected opportunity loss", "الندم المتوقع", "min",
                     r"\operatorname{EOL}(a_i)=\sum_{j=1}^{m}p_j\ell_{ij}",
                     "Prefer the smallest expected missed opportunity. EOL and EMV identify the same optimal alternatives, up to numerical tolerance.",
                     [x[0] for x in losses], [x[1] for x in losses])
    variances, stds, steps = [], [], []
    for row, mean in zip(matrix.values, emv["scores"]):
        var = fsum(pj*(x-mean)**2 for pj,x in zip(p,row))
        std = sqrt(var)
        variances.append(var)
        stds.append(std)
        terms = " + ".join(f"{fmt(pj)}({fmt(x)} − ({fmt(mean)}))²" for pj,x in zip(p,row))
        steps.append(f"{terms} = {fmt(var)}; σ = √{fmt(var)} = {fmt(std)}")
    perfect, perfect_step = weighted(best_by_state, p)
    # min EOL is the same oriented difference, computed without cancellation.
    evpi = eol["best"]
    lhs, rhs = (perfect, emv["best"]) if matrix.direction == "max" else (emv["best"], perfect)
    return dict(probabilities=p, emv=emv, eol=eol, regret=regret, bestByState=best_by_state, variance=variances,
                std=stds, varianceSteps=steps, perfect=perfect, evpi=evpi, perfectStep=perfect_step,
                evpiStep=f"{fmt(lhs)} − ({fmt(rhs)}) = {fmt(evpi)}", price=price, buy=should_buy(price,evpi),
                evpiFormula=r"\operatorname{EVPI}=" + (r"V_{\mathrm{perfect}}-V_{\mathrm{current}}" if matrix.direction == "max" else r"V_{\mathrm{current}}-V_{\mathrm{perfect}}"))
