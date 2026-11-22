"""Streamlit tree, Bayesian analysis, course models and interactive exercises."""
import json

import pandas as pd
import streamlit as st

from decision_engine.bayesian import bayes
from decision_engine.examples import example, fixtures
from decision_engine.matrix import Matrix, ModelError
from decision_engine.tree import solve_tree
from .charts import distributions, tree_figure
from .common import arabic, display_matrix, heading, load, matrix, show_eval, steps, valid
from .views import display_risk, display_uncertainty


def show_tree(result):
    st.metric("Optimal root value",f"{result['value']:.8g}")
    roots = next(n for n in result["nodes"] if n["id"]==result["root"])
    if roots["chosen"]:
        picks = [roots["branches"][i]["label"] or roots["branches"][i]["to"] for i in roots["chosen"]]
        st.success("Optimal initial choice: " + ", ".join(picks))
    st.latex(r"W(c)=g_c+V(c),\quad V_{\mathrm{chance}}=\sum_c p_cW(c),\quad V_{\mathrm{decision}}=\operatorname{"+result["direction"]+r"}_cW(c)")
    st.plotly_chart(tree_figure(result),width="stretch")
    st.caption("Purple branches trace the optimal contingent policy, including all positive-probability chance outcomes on that policy.")
    by_id = {node["id"]:node for node in result["nodes"]}
    for key in result["evaluationOrder"]:
        node = by_id[key]
        with st.expander(f"{node['name']} · {node['type']} · {node['value']:.8g}"):
            st.text(node["step"])
            if node["branches"]:
                st.dataframe(pd.DataFrame([dict(branch=b["label"] or b["to"],probability=b.get("probability"),
                                                 adjustment=b["immediate"],child_value=b["childValue"],total=b["total"],
                                                 optimal=i in node["chosen"]) for i,b in enumerate(node["branches"])]),hide_index=True)


def tree_page():
    heading("Decision Trees", "شجرة القرار", "Build a rooted multi-stage tree. Enter local probabilities at chance nodes and solve from the leaves back to the root.")
    st.caption("Requested extension · the provided course text lists the chapter but not its detailed rules.")
    model = st.session_state.get("tree",example("expansion")["tree"])
    version = st.session_state.get("tree_version",0)
    objective = st.radio("Tree objective",["profit","cost"],horizontal=True)
    with st.expander("Construct or edit the tree",expanded=True):
        root = st.text_input("Root node ID",model["root"],key=f"tree-root-{version}")
        st.markdown("**Nodes** · Add rows, give each node a unique ID, and choose a type. Only terminal nodes need a terminal payoff.")
        nodes = pd.DataFrame([dict(ID=n["id"],Name=n["name"],Type=n["type"],Payoff=n.get("payoff")) for n in model["nodes"]])
        edges = pd.DataFrame([dict(Parent=n["id"],Child=b["to"],Label=b["label"],Probability=b.get("probability"),Adjustment=b["immediate"]) for n in model["nodes"] for b in n.get("branches",[])],columns=["Parent","Child","Label","Probability","Adjustment"])
        n_table = st.data_editor(nodes,hide_index=True,num_rows="dynamic",width="stretch",key=f"tree-nodes-{version}",column_config={"Type":st.column_config.SelectboxColumn(options=["decision","chance","terminal"])})
        st.markdown("**Branches** · Connect parent and child IDs. Enter probabilities only for chance branches; use negative adjustments for expenses in a profit tree.")
        e_table = st.data_editor(edges,hide_index=True,num_rows="dynamic",width="stretch",key=f"tree-edges-{version}")
    edited = dict(root=root,nodes=[])
    for row in n_table.to_dict("records"):
        node = dict(id=row["ID"],name=row["Name"],type=row["Type"],branches=[])
        if node["type"] == "terminal":
            node["payoff"] = row["Payoff"]
        edited["nodes"].append(node)
    by_id = {n["id"]:n for n in edited["nodes"]}
    unknown = False
    for row in e_table.to_dict("records"):
        if row["Parent"] not in by_id:
            unknown = True
            continue
        by_id[row["Parent"]]["branches"].append(dict(to=row["Child"], label="" if pd.isna(row["Label"]) else row["Label"],
                     immediate=0 if pd.isna(row["Adjustment"]) else row["Adjustment"],probability=None if pd.isna(row["Probability"]) else row["Probability"]))
    cols = st.columns(3)
    clicked_solve = cols[0].button("Solve tree",type="primary")
    if clicked_solve or "tree_result" not in st.session_state:
        if unknown:
            st.error("A branch refers to an unknown parent ID.")
            st.session_state.pop("tree_result",None)
        else:
            result = valid(solve_tree,edited,objective)
            if result:
                st.session_state.tree_result = (edited,objective,result)
                st.session_state.tree = edited
                if clicked_solve:
                    st.session_state.tree_version = version+1
                    st.rerun()
            else:
                st.session_state.pop("tree_result",None)
    if cols[1].button("Reset to expansion example"):
        st.session_state.tree = example("expansion")["tree"]
        st.session_state.tree_version = version+1
        st.session_state.pop("tree_result",None)
        st.rerun()
    cols[2].download_button("Download tree JSON",json.dumps(st.session_state.get("tree",model),ensure_ascii=False,indent=2),"decision-tree.json","application/json")
    if "tree_result" in st.session_state:
        snapshot,obj,result = st.session_state.tree_result
        if snapshot != edited or objective != obj:
            st.info("The editor has changed. Solve again to update the displayed result.")
        show_tree(result)


def show_bayes(m, result):
    st.latex(r"P(e_j\mid z_k)=\frac{P(z_k\mid e_j)p_j}{\sum_l P(z_k\mid e_l)p_l}")
    names = [o["name"] for o in result["observations"]]
    st.dataframe(pd.DataFrame(result["likelihoods"],index=names,columns=m.states),width="stretch")
    series = {"Prior distribution":result["prior"],**{f"After {o['name']}":o["posterior"] for o in result["observations"] if o["posterior"] is not None}}
    st.plotly_chart(distributions(m.states,series),width="stretch")
    with st.expander("Before observing evidence",expanded=True):
        show_eval(m,result["baseline"],chart=False)
    for obs in result["observations"]:
        with st.expander(f"After {obs['name']} · P = {obs['probability']:.8g}"):
            st.text(f"P({obs['name']}) = {obs['marginalStep']}")
            if obs["posterior"] is None:
                st.warning("This evidence is impossible under the model; the posterior is undefined.")
                continue
            steps(m.states,obs["posteriorSteps"])
            st.dataframe(pd.DataFrame([result["prior"],obs["posterior"]],index=["Prior","Posterior"],columns=m.states))
            show_eval(m,obs["emv"],chart=False)
    st.subheader("Value of sample information")
    cols = st.columns(3)
    for col,key,label in zip(cols,("evsi","evpi","net"),("EVSI · gross","EVPI · upper bound","Net sample value")):
        col.metric(label,f"{result[key]:.8g}")
    subtract = r"V_{\mathrm{sample}}-V_{\mathrm{current}}" if m.objective=="profit" else r"V_{\mathrm{current}}-V_{\mathrm{sample}}"
    st.latex(r"V_{\mathrm{sample}}=\sum_k P(z_k)V^*(z_k),\qquad \mathrm{EVSI}="+subtract)
    st.text(f"Sample-informed value = {result['sampleStep']}")
    st.text(f"Perfectly informed value = {result['perfectStep']}; EVPI = {result['evpiStep']}")
    st.text(f"EVSI = {result['evsiStep']}; EVSI net = {result['evsi']:.8g} − {result['price']:.8g} = {result['net']:.8g}")
    st.write("Collect the sample." if result["buy"] else "Do not pay for the sample at this price. Equality breaks even.")


def bayes_page():
    heading("Bayesian Decision Analysis", "نظرية القرار والتحليل البايزي", "Use a diagnostic signal or observation to update state probabilities before choosing an alternative.")
    st.caption("Requested extension · the provided course text does not give the chapter’s formulas or examples.")
    if st.button("Load diagnostic example"):
        load(example("diagnostic"))
        st.rerun()
    m = matrix()
    display_matrix(m)
    pv = st.session_state.p
    version = st.session_state.version
    cs = st.columns(min(len(m.states),4))
    prior = [cs[j%len(cs)].number_input(f"Prior P({s})",0.0,1.0,float(pv[j]),.01,key=f"prior-{version}-{j}") for j,s in enumerate(m.states)]
    states = [f"e{j+1} · {s}" for j,s in enumerate(m.states)]
    names = st.session_state.get("evidence",["Positive signal","Negative signal"])
    default = st.session_state.get("likelihoods",[[.7]*len(states),[.3]*len(states)])
    table = pd.DataFrame([[n,*row] for n,row in zip(names,default)],columns=["Observation",*states])
    st.write("**Likelihood table:** P(observation | state). Each state column must sum to 1. Add or delete observation rows as needed.")
    editor = st.data_editor(table,num_rows="dynamic",hide_index=True,width="stretch",key=f"likelihood-{version}")
    price = st.number_input("Cost of sample information",min_value=0.0,value=float(st.session_state.get("samplePrice",0)),key=f"sample-price-{version}")
    result = valid(bayes,m,prior,editor.iloc[:,0].tolist(),editor.iloc[:,1:].values.tolist(),price)
    if result:
        show_bayes(m,result)


def examples_page():
    heading("Examples & Exercises", "أمثلة وتمارين", "Practice with course cases and clearly labeled supplemental scenarios. Reveal the solution only when you are ready.")
    catalog = fixtures()
    group = st.selectbox("Topic",["All topics",*dict.fromkeys(x["group"] for x in catalog)])
    choices = {x["id"]:x for x in catalog if group == "All topics" or x["group"] == group}
    id_ = st.selectbox("Worked problem",list(choices),format_func=lambda key:choices[key]["title"],key=f"example-{group}")
    item = choices[id_]
    st.subheader(item["title"])
    arabic(item["arabic"])
    st.caption(f"Course example {item['course']}" if "course" in item else "Supplemental practice")
    st.write(item["summary"])
    mode = item["mode"]
    options = {}
    if mode == "staffing":
        st.warning("The printed RHS differs from the demand table. Equalities are infeasible (19 ≠ 21); this tool uses the demand table and cyclic coverage ≥.")
        cols = st.columns(6)
        options["demands"] = [cols[j].number_input(f"Period {j+1}",0,60,d,key=f"demand-{j}") for j,d in enumerate(item["demands"])]
    elif mode == "poisson":
        cols = st.columns(4)
        options = dict(rate=cols[0].number_input("Poisson rate λ",0.,120.,float(item["rate"])),cutoff=cols[1].number_input("Maximum breaks",0,23,item["cutoff"]),
                       upfront=cols[2].number_input("Upfront unit cost",0.,value=float(item["upfront"])),replacement=cols[3].number_input("Shortage unit cost",0.,value=float(item["replacement"])))
    elif mode == "assignment":
        st.markdown("**Repair times (edit any cell)**")
        options["times"] = st.data_editor(pd.DataFrame(item["times"],index=["T1","T2","T3"],columns=["A","B","C"]),key="repair-times").values.tolist()
    payload = valid(example,id_,options)
    if not payload:
        return
    if "matrix" in payload:
        m = Matrix.from_dict(payload["matrix"])
        display_matrix(m,p=payload.get("probabilities"))
    if mode == "tree":
        st.dataframe(pd.DataFrame([dict(parent=n["name"],branch=b["label"],child=b["to"],p=b.get("probability"),adjustment=b["immediate"]) for n in payload["tree"]["nodes"] for b in n.get("branches",[])]),hide_index=True)
        st.caption("Leaf values are in the example tree; load it to edit them.")
        st.write({n["name"]:n["payoff"] for n in payload["tree"]["nodes"] if n["type"]=="terminal"})
    if mode == "bayes":
        st.dataframe(pd.DataFrame(payload["likelihoods"],index=payload["evidence"],columns=m.states))
    if mode == "poisson":
        st.latex(r"q_k=e^{-\lambda}\lambda^k/k!,\quad P(K=k\mid K\leq c)=q_k/\sum_{t=0}^c q_t")
        st.caption(f"Included mass {payload['mass']:.10g}; omitted tail {payload['omitted']:.10g}. Conditioning is an explicit model choice.")
        st.dataframe(pd.DataFrame({"Breaks":m.states,"Raw mass":payload["raw"],"Conditional":payload["probabilities"]}),hide_index=True)
        with st.expander("Poisson probability substitutions"):
            steps(m.states,[f"exp(−{payload['rate']:.8g}) × {payload['rate']:.8g}^{k}/{k}! = {q:.8g}; {q:.8g} / {payload['mass']:.8g} = {p:.8g}" for k,(q,p) in enumerate(zip(payload["raw"],payload["probabilities"]))])
    if "matrix" in payload and st.button("Load into workspace",type="primary"):
        load(payload)
        if mode == "tree":
            st.session_state.tree_version = st.session_state.get("tree_version",0)+1
            st.session_state.pop("tree_result",None)
        target = {"tree":"tree","bayes":"bayes","poisson":"risk","assignment":"certainty"}.get(mode,mode)
        st.switch_page(st.session_state.sl_pages[target])
    st.markdown("**Exercise**")
    st.write(item["task"])
    answer_choices = payload.get("answerChoices")
    answer = st.selectbox("Your alternative",range(len(answer_choices)),format_func=lambda i:answer_choices[i],key=f"answer-{id_}") if answer_choices else st.text_input("Your numeric answer",key=f"answer-{id_}")
    if st.button("Check answer",key=f"check-{id_}"):
        check = valid(example,id_,options,answer=answer)
        if check:
            if check["correct"]:
                st.success("Correct.")
            else:
                st.warning("Not quite. Revisit the criterion, or reveal the solution.")
    if not st.toggle("Reveal complete solution",key=f"reveal-{id_}"):
        return
    solved = valid(example,id_,options,solve=True)
    if not solved:
        return
    res = solved["solution"]
    if mode == "staffing":
        st.latex(r"\min\sum_{j=1}^{6}x_j,\quad x_{j-1}+x_j\ge d_j,\quad x_0=x_6,\quad x_j\in\mathbb{Z}_{\ge0}")
        st.metric("Minimum workforce",res["total"])
        st.dataframe(pd.DataFrame({"Period":["00–04","04–08","08–12","12–16","16–20","20–00"],"Demand":res["demands"],"Start":res["starts"],"Coverage":res["coverage"]}),hide_index=True)
        steps(range(1,7),[f"{res['starts'][j-1]} + {x} = {res['coverage'][j]} ≥ {res['demands'][j]}" for j,x in enumerate(res["starts"])])
    elif mode == "tree":
        show_tree(res)
    elif mode == "bayes":
        show_bayes(m,res)
    elif mode in ("risk","poisson"):
        if mode == "poisson":
            st.latex(r"r_{ik}=c_0i+c_1\max(k-i,0)")
        display_risk(m,res)
    elif mode == "uncertainty":
        display_uncertainty(m,res)
    else:
        if mode == "assignment":
            steps(m.alternatives,[" + ".join(f"{v:.8g}" for v in row)+f" = {sum(row):.8g}" for row in solved["summands"]])
        show_eval(m,res)
