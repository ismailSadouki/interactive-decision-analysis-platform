import { useState } from "react";
import { ArrowLeft, ArrowRight, BookOpen, Boxes, ChartNoAxesCombined, Clock, Eye, EyeOff, FlaskConical, GitFork, Info, Landmark, Leaf, Wrench } from "lucide-react";
import { BayesianView, TreeView } from "./advanced";
import { RiskView, UncertaintyView } from "./analysis";
import { analyze, editing, format, problems, type Bayesian, type Evaluation, type Input, type Problem, type Risk, type SolvedTree, type Staffing, type Uncertainty } from "./model";
import { Arabic, DataTable, EvaluationView, Feedback, Formula, PageHeading, PanelTitle, PayoffTable, Pill, Steps, Tip } from "./ui";
import { useAnalysis } from "./workspace";

const icons={wrench:Wrench,clock:Clock,chart:ChartNoAxesCombined,land:Landmark,boxes:Boxes,info:Info,tree:GitFork,leaf:Leaf,flask:FlaskConical};
const groups=["All examples","Course examples","Certainty","Uncertainty","Risk","Trees","Bayesian"];
const tone:Record<string,string>={Certainty:"mint",Uncertainty:"blue",Risk:"amber",Trees:"purple",Bayesian:"rose"};

function Solution({item}:{item:Problem}) {
  const {mode,solution,matrix}=item;
  if(!solution)return null;
  if(mode==="staffing"){
    const r=solution as Staffing;
    return <section className="panel stack"><PanelTitle title="Optimal workforce schedule" description="Start xⱼ workers at period j. They cover this period and the next one, including the midnight wraparound." action={<Pill tone="green">Minimum · {r.total} workers</Pill>}/><Formula>{String.raw`\min\sum_{j=1}^6x_j,\qquad x_{j-1}+x_j\ge d_j,\qquad x_0=x_6,\qquad x_j\in\mathbb{Z}_{\ge0}`}</Formula><DataTable head={["Period","Workers required","Starts here","Coverage"]} rows={["00–04","04–08","08–12","12–16","16–20","20–00"].map((p,j)=>[p,r.demands[j],r.starts[j],r.coverage[j]])}/><Steps names={r.starts.map((_,j)=>`Period ${j+1}`)} steps={r.starts.map((x,j)=>`${r.starts.at(j-1)} + ${x} = ${r.coverage[j]} ≥ ${r.demands[j]}`)}/><Tip><b>{r.starts.join(" + ")} = {r.total} workers.</b> This is an optimal integer solution of the corrected coverage constraints. The printed equalities require equal alternating sums, but yield {r.printedAlternating.join(" and ")}.</Tip></section>;
  }
  if(mode==="tree")return <TreeView result={solution as SolvedTree}/>;
  if(mode==="bayes")return <BayesianView matrix={matrix!} result={solution as Bayesian}/>;
  if(mode==="uncertainty")return <UncertaintyView matrix={matrix!} result={solution as Uncertainty} defaultKey={item.criterion}/>;
  if(mode==="risk"||mode==="poisson")return <>{mode==="poisson"&&<section className="panel stack"><PanelTitle title="Inventory cost" description="Pay upfront for each spare, plus replacement and downtime costs for shortages."/><Formula>{String.raw`r_{ik}=c_0 i+c_1\max(k-i,0)`}</Formula><Steps names={["Example cell: no spares, maximum breaks"]} steps={[`${format(item.upfront)}(0) + ${format(item.replacement)} × max(${item.cutoff} − 0, 0) = ${format(matrix!.values[0].at(-1))}`]}/></section>}<RiskView matrix={matrix!} result={solution as Risk} initial={item.criterion==="evpi"?"information":"emv"}/></>;
  return <section className="panel stack">{mode==="assignment"&&<><PanelTitle title="Enumerate one-to-one assignments" description="Each feasible alternative assigns every technician to a different machine. Sum the repair time across the three assignments."/><Formula>{String.raw`r(a_i)=\sum_{t=1}^{n} c_{t,a_i(t)},\qquad a^*\in\operatorname*{argmin}_i r(a_i)`}</Formula><Steps names={matrix!.alternatives} steps={item.summands!.map((r,i)=>r.map(x=>format(x)).join(" + ")+` = ${format(matrix!.values[i][0])}`)} label="Repair time substitutions"/></>}<EvaluationView matrix={matrix!} result={solution as Evaluation}/></section>;
}

function ProblemDetail({problem,onBack,load}:{problem:Problem;onBack:()=>void;load:(p:Problem)=>void}) {
  const {mode}=problem;
  const [reveal,setReveal]=useState(false);
  const [answer,setAnswer]=useState("");
  const [status,setStatus]=useState<{error?:string;correct?:boolean;loading?:boolean}>({});
  const [demands,setDemands]=useState<Input[]>(problem.demands??[]);
  const [times,setTimes]=useState<Input[][]>(Array.isArray(problem.times)?problem.times:[]);
  const [parameters,setParameters]=useState({rate:problem.rate,cutoff:problem.cutoff,upfront:problem.upfront,replacement:problem.replacement});
  const options=mode==="staffing"?{demands}:mode==="assignment"?{times}:mode==="poisson"?parameters:{};
  const {data,error,loading}=useAnalysis<Problem>({action:"example",id:problem.id,options,solve:reveal},150);
  const current=data??problem;
  const checks=current.answerChoices;
  async function check() {
    setStatus({loading:true});
    try {const r=await analyze<Problem>({action:"example",id:problem.id,options,answer});setStatus({correct:r.correct});}
    catch(e){setStatus({error:(e as Error).message});}
  }
  return <div className="stack page-content"><div><button onClick={onBack} className="text-link"><ArrowLeft size={16}/> All examples</button></div><PageHeading kicker={problem.course?`Course example ${problem.course} · ${problem.group}`:`Supplemental practice · ${problem.group}`} title={problem.title} ar={problem.arabic} description={problem.summary} actions={current.matrix&&<button onClick={()=>load(current)} className="button primary">Load into workspace <ArrowRight size={16}/></button>}/>
    <section className="panel stack"><PanelTitle title="Problem data" description={mode==="staffing"?"Each worker covers two consecutive four-hour periods.":mode==="assignment"?"Edit repair times, then examine all feasible assignments.":mode==="poisson"?"Generate breakage probabilities and costs from the stated parameters.":mode==="tree"?"The matrix compares the immediate options. The tree below adds a pilot and later decisions.":"Use the supplied payoffs and conditions to solve the exercise."}/>
      {mode==="staffing"&&<><Tip>The printed demand equalities are inconsistent (19 ≠ 21). This exercise uses the demand table with integer coverage of at least the demand.</Tip><div className="field-grid">{demands.map((d,i)=><label key={i} className="field"><span>Period {i+1} demand</span><input inputMode="numeric" maxLength={2} value={editing(d)} onChange={e=>{setDemands(demands.map((v,j)=>i===j?e.target.value:v));setStatus({});}}/></label>)}</div></>}
      {mode==="assignment"&&<div className="table-scroll matrix-wrap"><table className="matrix-edit"><thead><tr><th>Technician</th><th>Machine A</th><th>Machine B</th><th>Machine C</th></tr></thead><tbody>{times.map((row,i)=><tr key={i}><th scope="row">T{i+1}</th>{row.map((v,j)=><td key={j}><input aria-label={`Technician ${i+1}, machine ${j+1}`} inputMode="decimal" maxLength={32} value={editing(v)} onChange={e=>{setTimes(times.map((r,k)=>k===i?r.map((x,l)=>l===j?e.target.value:x):r));setStatus({});}}/></td>)}</tr>)}</tbody></table></div>}
      {mode==="poisson"&&<><div className="field-grid">{Object.entries({rate:"Poisson rate λ",cutoff:"Maximum breakages",upfront:"Upfront unit cost",replacement:"Shortage unit cost"}).map(([k,label])=><label className="field" key={k}><span>{label}</span><input inputMode="decimal" maxLength={32} value={editing(parameters[k as keyof typeof parameters])} onChange={e=>{setParameters({...parameters,[k]:e.target.value});setStatus({});}}/></label>)}</div><Formula>{String.raw`q_k=e^{-\lambda}\frac{\lambda^k}{k!},\qquad P(K=k\mid K\le c)=\frac{q_k}{\sum_{t=0}^c q_t}`}</Formula>{data?.raw&&<><Tip>The bounded model retains mass {format(data.mass,9)} and omits tail mass {format(data.omitted,9)}. Conditioning on the stated range is explicit.</Tip><DataTable head={["Breakages k","Unconditioned mass","Conditional probability"]} rows={data.raw.map((x,i)=>[i,format(x,9),format(data.probabilities?.[i],9)])}/><Steps names={data.raw.map((_,i)=>`k = ${i}`)} steps={data.raw.map((x,i)=>`e^(−${format(data.rate)}) × ${format(data.rate)}^${i} / ${i}! = ${format(x,9)}; ${format(x,9)} / ${format(data.mass,9)} = ${format(data.probabilities?.[i],9)}`)} open={false}/></>}</>}
      <Feedback error={error} loading={loading} note="Preparing the problem…"/>{current.matrix&&<PayoffTable matrix={current.matrix} probabilities={current.probabilities} activeState={current.state}/>}
      {mode==="bayes"&&<><h3>Sensor likelihoods</h3><DataTable head={["Observation",...current.matrix!.states]} rows={current.likelihoods!.map((r,i)=>[current.evidence![i],...r.map(x=>format(x))])}/><p className="muted">Sample cost: {format(current.samplePrice)} (the exercise asks for gross value before cost).</p></>}
      {mode==="tree"&&<><h3>Branches and terminal payoffs</h3><DataTable head={["Parent node","Branch","Probability","Adjustment","Child","Terminal value"]} rows={current.tree!.nodes.flatMap(n=>(n.branches??[]).map(b=>{const child=current.tree!.nodes.find(x=>x.id===b.to)!;return [n.name,b.label,format(b.probability),format(b.immediate),child.name,format(child.payoff)];}))}/></>}
    </section><section className="panel stack"><PanelTitle title="Try it yourself" description={problem.task} action={<Pill>Exercise mode</Pill>}/><div className="exercise-form"><label className="field"><span>Your answer</span>{checks?<select value={answer} onChange={e=>{setAnswer(e.target.value);setStatus({});}}><option value="" disabled>Select an alternative</option>{checks.map((n,i)=><option key={i} value={i}>{n}</option>)}</select>:<input inputMode="decimal" maxLength={32} value={answer} placeholder="Enter your answer" onChange={e=>{setAnswer(e.target.value);setStatus({});}}/>}</label><button className="button secondary" onClick={check} disabled={status.loading||!answer.trim()}>Check answer</button><button className="button primary" onClick={()=>setReveal(!reveal)}>{reveal?<EyeOff size={16}/>:<Eye size={16}/>} {reveal?"Hide solution":"Reveal solution"}</button></div><Feedback {...status}/>{status.correct!==undefined&&<div role="status" className={`feedback ${status.correct?"success":""}`}>{status.correct?"Correct. Reveal the solution to verify your work.":"Not quite. Try again or reveal the solution for a worked explanation."}</div>}</section>{reveal&&data?.solution&&<Solution item={data}/>}</div>;
}

export function ExamplesPage({load}:{load:(p:Problem)=>void}) {
  const [group,setGroup]=useState("All examples");
  const [id,setId]=useState<string|null>(null);
  const selected=problems.find(p=>p.id===id);
  function open(id:string|null){setId(id);window.scrollTo(0,0);}
  if(selected)return <ProblemDetail key={selected.id} problem={selected} load={load} onBack={()=>open(null)}/>;
  const visible=problems.filter(p=>group==="All examples"||(group==="Course examples"?p.course!==undefined:p.group===group));
  return <div className="stack page-content"><PageHeading kicker="Resources · Practice library" title="Examples & Exercises" ar="أمثلة وتمارين" description="Work through the six supplied course examples or practice with supplemental scenarios. Check your answer before revealing the solution." actions={<Pill><BookOpen size={15}/> {problems.length} scenarios</Pill>}/><div className="tabs filters" role="group" aria-label="Filter examples">{groups.map(g=><button key={g} aria-pressed={g===group} onClick={()=>setGroup(g)}>{g}</button>)}</div><div className="example-grid">{visible.map(p=>{const Icon=icons[p.icon as keyof typeof icons]??BookOpen;return <button key={p.id} className="example-card" onClick={()=>open(p.id)}><div className="module-card-top"><div className={`icon-tile tone-${tone[p.group]}`}><Icon size={21}/></div><Pill tone={p.course?"mint":"neutral"}>{p.course?`Course ${p.course}`:"Practice"}</Pill></div><h3>{p.title}</h3><Arabic>{p.arabic}</Arabic><p>{p.summary}</p><span className="text-link">Open exercise <ArrowRight size={15}/></span></button>;})}</div></div>;
}

export function destination(item:Problem):"certainty"|"risk"|"uncertainty"|"trees"|"bayes"|"matrix" {
  switch(item.mode) {case "assignment":case "certainty":return "certainty";case "poisson":case "risk":return "risk";case "uncertainty":return "uncertainty";case "tree":return "trees";case "bayes":return "bayes";default:return "matrix";}
}
