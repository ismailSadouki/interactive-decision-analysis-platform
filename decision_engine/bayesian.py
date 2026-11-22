"""Finite-state Bayesian decision analysis and value of sample information."""
from math import fsum
from typing import Any

from .criteria import expected_values, should_buy
from .matrix import Matrix, ModelError, fmt, label_names, number, probabilities, regret_matrix, weighted


def bayes(matrix: Matrix, prior: Any, evidence: Any, likelihoods: Any, price: Any = 0) -> dict:
    """likelihoods[k][j] = P(observation k | state j); observations partition the sample space."""
    p = probabilities(prior, len(matrix.states), field="Prior probabilities")
    evidence = label_names(evidence, "Observation")
    if not isinstance(likelihoods, (list, tuple)) or len(likelihoods) != len(evidence):
        raise ModelError("Provide one likelihood row per possible observation.")
    if any(not isinstance(row, (list, tuple)) or len(row) != len(p) for row in likelihoods):
        raise ModelError("Every likelihood row must contain one entry per state.")
    cols = [probabilities(list(col), len(evidence), field=f"Likelihoods conditional on {state}")
            for state, col in zip(matrix.states, zip(*likelihoods))]
    table = [list(row) for row in zip(*cols)]
    price = number(price, "Sample cost")
    if price < 0:
        raise ModelError("Sample cost cannot be negative.")
    baseline = expected_values(matrix, p)
    observations = []
    for label, row in zip(evidence, table):
        joint = [a*b for a,b in zip(row,p)]
        marginal, marginal_step = weighted(row, p)
        posterior = [x/marginal for x in joint] if marginal > 0 else None
        posterior_steps = [f"({fmt(l)} × {fmt(q)}) / {fmt(marginal)} = {fmt(z)}" for l,q,z in zip(row,p,posterior)] if posterior is not None else []
        emv = expected_values(matrix, posterior) if posterior is not None else None
        observations.append(dict(name=label, probability=marginal, joint=joint, marginalStep=marginal_step,
                                 posterior=posterior, posteriorSteps=posterior_steps, emv=emv))
    possible = [o for o in observations if o["emv"] is not None]
    sample, sample_step = weighted([o["emv"]["best"] for o in possible], [o["probability"] for o in possible])
    best_by_state, regret = regret_matrix(matrix)
    perfect, perfect_step = weighted(best_by_state, p)
    evpi = min(fsum(x*q for x,q in zip(row,p)) for row in regret)
    # Evaluate incremental payoff/cost savings versus the best fixed action. This
    # is algebraically Vsample − Vcurrent (or the reverse for costs), without
    # subtracting two nearly equal, potentially very large expected totals.
    fixed = matrix.values[baseline["scores"].index(baseline["best"])]
    sign = 1 if matrix.direction == "max" else -1
    gains = [max(fsum(sign * (v - ref) * q for v,ref,q in zip(row,fixed,o["joint"]))
                 for row in matrix.values) for o in possible]
    evsi = fsum(gains)
    lhs,rhs = (sample, baseline["best"]) if matrix.direction == "max" else (baseline["best"], sample)
    plhs,prhs = (perfect, baseline["best"]) if matrix.direction == "max" else (baseline["best"], perfect)
    return dict(prior=p, observations=observations, likelihoods=table, baseline=baseline, sample=sample,
                perfect=perfect, evsi=evsi, evpi=evpi, sampleStep=sample_step, perfectStep=perfect_step,
                evpiStep=f"{fmt(plhs)} − ({fmt(prhs)}) = {fmt(evpi)}",
                evsiStep=f"{fmt(lhs)} − ({fmt(rhs)}) = {fmt(evsi)}", price=price, net=evsi-price, buy=should_buy(price,evsi))
