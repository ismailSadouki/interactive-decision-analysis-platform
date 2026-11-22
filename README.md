# DecisionLab · نظرية اتخاذ القرار

DecisionLab turns the supplied Arabic decision-theory transcription into an interactive laboratory. It includes a **Python/Streamlit application** and a **Next.js browser workspace**. Both call the same independent Python engine; the browser stores anonymous drafts in PostgreSQL via Drizzle and keeps an on-device copy. Neither interface uses hardcoded solved outputs.

## Run the Streamlit application

Python 3.10+ (3.11+ recommended). From the project root:

```sh
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL printed by Streamlit (usually `http://localhost:8501`). The Streamlit app does not need Node.js or PostgreSQL. Use `python -m pytest` to run the independent numerical checks and Streamlit page tests.

## Use the lab

1. **Decision Concepts:** identify the decision maker, feasible alternatives, states, outcomes, objectives, and constraints. Try an interactive budget constraint.
2. **Decision Matrix:** edit row and column names, choose profit or cost, and enter payoffs. Import/export UTF-8 CSV or Excel `.xlsx`. The first row contains state names, the first column contains alternative names, and the remaining cells are numbers. Change the profit/cost objective in the workspace; spreadsheets contain the matrix only. Try `examples/investment.csv`.
3. **Certainty, Uncertainty, Risk:** select a known state, compare the five course criteria, or enter a probability distribution. Hurwicz includes the exact optimal-α ranges. Risk includes EMV, EOL, EVPI, variance, standard deviation, and an information purchase decision. Probabilities are validated and are normalized only when you choose **Normalize probabilities**.
4. **Decision Trees:** create decision, chance, and terminal nodes. Add branch adjustments and chance probabilities. Solve by backward induction and inspect each node’s arithmetic. Highlighting follows all optimal branches and possible chance outcomes, not a single deterministic path.
5. **Bayesian Analysis:** enter prior probabilities and observation likelihoods. Likelihood columns must sum to 1. Inspect posterior calculations and the decision for each observation; compare EVSI, EVPI, and net sample value. An impossible observation has an undefined posterior, not an all-zero posterior.
6. **Results Comparison:** inspect certainty, uncertainty, and risk recommendations for the same model. Different criteria have different scales. Evidence-dependent or staged policies remain in their own modules.
7. **Examples & Exercises:** six course examples and five supplemental problems. Attempt an answer, reveal the worked solution, and load models into the workspace for editing. The assignment, workforce, and Poisson examples have their own editable inputs.

## Source fidelity

[COURSE_MAP.md](COURSE_MAP.md) is the academic coverage table and records all source interpretations. The input was the user’s transcription, not an original PDF. It contains full details for Modules I–II and headings for III–VI only. Tree algorithms, Bayesian mathematics (including EVSI), and payoff dispersion are explicitly labeled requested extensions. Utility theory and game theory were not implemented as course methods because their teaching material is absent. The original untranscribed diagrams are not reproduced. The map also documents the Laplace denominator, infeasible printed staffing equalities, and the explicit conditional Poisson model.

## Project structure

| Location | Purpose |
|---|---|
| `app.py`, `streamlit_ui/` | Streamlit navigation, Pandas tables, Plotly visualizations, file exchange |
| `decision_engine/` | Matrix and model validation; pure criteria, risk, Bayesian, tree, and course-model logic |
| `decision_engine/api.py` | JSON bridge to the same Python engine from Next.js |
| `examples/` | Input fixtures and a sample CSV |
| `tests/` | Numerical and UI smoke tests |
| `src/app/`, `src/components/` | Browser application and server routes |
| `src/db/` | Drizzle PostgreSQL workspace schema |

## Run the browser workspace locally (optional)

Use Node.js supported by Next.js, Python 3.10+ on `PATH`, and a local PostgreSQL database; set `DATABASE_URL` to its connection string. The push below uses the local instance configured in `drizzle.config.json`. For a different instance, run `npx drizzle-kit push --dialect postgresql --schema ./src/db/schema.ts --url "$DATABASE_URL"` instead.

```sh
npm install
npx drizzle-kit push
npm run dev
```

`DECISION_PYTHON` optionally selects another Python executable, for example `.venv/bin/python`. The browser bridge uses a portable Python implementation if NumPy/SciPy are not installed. The Streamlit setup uses NumPy for matrix operations, SciPy MILP for staffing, Pandas for tables, and Plotly for charts. Both the SciPy model and portable schedule algorithm solve the same corrected integer-coverage problem.
# interactive-decision-analysis-platform
