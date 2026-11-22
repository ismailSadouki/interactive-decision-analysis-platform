"""Independent numerical expectations, not snapshots of the application."""
from copy import deepcopy
from itertools import product
from math import exp, sqrt

import pytest

from decision_engine.api import dispatch
from decision_engine.bayesian import bayes
from decision_engine.course_models import _staff_dp, assignment, spare_parts, staffing
from decision_engine.criteria import certainty, hurwicz_intervals, risk, uncertainty
from decision_engine.examples import example, fixtures
from decision_engine.matrix import Matrix, ModelError, probabilities, regret_matrix
from decision_engine.tree import solve_tree


def m(values, objective="profit"):
    return Matrix([f"a{i + 1}" for i in range(len(values))],
                  [f"e{j + 1}" for j in range(len(values[0]))],values,objective)


def test_certainty_profit_negative_and_ties():
    a = m([[-7,2],[-4,5],[-4,1]])
    r = certainty(a,0)
    assert r["scores"] == [-7,-4,-4]
    assert r["winners"] == [1,2]
    assert r["best"] == -4
    assert certainty(a,1)["winners"] == [1]
    with pytest.raises(ModelError,match="state"):
        certainty(a,2)


def test_certainty_minimum_cost():
    r = certainty(m([[5,3],[9,1],[2,9]],"cost"),0)
    assert (r["direction"],r["best"],r["winners"]) == ("min",2,[2])


def test_laplace_rectangular_matrix_and_objective():
    vals = [[1,6,8],[5,-2,6]]
    assert uncertainty(m(vals))["criteria"][0]["scores"] == [5,3]
    assert uncertainty(m(vals,"cost"))["criteria"][0]["winners"] == [1]


def test_all_course_uncertainty_criteria():
    model = m([[35,410,660],[0,450,750],[-115,410,760]])
    r = uncertainty(model,.5)
    by_key = {c["key"]:c for c in r["criteria"]}
    expected = {"laplace":([1105/3,400,1055/3],[1]),"wald":([35,0,-115],[0]),"maximax":([660,750,760],[2]),
                "savage":([100,35,150],[1]),"hurwicz":([347.5,375,322.5],[1])}
    for key,(scores,win) in expected.items():
        assert by_key[key]["scores"] == pytest.approx(scores)
        assert by_key[key]["winners"] == win
        assert len(by_key[key]["steps"]) == 3
    assert r["bestByState"] == [35,450,760]
    assert r["regret"] == [[0,40,100],[35,0,10],[150,40,0]]
    for line,interval in zip(r["lines"],[(0,.28),(.28,.92),(.92,1)]):
        assert line["interval"] == pytest.approx(interval)
    assert uncertainty(model,.28)["criteria"][-1]["winners"] == [0,1]
    assert uncertainty(model,.92)["criteria"][-1]["winners"] == [1,2]
    with pytest.raises(ModelError,match="coefficient"):
        uncertainty(model,1.01)


def test_hurwicz_cost_extremes_and_dominated_lines():
    model = m([[3,50],[14,16],[20,22]],"cost")
    r = uncertainty(model,0)
    assert r["criteria"][1]["winners"] == [1]
    assert r["criteria"][2]["winners"] == [0]
    assert r["criteria"][-1]["scores"] == [50,16,22]
    assert uncertainty(model,1)["criteria"][-1]["scores"] == [3,14,20]
    assert r["lines"][0]["interval"] == pytest.approx([34/45,1])
    assert r["lines"][1]["interval"] == pytest.approx([0,34/45])
    assert r["lines"][2]["interval"] is None
    lines = hurwicz_intervals([7,7,7],[7,7,6],"max")
    assert [x["interval"] for x in lines] == [[0,1],[0,1],[1,1]]


@pytest.mark.parametrize("invalid", ([.4,.4],[-.1,1.1],[1.1,0],[float('nan'),0],[float('inf'),0],[1],[True,0],["",1]))
def test_probability_rejections(invalid):
    with pytest.raises(ModelError):
        probabilities(invalid,2)


def test_probability_no_silent_normalization_and_zero_mass():
    assert probabilities([0,1],2) == [0,1]
    assert probabilities([.2,.3],2,normalize=True) == [.4,.6]
    close = [.4,.6000000001]
    assert probabilities(close,2) == close
    with pytest.raises(ModelError,match="total is zero"):
        probabilities([0,0],2,normalize=True)


def test_course_evpi_expected_regret_and_variance():
    model = m([[-5,8],[10,2]])
    result = risk(model,[.4,.6],price=3.61)
    assert result["emv"]["scores"] == pytest.approx([2.8,5.2])
    assert result["eol"]["scores"] == pytest.approx([6,3.6])
    assert result["emv"]["winners"] == result["eol"]["winners"] == [1]
    assert result["regret"] == [[15,0],[0,6]]
    assert result["perfect"] == pytest.approx(8.8)
    assert result["evpi"] == pytest.approx(3.6)
    assert result["variance"] == pytest.approx([40.56,15.36])
    assert result["std"] == pytest.approx([sqrt(40.56),sqrt(15.36)])
    assert not result["buy"]
    assert risk(model,[.4,.6],price=3.5)["buy"]
    assert not risk(model,[.4,.6],price=3.6)["buy"]


def test_cost_regret_emv_and_zero_probability():
    model = m([[30,5],[8,10]],"cost")
    assert regret_matrix(model) == ([8,5],[[22,0],[0,5]])
    r = risk(model,[.5,.5])
    assert r["emv"]["scores"] == [17.5,9]
    assert r["eol"]["scores"] == [11,2.5]
    assert r["evpi"] == 2.5
    assert risk(model,[0,1])["std"] == [0,0]
    assert risk(model,[0,1])["evpi"] == 0
    assert risk(m([[-8,1],[-7,0]]),[.5,.5])["emv"]["winners"] == [0,1]
    with pytest.raises(ModelError):
        risk(model,[.1,.2])
    with pytest.raises(ModelError):
        risk(model,[1,0],price=-1)


def test_information_value_with_large_common_payoff_offset():
    offset = 2**53
    model = m([[offset+2,offset],[offset,offset+2]])
    r = risk(model,[.5,.5])
    b = bayes(model,[.5,.5],["A","B"],[[1,0],[0,1]])
    # Either uninformed action misses two units half the time. The rounded
    # difference of two large expected totals would not retain that one unit.
    assert r["evpi"] == b["evpi"] == b["evsi"] == 1


def test_oil_risk_with_negative_outcomes():
    r = risk(m([[200_000,-20_000],[1_000,1_000]]),[.25,.75])
    assert r["emv"]["scores"] == [35000,1000]
    assert r["eol"]["scores"] == [15750,49750]


def test_bayesian_cost_diagnostic_and_evsi():
    r = bayes(m([[40,40],[140,0]],"cost"),[.25,.75],["Alert","Clear"],[[.9,.12],[.1,.88]],5)
    pos,neg = r["observations"]
    assert pos["probability"] == pytest.approx(.315)
    assert pos["posterior"] == pytest.approx([.225/.315,.09/.315])
    assert neg["posterior"] == pytest.approx([.025/.685,.66/.685])
    assert pos["emv"]["winners"] == [0]
    assert neg["emv"]["winners"] == r["baseline"]["winners"] == [1]
    assert r["sample"] == pytest.approx(16.1)
    assert r["evsi"] == pytest.approx(18.9)
    assert r["evpi"] == pytest.approx(25)
    assert r["net"] == pytest.approx(13.9)
    assert r["buy"]


def test_bayesian_perfect_and_uninformative_evidence():
    model = m([[10,-3],[0,6]])
    prior = [.4,.6]
    yes = bayes(model,prior,["first","second","impossible"],[[1,0],[0,1],[0,0]])
    assert yes["observations"][2]["posterior"] is None
    assert yes["observations"][2]["emv"] is None
    assert yes["sample"] == pytest.approx(7.6)
    assert yes["evpi"] == yes["evsi"] == pytest.approx(4)
    no = bayes(model,prior,["A","B"],[[.3,.3],[.7,.7]])
    assert no["evsi"] == pytest.approx(0)
    certain = bayes(model,[1,0],["A","B"],[[1,0],[0,1]])
    assert certain["observations"][1]["posterior"] is None
    with pytest.raises(ModelError,match="sum to 1"):
        bayes(model,prior,["x","y"],[[.8,.01],[.3,.99]])


def test_tree_actual_multiple_decision_stages():
    item = next(x for x in fixtures() if x["id"]=="expansion")
    r = solve_tree(item["tree"])
    nodes = {x["id"]:x for x in r["nodes"]}
    assert nodes["positive"]["value"] == 95
    assert nodes["negative"]["value"] == 18
    assert nodes["pilot"]["value"] == pytest.approx(.55*95 + .45*18)
    assert nodes["direct"]["value"] == pytest.approx(44.75)
    assert r["value"] == pytest.approx(52.35)
    assert nodes["root"]["chosen"] == [0]
    assert {(x["source"],x["target"]) for x in r["policy"]} == {("root","pilot"),("pilot","positive"),("pilot","negative"),("positive","rollout"),("negative","pause")}


def test_tree_cost_ties_adjustments_and_zero_chance():
    tree = dict(root="root",nodes=[dict(id="root",name="Choice",type="decision",branches=[dict(to="a",immediate=2),dict(to="b")]),
        dict(id="a",name="Chance",type="chance",branches=[dict(to="c",probability=1,immediate=1),dict(to="d",probability=0)]),
        dict(id="b",name="Outside",type="terminal",payoff=8),dict(id="c",name="Certain",type="terminal",payoff=5),dict(id="d",name="Impossible",type="terminal",payoff=-20)])
    r = solve_tree(tree,"cost")
    assert r["value"] == 8
    assert r["nodes"][0]["chosen"] == [0,1]
    assert all(e["target"] != "d" for e in r["policy"])
    bad = deepcopy(tree)
    bad["nodes"][1]["branches"][0]["probability"] = .4
    with pytest.raises(ModelError,match="sum to 1"):
        solve_tree(bad)
    bad = deepcopy(tree)
    bad["nodes"][0]["branches"].append(dict(to="c"))
    with pytest.raises(ModelError,match="one parent"):
        solve_tree(bad)
    bad = deepcopy(tree)
    bad["nodes"].extend([dict(id="orphan1",name="Cycle1",type="decision",branches=[dict(to="orphan2")]),dict(id="orphan2",name="Cycle2",type="decision",branches=[dict(to="orphan1")])])
    with pytest.raises(ModelError,match="reachable"):
        solve_tree(bad)


def test_assignment_and_staffing():
    a = assignment([[3,7,4],[4,6,6],[3,8,5]])
    assert a["matrix"]["values"] == [[14],[17],[16],[16],[16],[13]]
    assert certainty(Matrix.from_dict(a["matrix"]))["winners"] == [5]
    r = staffing([6,10,4,2,5,9])
    assert r["printedAlternating"] == [19,21]
    assert r["total"] == 21  # The alternating even-period demands alone require 10+2+9 workers.
    assert all(v>=d for v,d in zip(r["coverage"],r["demands"]))
    d = [1,2,0,0,2,1]
    brute = min(sum(x) for x in product(range(3),repeat=6) if all(x[i-1]+x[i]>=n for i,n in enumerate(d)))
    assert sum(_staff_dp(d)) == staffing(d)["total"] == brute
    assert staffing([0]*6)["total"] == 0


def test_poisson_probability_and_minimizing_cost():
    r = spare_parts()
    assert r["mass"] == pytest.approx(exp(-2)*331/45)
    assert r["omitted"] == pytest.approx(1-exp(-2)*331/45)
    assert sum(r["probabilities"]) == pytest.approx(1)
    assert r["matrix"]["values"][3] == [30000,30000,30000,30000,70000,110000,150000]
    assert risk(Matrix.from_dict(r["matrix"]),r["probabilities"])["emv"]["winners"] == [3]
    assert spare_parts(0)["probabilities"] == [1,0,0,0,0,0,0]


def test_validation_and_all_examples():
    with pytest.raises(ModelError,match="unique"):
        Matrix(["a","a"],["e"],[[1],[2]])
    with pytest.raises(ModelError,match="payoff per state"):
        m([[1,2],[3]])
    with pytest.raises(ModelError,match="finite"):
        m([[float("nan")]])
    assert "solution" not in example("repair")
    assert example("repair",answer=5)["correct"]
    assert not example("repair",answer=0)["correct"]
    assert example("information",answer=3.6)["correct"]
    assert example("spares",{"upfront":0,"replacement":0},answer=6)["correct"]
    for x in fixtures():
        assert example(x["id"],solve=True)["solution"]
    comp = dispatch(dict(action="comparison",matrix=m([[1,2],[3,4]]).to_dict(),probabilities=[.2,.1]))
    assert "riskError" in comp and "risk" not in comp
