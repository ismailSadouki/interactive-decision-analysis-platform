"""Plotly charts for score, probability, sensitivity, and policy visualization."""
from html import escape

import plotly.graph_objects as go

PURPLE = "#6d54df"
COLORS = [PURPLE, "#159b89", "#df8a34", "#397ac6", "#b65c94"]


def theme(fig, y_title=None):
    return fig.update_layout(template="plotly_white", font=dict(color="#272541"),
                             margin=dict(l=38,r=32,t=22,b=45), yaxis_title=y_title,
                             hoverlabel=dict(namelength=-1))


def scores(names, evaluation):
    return theme(go.Figure(go.Bar(x=names, y=evaluation["scores"],
                                marker_color=[PURPLE if i in evaluation["winners"] else "#cdcbdf" for i in range(len(names))])), evaluation["label"])


def distributions(states, series):
    fig = go.Figure()
    for i,(name,values) in enumerate(series.items()):
        fig.add_bar(name=name, x=states, y=values, marker_color=COLORS[i % len(COLORS)])
    return theme(fig, "Probability").update_layout(barmode="group", yaxis_range=[0,1])


def sensitivity(names, result):
    fig = go.Figure()
    for i,(name,row) in enumerate(zip(names,result["lines"])):
        color = COLORS[i % len(COLORS)]
        def y(a):
            return row["intercept"] + a * row["slope"]
        fig.add_scatter(x=[0,1],y=[y(0),y(1)],mode="lines",name=name,line=dict(color=color,width=1.5))
        if row["interval"] is not None:
            lo,hi = row["interval"]
            fig.add_scatter(x=[lo,hi],y=[y(lo),y(hi)],mode="lines+markers",line=dict(color=color,width=5),
                            marker=dict(size=7),showlegend=False,name=f"Optimal: {name}")
    fig.add_vline(x=result["alpha"],line_dash="dot",line_color="#777089")
    return theme(fig,"Hurwicz score").update_layout(xaxis_title="Optimism coefficient α",xaxis_range=[-0.02,1.02])


def tree_figure(result):
    by_id = {n["id"]:n for n in result["nodes"]}
    positions = {}
    leaf = 0
    def place(key,depth):
        nonlocal leaf
        branches = by_id[key]["branches"]
        if branches:
            ys = [place(e["to"],depth+1) for e in branches]
            y = sum(ys)/len(ys)
        else:
            y = leaf
            leaf += 1
        positions[key]=(depth,-y)
        return y
    place(result["root"],0)
    active = {(e["source"],e["target"]) for e in result["policy"]}
    fig = go.Figure()
    for n in result["nodes"]:
        x,y = positions[n["id"]]
        for branch in n["branches"]:
            xx,yy = positions[branch["to"]]
            on = (n["id"],branch["to"]) in active
            label = escape(branch["label"] or by_id[branch["to"]]["name"])
            if "probability" in branch:
                label += f" · p={branch['probability']:.4g}"
            fig.add_scatter(x=[x,xx],y=[y,yy],mode="lines",line=dict(color=PURPLE if on else "#c0bfcd",width=3 if on else 1.5),
                            text=f"{label}<br>Adjustment: {branch['immediate']:.6g}",hovertemplate="%{text}<extra></extra>",showlegend=False)
            fig.add_annotation(x=(x+xx)/2,y=(y+yy)/2,text=label,showarrow=False,bgcolor="rgba(255,255,255,.9)",font=dict(size=10))
    for kind,symbol,color in (("decision","square",PURPLE),("chance","circle","#159b89"),("terminal","diamond","#64748b")):
        rows = [n for n in result["nodes"] if n["type"] == kind]
        if not rows:
            continue
        fig.add_scatter(x=[positions[n["id"]][0] for n in rows],y=[positions[n["id"]][1] for n in rows],
                        mode="markers+text",text=[f"{escape(n['name'])}<br>{n['value']:.6g}" for n in rows],
                        textposition="top center",marker=dict(size=13,symbol=symbol,color=color),name=kind.title(),
                        customdata=[n["step"] for n in rows],hovertemplate="%{text}<br>%{customdata}<extra></extra>")
    return theme(fig).update_layout(height=max(390,min(1200,80*leaf)),
                                    xaxis=dict(visible=False,range=[-.48,max(x for x,_ in positions.values())+.52]),
                                    yaxis=dict(visible=False,range=[-leaf+0.45,.65]),legend=dict(orientation="h"))
