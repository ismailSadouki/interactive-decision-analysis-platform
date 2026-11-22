"""Streamlit views for concepts, the matrix, and matrix-based analysis."""
from pathlib import Path

import pandas as pd
import streamlit as st

from decision_engine.criteria import certainty, risk, uncertainty
from decision_engine.examples import example, fixtures
from decision_engine.matrix import Matrix, MAX_DIMENSION, probabilities
from .charts import distributions, scores, sensitivity
from .common import arabic, display_matrix, export_matrix, heading, load, matrix, parse_table, show_eval, steps, valid


def dashboard():
    heading("DecisionLab", "مختبر نظرية اتخاذ القرار", "Build decision models, compare strategies, and see the mathematics behind each result.")
 
    st.subheader("Start a decision problem")
    a,b = st.columns(2)
    a.page_link(st.session_state.sl_pages["matrix"],label="Build a decision matrix",icon=":material/grid_on:")
    # b.page_link(st.session_state.sl_pages["examples"],label="Explore worked examples",icon=":material/book_2:")
    st.subheader("Current workspace")
    display_matrix(matrix())
    


# def concepts():
#     heading("Decision Concepts", "مفهوم القرار والعوامل المؤثرة فيه", "A decision is a reasoned choice among feasible alternatives. Modeling makes the trade-offs explicit.")
#     arabic("القرار هو اختيار بين بدائل ممكنة لتحقيق هدف محدد، في ضوء المعلومات والقيود المتاحة.")
#     st.dataframe(pd.DataFrame([
#         ("Decision maker","متخذ القرار","The person or institution choosing a course of action."),
#         ("Alternatives","البدائل","Actions under the decision maker’s control."),
#         ("States of nature","حالات الطبيعة","Possible external outcomes, such as levels of market demand."),
#         ("Payoffs","العوائد","Profit, cost, or another result for each action and state."),
#         ("Objective and constraints","الأهداف والقيود","Goals and limits on funding, labor, time or external policy.")
#     ],columns=["Element","Arabic term","Meaning"]),hide_index=True,width="stretch")
#     st.markdown("**Influencing factors:** precision of payoff estimates, state probabilities, goals, implementation constraints and the criterion chosen. The course distinguishes personal intuition, descriptive judgment and quantitative analysis.")
#     st.subheader("Try it: an investment budget")
#     st.write("You are the investor. Choose a feasible project to maximize profit under the known medium-demand state. The budget changes feasibility, not the underlying payoffs.")
#     budget = st.slider("Available capital (thousands)",40,150,95)
#     selected = example("investment")["matrix"]
#     capital = [60,90,130]
#     st.dataframe(pd.DataFrame({"Alternative":selected["alternatives"],"Capital required":capital,"Feasible":[cap<=budget for cap in capital]}),hide_index=True)
#     keep = [i for i,cap in enumerate(capital) if cap <= budget]
#     if keep:
#         m = Matrix([selected["alternatives"][i] for i in keep],selected["states"],[selected["values"][i] for i in keep])
#         display_matrix(m)
#         show_eval(m,certainty(m,1),chart=False)
#     else:
#         st.warning("No alternative satisfies the funding constraint.")


def matrix_page():
    heading("Decision Matrix Builder", "بناء مصفوفة القرار", "Edit names and payoffs, or import the first sheet of an Excel workbook or a UTF-8 CSV.")
    m = matrix()
    version = st.session_state.version
    objective = st.radio("Objective",["profit","cost"],format_func=lambda x:"Maximize profit" if x=="profit" else "Minimize cost",horizontal=True,index=int(m.objective=="cost"),key=f"matrix-objective-{version}")
    upload = st.file_uploader("Import CSV / Excel (.xlsx)",type=["csv","xlsx"])
    if upload and st.button("Import spreadsheet"):
        incoming = valid(parse_table,upload,objective)
        if incoming:
            load({"matrix":incoming.to_dict()})
            st.rerun()
    st.latex(r"R=(r_{ij})\in\mathbb{R}^{n\times m},\quad R(a_i,e_j)=r_{ij}")
    st.caption(f"Course notation: n = {len(m.alternatives)} alternatives, m = {len(m.states)} states. Changes below are applied to every analysis page when saved.")
    with st.expander("Edit state names",expanded=True):
        columns = st.columns(min(4,len(m.states)))
        names = [columns[j % len(columns)].text_input(f"State {j+1}",name,max_chars=70,key=f"state-{version}-{j}") for j,name in enumerate(m.states)]
    keys = ["Alternative",*[f"e{j+1}" for j in range(len(names))]]
    df = pd.DataFrame([[name,*row] for name,row in zip(m.alternatives,m.values)],columns=keys)
    edited = st.data_editor(df,hide_index=True,num_rows="dynamic",width="stretch",key=f"payoffs-{version}",
                            column_config={k:st.column_config.NumberColumn(n,required=True) for k,n in zip(keys[1:],names)})
    buttons = st.columns([1,1,1,2])
    save = buttons[0].button("Apply matrix",type="primary")
    add = buttons[1].button("Add state",disabled=len(names)>=MAX_DIMENSION)
    remove = buttons[2].button("Remove state",disabled=len(names)==1)
    to_remove = buttons[3].selectbox("State to remove",range(len(names)),format_func=lambda j:names[j] or f"State {j+1}",label_visibility="collapsed",key=f"remove-state-{version}")
    if save or add or remove:
        alternatives = edited.iloc[:,0].tolist()
        vals = edited.iloc[:,1:].values.tolist()
        prev_p = list(st.session_state.p)
        if add:
            label = f"State {len(names)+1}"
            while label in names:
                label += " +"
            names.append(label)
            vals = [row+[0] for row in vals]
            prev_p.append(0.0)
        if remove:
            names.pop(to_remove)
            vals = [row[:to_remove]+row[to_remove+1:] for row in vals]
            prev_p.pop(to_remove)
        new = valid(Matrix,alternatives,names,vals,objective)
        if new:
            source = st.session_state.prob_source
            load({"matrix":new.to_dict(),"probabilities":prev_p,"alpha":st.session_state.alpha,"state":min(st.session_state.known,len(names)-1)})
            st.session_state.prob_source = source
            st.rerun()
    st.caption("Use the + or row-selection and Delete controls in the table to add or remove alternatives. Exports contain the applied matrix.")
    export_matrix(m)


def certainty_page():
    heading("Decision Under Certainty", "القرار في حالة التأكد", "One state of nature is known to occur. Compare only its payoff column.")
    m = matrix()
    display_matrix(m)
    known = st.selectbox("Known state of nature",range(len(m.states)),index=st.session_state.known,format_func=lambda j:m.states[j],key=f"known-{st.session_state.version}")
    st.session_state.known = known
    show_eval(m,certainty(m,known))


def display_uncertainty(m, result):
    criteria = result["criteria"]
    st.dataframe(pd.DataFrame({"Alternative":m.alternatives,**{r["label"]:[f"{x:.8g}{' ★' if i in r['winners'] else ''}" for i,x in enumerate(r["scores"])] for r in criteria}}),hide_index=True,width="stretch")
    for tab,r in zip(st.tabs([r["label"].split(" (")[0] for r in criteria]),criteria):
        with tab:
            if r["key"] == "savage":
                st.markdown("**Regret matrix** · state benchmarks: " + ", ".join(f"{x:.8g}" for x in result["bestByState"]))
                display_matrix(m,result["regret"])
            show_eval(m,r)
            if r["key"] == "hurwicz":
                st.write("Thick segments show optimal intervals; shared endpoints are ties.")
                st.plotly_chart(sensitivity(m.alternatives,result),width="stretch")
                st.dataframe(pd.DataFrame([{"Alternative":name,"Score line":f"{row['intercept']:.8g} + ({row['slope']:.8g})α",
                                             "Optimal α interval":"Never optimal" if row["interval"] is None else "["+", ".join(f"{x:.8g}" for x in row["interval"])+"]"} for name,row in zip(m.alternatives,result["lines"])]),hide_index=True,width="stretch")
                with st.expander("Pairwise inequalities, intersected with [0, 1]"):
                    for name,line in zip(m.alternatives,result["lines"]):
                        st.markdown(f"**{name}**")
                        for comparison_step in line["comparisons"]:
                            st.text(comparison_step)


def uncertainty_page():
    heading("Decision Under Uncertainty", "القرار في حالة عدم التأكد", "State probabilities are not known. Use explicitly different decision attitudes rather than treating them as measured risk.")
    m = matrix()
    display_matrix(m)
    alpha = st.slider("Hurwicz optimism coefficient α",0.0,1.0,float(st.session_state.alpha),.01,key=f"alpha-{st.session_state.version}")
    st.session_state.alpha = alpha
    display_uncertainty(m,uncertainty(m,alpha))


def display_risk(m, result):
    tabs = st.tabs(["EMV","Expected regret","Dispersion","Perfect information"])
    with tabs[0]:
        show_eval(m,result["emv"])
    with tabs[1]:
        st.latex(r"\ell_{ij}=|r_{ij}-r_j^*|")
        st.write("State benchmarks: " + ", ".join(f"{x:.8g}" for x in result["bestByState"]))
        display_matrix(m,result["regret"],result["probabilities"])
        show_eval(m,result["eol"])
    with tabs[2]:
        st.latex(r"\sigma_i^2=\sum_j p_j(r_{ij}-\mu_i)^2,\quad \sigma_i=\sqrt{\sigma_i^2}")
        st.write("Standard deviation measures spread in payoff units. A lower spread does not automatically make an alternative optimal under EMV.")
        st.dataframe(pd.DataFrame({"Alternative":m.alternatives,"EMV":result["emv"]["scores"],"Variance":result["variance"],"Standard deviation":result["std"]}),hide_index=True)
        steps(m.alternatives,result["varianceSteps"])
    with tabs[3]:
        st.metric("Expected value of perfect information",f"{result['evpi']:.8g}")
        st.latex(result["evpiFormula"] + r",\qquad V_{\rm perfect}=\sum_j p_jr_j^*;\quad \operatorname{EVPI}=\min_i\operatorname{EOL}(a_i)")
        st.text(f"With perfect information: {result['perfectStep']}")
        st.text(f"Best current expected value: {result['emv']['best']:.10g}")
        st.text(f"EVPI = {result['evpiStep']}; minimum EOL = {result['eol']['best']:.10g}")
        st.write(f"At the entered price of {result['price']:.8g}: " + ("buy the information." if result["buy"] else "do not buy. Equality breaks even."))


def risk_page():
    heading("Decision Under Risk", "القرار في حالة المخاطرة", "Use a known or estimated probability distribution. Changing probabilities can change the preferred alternative.")
    m = matrix()
    cols = st.columns(min(4,len(m.states)))
    version = st.session_state.version
    p = [cols[j%len(cols)].number_input(f"P({name})",min_value=0.0,max_value=1.0,value=float(st.session_state.p[j]),step=.01,format="%.9f",key=f"risk-p-{version}-{j}") for j,name in enumerate(m.states)]
    changed = p != st.session_state.p
    st.session_state.p = p
    if changed:
        st.session_state.prob_source = "User-entered probabilities"
    st.caption(f"Current sum: {sum(p):.12g} · {st.session_state.prob_source}")
    if st.button("Normalize probabilities"):
        normalized = valid(probabilities,p,len(p),normalize=True)
        if normalized is not None:
            st.session_state.p = normalized
            st.session_state.prob_source = "Explicitly normalized by user"
            st.session_state.version += 1
            st.rerun()
    price = st.number_input("Price of perfect information",min_value=0.0,value=0.0)
    result = valid(risk,m,p,price=price)
    display_matrix(m,p=p)
    if result:
        st.plotly_chart(distributions(m.states,{"State probabilities":result["probabilities"]}),width="stretch")
        display_risk(m,result)


def comparison():
    heading("Results Comparison", "مقارنة النتائج", "Compare the recommended alternatives on the same model. Scores on different scales are not interchangeable.")
    m = matrix()
    display_matrix(m)
    cert = certainty(m,st.session_state.known)
    unc = uncertainty(m,st.session_state.alpha)
    res = [cert,*unc["criteria"]]
    risk_out = valid(risk,m,st.session_state.p)
    if risk_out:
        res.extend([risk_out["emv"],risk_out["eol"]])
    st.caption(f"Known state: {m.states[st.session_state.known]} · α = {st.session_state.alpha:.5g}")
    rows = [{"Method":r["label"],"Rule":r["direction"],"Optimal":[m.alternatives[i] for i in r["winners"]],"Best score":r["best"]} for r in res]
    st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
    choice = st.selectbox("Inspect a method",range(len(res)),format_func=lambda i:res[i]["label"])
    show_eval(m,res[choice])
