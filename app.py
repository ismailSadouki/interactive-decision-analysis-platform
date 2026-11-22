"""Run with: streamlit run app.py"""
import streamlit as st

from streamlit_ui import advanced, views
from streamlit_ui.common import bootstrap

st.set_page_config(page_title="DecisionLab · Decision Analysis",page_icon="📐",layout="wide")
st.html("""<style>
.dl-arabic {text-align:right;direction:rtl;color:#5b4ca1;font-size:1.13rem;line-height:1.65;margin:.2rem 0 1rem}
[data-testid='stSidebar'] [data-testid='stSidebarNav'] {padding-top:.25rem}
[data-testid='stMainBlockContainer'] {max-width:1260px;padding-top:2.1rem}
</style>""")
bootstrap()

pages = {
    "dashboard": st.Page(views.dashboard,title="Dashboard",icon=":material/dashboard:",default=True),
    # "concepts": st.Page(views.concepts,title="Decision Concepts",url_path="concepts",icon=":material/lightbulb:"),
    "matrix": st.Page(views.matrix_page,title="Decision Matrix",url_path="matrix",icon=":material/grid_on:"),
    "certainty": st.Page(views.certainty_page,title="Certainty",url_path="certainty",icon=":material/check_circle:"),
    "uncertainty": st.Page(views.uncertainty_page,title="Uncertainty",url_path="uncertainty",icon=":material/help:"),
    "risk": st.Page(views.risk_page,title="Risk Analysis",url_path="risk",icon=":material/show_chart:"),
    "tree": st.Page(advanced.tree_page,title="Decision Trees",url_path="trees",icon=":material/account_tree:"),
    "bayes": st.Page(advanced.bayes_page,title="Bayesian Analysis",url_path="bayes",icon=":material/functions:"),
    "comparison": st.Page(views.comparison,title="Results Comparison",url_path="comparison",icon=":material/compare_arrows:"),
    # "examples": st.Page(advanced.examples_page,title="Examples & Exercises",url_path="examples",icon=":material/menu_book:")
}
st.session_state.sl_pages = pages
st.navigation({"Workspace":[pages[k] for k in ("dashboard","matrix")],
               "Analysis":[pages[k] for k in ("certainty","uncertainty","risk","tree","bayes")]},expanded=True).run()
