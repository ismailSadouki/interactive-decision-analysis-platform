"""Session, matrix interchange, and presentation helpers (no decision rules)."""
from html import escape
from io import BytesIO

import pandas as pd
import streamlit as st
from openpyxl import Workbook

from decision_engine.examples import example
from decision_engine.matrix import Matrix, ModelError
from .charts import scores


def bootstrap():
    if "model" not in st.session_state:
        load(example("investment"))


def load(item):
    if "matrix" in item:
        st.session_state.model = item["matrix"]
        m = len(item["matrix"]["states"])
        st.session_state.p = item.get("probabilities", [1/m]*m)
        st.session_state.prob_source = "Provided by this example" if "probabilities" in item else "Illustrative equal weights; edit to model actual risk"
        st.session_state.known = item.get("state",0)
        st.session_state.alpha = item.get("alpha",.5)
        if "evidence" not in item:
            st.session_state.pop("evidence",None)
            st.session_state.pop("likelihoods",None)
            st.session_state.pop("samplePrice",None)
    for key in ("tree","evidence","likelihoods","samplePrice"):
        if key in item:
            st.session_state[key] = item[key]
    st.session_state.version = st.session_state.get("version",0)+1


def arabic(text):
    st.html(f'<p lang="ar" dir="rtl" class="dl-arabic">{escape(text)}</p>')


def heading(title, ar, description):
    st.title(title)
    arabic(ar)
    st.write(description)


def valid(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ModelError as exc:
        st.error(str(exc))
        return None


def matrix():
    return Matrix.from_dict(st.session_state.model)


def display_matrix(m, values=None, p=None):
    values = m.values if values is None else values
    df = pd.DataFrame(values, index=m.alternatives, columns=m.states)
    if p is not None:
        # Construct the probability row underneath the matrix, not as a decision alternative.
        df = pd.concat([df,pd.DataFrame([p],index=["P(eⱼ)"],columns=m.states)])
    st.dataframe(df.style.format(precision=6),width="stretch")


def steps(names, strings):
    for name,value in zip(names,strings):
        st.text(f"{name}: {value}")


def show_eval(m, result, *, chart=True):
    st.subheader(result["label"])
    arabic(result["arabic"])
    st.latex(result["formula"])
    st.write(result["interpretation"])
    winning = result["winners"]
    label = ", ".join(m.alternatives[i] for i in winning)
    status = "Tie · " if len(winning)>1 else "Optimal · "
    st.success(f"{status}{label} — {result['best']:.10g} ({'maximum' if result['direction'] == 'max' else 'minimum'} score)")
    df = pd.DataFrame({"Alternative":m.alternatives,"Score":result["scores"],"Optimal":["✓" if i in winning else "" for i in range(len(m.alternatives))]})
    st.dataframe(df,hide_index=True,width="stretch")
    if chart:
        st.plotly_chart(scores(m.alternatives,result),width="stretch")
    with st.expander("Show numerical substitutions",expanded=True):
        steps(m.alternatives,result["steps"])


def parse_table(file, objective):
    if file.size > 2_000_000:
        raise ModelError("Choose a file under 2 MB.")
    try:
        df = pd.read_excel(file,header=None,engine="openpyxl") if file.name.lower().endswith(".xlsx") else pd.read_csv(file,header=None,encoding="utf-8-sig")
    except Exception as exc:
        raise ModelError("Could not read the table. Use a UTF-8 CSV or Excel .xlsx file.") from exc
    if df.shape[0] < 2 or df.shape[1] < 2:
        raise ModelError("Include a header row and a first column containing alternative names.")
    if df.iloc[1:,0].isna().any() or df.iloc[0,1:].isna().any():
        raise ModelError("Alternative and state names cannot be blank.")
    return Matrix(df.iloc[1:,0].astype(str).tolist(),df.iloc[0,1:].astype(str).tolist(),df.iloc[1:,1:].values.tolist(),objective)


def export_matrix(m):
    # Strings that look like formulas are forced to text in spreadsheet exports.
    safe = lambda s: "'"+s if s.startswith(("=","+","-","@","\t","\r")) else s
    csv_df = pd.DataFrame(m.values,index=[safe(x) for x in m.alternatives],columns=[safe(x) for x in m.states])
    cols = st.columns(2)
    cols[0].download_button("Download CSV",csv_df.to_csv(index_label="Alternative").encode("utf-8-sig"),"decision-matrix.csv","text/csv")
    wb = Workbook()
    ws = wb.active
    ws.title = "Decision matrix"
    ws.append(["Alternative",*m.states])
    for name,row in zip(m.alternatives,m.values):
        ws.append([name,*row])
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value,str):
                cell.data_type="s"
    out = BytesIO()
    wb.save(out)
    cols[1].download_button("Download Excel",out.getvalue(),"decision-matrix.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
