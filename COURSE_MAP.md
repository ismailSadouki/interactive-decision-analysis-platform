# Source analysis and implementation specification

**Academic source:** the full Arabic transcription supplied in the project brief, beginning with مقدمة and ending with Example 6 (EVPI). No original PDF or figures were attached. The transcription supplies detailed content for I–II, titles only for III–VI. The platform never attributes unsupplied formulas to the professor.

## Course structure and feature coverage

| PDF concept | Mathematical method / decision rule | Application module | Status |
|---|---|---|---|
| مقدمة — information and quantitative decisions | Information, economic value, and modeling | Dashboard / Concepts | Course explanation |
| I — التعريف، الأساليب والعوامل | Choice, intuition vs descriptive vs quantitative methods, precision, probabilities, goals, contextual constraints, criterion | Concepts; interactive capacity constraint example | Course explanation |
| II.1 — مراحل اتخاذ القرار | Identify environment, objective, alternatives, states, and outcomes; R(ai, ej) = rij | Matrix Builder; CSV/XLSX and notation | Implemented |
| II.2 — القرار في حالة التأكد | Compare one known column: max profit / min cost | Certainty | Implemented |
| Example 1 — technician assignment | Enumerate permutations; minimize total repair time | Examples / Certainty | Implemented, 6 assignments; a6 costs 13 |
| Example 2 — 24-hour staffing | Minimize the sum of starts across six cyclic periods | Examples / Staffing solver | Printed model preserved in notes; corrected integer coverage model is interactive |
| II.3a — Laplace | Row mean with equal weight for each state | Uncertainty | Implemented |
| II.3b — Wald | Profit max of row minima; cost min of row maxima | Uncertainty | Implemented |
| II.3c — Maximax | Profit max of row maxima; optimistic cost counterpart min of row minima | Uncertainty | Implemented |
| II.3d — Savage | Column benchmark r*j; lij = abs(rij − r*j); min of row maximum regrets | Uncertainty / Risk | Implemented |
| II.3e — Hurwicz | α × best + (1 − α) × worst, α ∈ [0, 1]; solve comparisons over α | Uncertainty / Sensitivity | Implemented; exact envelope intervals, all ties |
| Example 3 — investment | Apply all five uncertainty criteria; switching at 0.28, 0.92 | Default workspace / Exercises | Implemented |
| II.4a–b — EMV and EOL | Σ rij P(ej); Σ lij P(ej); minimize EOL | Risk; oil example | Implemented |
| Example 5 — Poisson spare parts | PMF exp(−λ) λ^k/k!; cost 10,000i + 40,000 max(k−i,0) | Examples / Poisson generator | Implemented with explicit conditional distribution; default a3 |
| II.4c — EVPI and information price | Perfect vs current value; equivalent min EOL; buy iff price < EVPI | Risk / Information; Example 6 | Implemented |
| Uncertainty vs risk; variance and standard deviation | Missing probabilities vs a known distribution; Σ p (r − μ)² and square root | Risk metrics and comparison | Distinction course-backed; dispersion is a requested extension |
| III — مفهوم شجرة القرار | Multi-stage trees, chance expectation, decision optimization, backward induction | Decision Trees | Headline verified; mechanics are a requested extension, not verified against PDF details |
| IV — نظرية القرار والتحليل البايزي | Priors, evidence likelihoods, Bayes’ theorem, posterior action, EVSI vs EVPI | Bayesian Analysis | Headline verified; mechanics are a requested extension, not verified against PDF details |
| V — القرار ونظرية المنفعة | No formulas, procedure, or worked example supplied | Reference | Listed only; not implemented as a course method |
| VI — القرار في حالة المنافسة (نظرية الألعاب) | No formulas, procedure, or worked example supplied | Reference | Listed only; not implemented as a course method |
| Untranscribed drawings | Only textual descriptions exist | Reference / tree and staffing explanations | Original artwork not reproduced |

## Notation and interpretation decisions

1. The professor names alternatives A = {a₁, …, aₙ}, states E = {e₁, …, eₘ}, and payoffs R(ai, ej) = rij. Thus R ∈ ℝⁿˣᵐ (rows = alternatives). The brief reverses the letters m and n; only notation differs. The printed Laplace denominator is n even though the course sums over states, and the square worked example cannot disambiguate it. Divide by the number of states m. Example 3’s third average is the repeating decimal 351.666…, rather than a fixed truncated 351.66.
2. The staffing demand table gives (6, 10, 4, 2, 5, 9), but the printed equalities give (6, 8, 4, 5, 9, 8) in cyclic order. Even without integrality the printed equalities are infeasible: alternating sums are 19 and 21. The interactive model takes the demand table as authoritative, with cyclic integer coverage x_(j−1) + x_j ≥ d_j. It explicitly distinguishes this correction from the printed equalities.
3. A Poisson variable is unbounded; the listed seven masses do not sum to one. The tool uses P(K = k | K ≤ 6) for the course’s stated finite range (cutoff editable), discloses the omitted mass and the denominator, and does not silently normalize hand-entered probabilities. Its exact expected costs need not match the printed rounded values. The course column labels EMG and EMV refer to the same expected-cost calculation here.
4. For cost matrices prefer smaller numbers, including in certainty, Laplace, EMV and the decision-tree optimizer. Hurwicz assigns α to the more desirable endpoint (the smaller value for costs). For cost EVPI/EVSI take current cost minus the informed cost. EOL is always minimized. The course says not to buy at the EVPI threshold; the app notes that equality breaks even.
5. Alternatives within numerical tolerance of the optimal score are reported jointly. Values are not rounded before calculations; numeric substitutions shown in the UI may be rounded for readability. A Bayesian observation with zero marginal probability has no defined posterior and contributes nothing to sample value.
6. Explanations for trees assume additive branch adjustments and terminal value, with conditional probabilities at each chance node. The Bayesian extension assumes the observation does not change the payoff conditional on the state; the observation is known before choosing an alternative. Information values are gross before the optional purchase cost.

## Software design

A reusable Python package owns all model validation and mathematics. Streamlit calls it directly and supplies Pandas tables and Plotly figures. The managed Next.js preview calls the same engine on the server and uses PostgreSQL/Drizzle to save the browser's editable workspace. Neither interface implements independent decision criteria. Fixtures are decision inputs, not solved answers.
