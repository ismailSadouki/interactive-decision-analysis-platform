import { ArrowDownRight, ArrowRight, BookOpen, Braces, ChartNoAxesCombined, ChevronRight, CircleCheck, CircleHelp, GitFork, GraduationCap, Layers3, Lightbulb, ListChecks, Sigma, Table2 } from "lucide-react";
import { CATEGORIES, type Navigation, investment, problems } from "./model";
import { Arabic, DataTable, PageHeading, PayoffTable, Pill, Tip } from "./ui";
import { useState } from "react";
import { useAnalysis } from "./workspace";
import type { Evaluation } from "./model";
import { EvaluationView, Feedback } from "./ui";

const metrics=[
  {icon:Layers3,tone:"purple",value:"3",name:"Decision environments",sub:"Certainty, uncertainty & risk"},
  {icon:ListChecks,tone:"blue",value:"5",name:"Uncertainty criteria",sub:"From Laplace to Hurwicz"},
  {icon:BookOpen,tone:"mint",value:String(problems.length),name:"Worked examples",sub:"Course cases + practice"},
  {icon:GitFork,tone:"amber",value:"2",name:"Advanced tools",sub:"Trees & Bayesian analysis"},
];
const modules=[
  {id:"matrix",icon:Table2,tone:"purple",name:"Decision Matrix",description:"Define alternatives, states of nature, and payoffs."},
  {id:"certainty",icon:CircleCheck,tone:"mint",name:"Decision Under Certainty",description:"Find the best choice when the outcome state is known."},
  {id:"uncertainty",icon:CircleHelp,tone:"blue",name:"Decision Under Uncertainty",description:"Compare five criteria without state probabilities."},
  {id:"risk",icon:ChartNoAxesCombined,tone:"amber",name:"Decision Under Risk",description:"Calculate EMV, expected regret, and information value."},
  {id:"trees",icon:GitFork,tone:"purple",name:"Decision Trees",description:"Model sequential decisions with backward induction."},
  {id:"bayes",icon:Sigma,tone:"rose",name:"Bayesian Analysis",description:"Update probabilities and evaluate new evidence."},
] as const;

export function Dashboard() {
  return <div className="dashboard">
    <div className="dashboard-heading"><div><h1>Dashboard</h1><p>Your interactive workspace for decision theory and analysis.</p></div><span className="edition"><GraduationCap size={16}/> Academic workspace</span></div>
    <section className="hero" aria-label="Start a decision analysis">
      <div className="hero-art" aria-hidden="true"/>
      <div className="hero-copy"><div className="hero-tag"><span/> DECISION THEORY LABORATORY</div><h2>Better decisions.<br/><span>Clearer reasoning.</span></h2><p>Build models, compare strategies, and understand the mathematics behind every decision.</p><div className="hero-actions"><a className="button hero-primary" href="#matrix"><Table2 size={17}/> Build decision matrix <ArrowRight size={16}/></a><a className="button hero-secondary" href="#examples"><BookOpen size={17}/> Explore examples</a></div></div>
    </section>
    <section className="metrics" aria-label="Workspace at a glance">{metrics.map(({icon:Icon,tone,value,name,sub})=><article key={name} className="metric-card"><div className={`icon-tile tone-${tone}`}><Icon size={20}/></div><div className="metric-copy"><div className="metric-value">{value}</div><div className="metric-name">{name}</div><small>{sub}</small></div></article>)}</section>
    <div className="dashboard-lower"><section aria-labelledby="module-heading"><div className="section-heading"><div><h2 id="module-heading">Analysis modules</h2><p>Choose a tool to start solving a decision problem.</p></div></div><div className="module-grid">{modules.map(({id,icon:Icon,tone,name,description})=><a key={id} href={`#${id}`} className="module-card"><div className="module-card-top"><div className={`icon-tile tone-${tone}`}><Icon size={21}/></div><ChevronRight size={18} className="module-arrow"/></div><h3>{name}</h3><p>{description}</p></a>)}</div></section>
    <aside className="roadmap"><div className="roadmap-header"><div className="icon-tile tone-purple"><BookOpen size={20}/></div><span className="eyebrow">COURSE GUIDE</span></div><h2>Course roadmap</h2><Arabic>نظرية اتخاذ القرار</Arabic><p>Follow the course structure, with extra tools for topics beyond the supplied text.</p><div className="roadmap-items">{CATEGORIES.map(({number,name,status})=><div className="roadmap-row" key={number}><span className="roman">{number}</span><span>{name}</span><Pill tone={status==="Course"?"mint":"neutral"}>{status}</Pill></div>)}</div><a className="text-link" href="#reference">View academic coverage <ArrowRight size={15}/></a></aside></div>
    <div className="dashboard-foot"><span><Lightbulb size={16}/> Start with the matrix, then choose a criterion that fits what you know.</span><a href="#concepts" className="text-link">Read decision concepts <ArrowRight size={15}/></a></div>
  </div>;
}

const elements=[
  ["Decision maker","متخذ القرار","The person or organization empowered to choose an action."],
  ["Alternatives","البدائل","The courses of action available to the decision maker."],
  ["States of nature","حالات الطبيعة","External outcomes outside the decision maker’s control."],
  ["Consequences / payoffs","النتائج والعوائد","The result of choosing an alternative under a particular state."],
  ["Objectives & constraints","الأهداف والقيود","The desired outcome and the financial, human, time, or regulatory limits on action."],
];
export function Concepts() {
  const [budget,setBudget]=useState(95);
  const fixture=investment.matrix!;
  const capital=[60,90,130];
  const feasible=capital.map((c,i)=>c<=budget?i:-1).filter(i=>i>=0);
  const matrix={...fixture,alternatives:feasible.map(i=>fixture.alternatives[i]),values:feasible.map(i=>fixture.values[i])};
  const analysis=useAnalysis<Evaluation>(feasible.length?{action:"certainty",matrix,state:1}:null);
  return <div className="stack page-content"><PageHeading kicker="Module I · Foundations" title="Decision Concepts" ar="مفهوم القرار والعوامل المؤثرة فيه" description="See how a real choice becomes a mathematical decision problem."/><section className="panel stack"><h2>What makes a decision?</h2><p>In the course, a decision is a considered choice among available actions. The method can be intuitive, descriptive, or quantitative. A quantitative model clarifies the trade-offs, but its usefulness depends on the quality of the inputs.</p><Arabic>القرار هو اختيار بين بدائل ممكنة لتحقيق هدف محدد، في ضوء المعلومات والقيود المتاحة.</Arabic><DataTable head={["Element","Arabic terminology","Role in the model"]} rows={elements.map(([a,b,c])=>[a,<Arabic key="ar">{b}</Arabic>,c])}/><Tip><b>What influences the choice?</b> Payoff accuracy, probabilities, goals, the ability to implement an action, and the chosen criterion. Financing, staffing, time, and external policy can rule out otherwise attractive alternatives.</Tip></section><section className="panel stack"><div className="panel-heading"><div><h2>Try it · An investment budget</h2><p>You are the investor. Maximize profit under known medium demand, subject to the capital limit.</p></div><Pill tone="mint">Interactive example</Pill></div><label className="range-field">Available capital (thousands) <b>{budget}</b><input type="range" min={40} max={150} value={budget} onChange={e=>setBudget(+e.target.value)}/></label><DataTable head={["Alternative","Capital required","Feasibility"]} rows={fixture.alternatives.map((x,i)=>[x,capital[i],<Pill key="f" tone={feasible.includes(i)?"mint":"neutral"}>{feasible.includes(i)?"Feasible":"Over budget"}</Pill>])}/>{feasible.length?<><PayoffTable matrix={matrix} activeState={1}/><Feedback {...analysis}/>{analysis.data&&<EvaluationView matrix={matrix} result={analysis.data} chart={false}/>}</>:<Tip>No alternative fits the budget. Increase available capital or add another alternative before applying a decision rule.</Tip>}</section></div>;
}

const coverage=[
  ["I · Choice, factors & stages","Feasibility filters and a known-state investment example","concepts","Course-verified"],
  ["II.1 · Payoff matrix","Rows aᵢ, states eⱼ, payoffs rᵢⱼ; CSV and Excel","matrix","Course-verified"],
  ["II.2 · Certainty","Known-column optimum, assignment permutations and cyclic staffing","certainty","Course-verified · staffing correction"],
  ["II.3 · Uncertainty","Laplace, Wald, Maximax, Savage, Hurwicz and α sensitivity","uncertainty","Course-verified"],
  ["II.4 · Risk","EMV, EOL, EVPI, information price, Poisson costs","risk","Course-verified · Poisson interpretation"],
  ["Risk dispersion","Variance and standard deviation of payoff","risk","Requested extension"],
  ["III · Decision trees","Multi-stage backward induction with conditional probabilities","trees","Title supplied · methods are extensions"],
  ["IV · Bayesian analysis","Posterior decisions, EVSI and comparison to EVPI","bayes","Title supplied · methods are extensions"],
  ["V · Utility theory","No method or example is given in the transcription","","Title only · not implemented"],
  ["VI · Game theory","No method or example is given in the transcription","","Title only · not implemented"],
];
export function Reference() {
  return <div className="stack page-content"><PageHeading kicker="Academic source" title="Course Reference" ar="مرجع المقرر والتغطية" description="Trace every method back to the supplied course transcription and distinguish source material from extensions."/><section className="panel stack"><div className="panel-heading"><div><h2>Academic coverage</h2><p>The supplied text runs from the introduction through Example 6. Chapters III–VI appear as titles only.</p></div><Pill tone="purple"><BookOpen size={14}/> Source map</Pill></div><DataTable head={["Course concept","Mathematical method","Application","Status"]} rows={coverage.map(([name,method,id,status])=>[name,method,id?<a key={id} className="text-link" href={`#${id}`}>Open module <ArrowDownRight size={13}/></a>:"—",status])}/></section><section className="panel stack"><h2>Conventions and ambiguous examples</h2><div className="reference-note"><Braces size={20}/><div><h3>Notation and Laplace</h3><p>The course uses n for alternatives and m for states, so the payoff matrix has n × m entries. The printed Laplace denominator is n, but it sums over states. The app uses m; the square course example cannot distinguish the two.</p></div></div><div className="reference-note"><CircleAlertIcon/><div><h3>Example 2 · Staffing</h3><p>The demand table is (6, 10, 4, 2, 5, 9). The printed equalities instead use (6, 8, 4, 5, 9, 8). The alternating sums 19 and 21 would have to agree. The solver uses the table and integer coverage of at least the demand.</p></div></div><div className="reference-note"><Sigma size={20}/><div><h3>Example 5 · Poisson spare parts</h3><p>Poisson mass extends beyond six. The bounded model conditions explicitly on the stated range and displays the omitted mass. Its exact costs may differ from the printed estimates.</p></div></div><div className="reference-note"><CircleCheck size={20}/><div><h3>Costs, ties, and source limits</h3><p>For costs, smaller payoffs are preferred, and optimism weights the best (smallest) cost. Information value is cost saved. The app retains tied optima. Untranscribed diagrams are not reproduced as original illustrations.</p></div></div></section></div>;
}
function CircleAlertIcon(){return <CircleHelp size={20}/>;}

export const shortPageTitle = (id:Navigation) => modules.find(x=>x.id===id)?.name;
