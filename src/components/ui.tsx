import type { ReactNode } from "react";
import { Check, CircleAlert, CircleCheck, Loader2, Sparkles } from "lucide-react";
import katex from "katex";
import { type Evaluation, type Input, type Matrix, type Uncertainty, format } from "./model";

export function Arabic({children,className=""}:{children:ReactNode;className?:string}) {
  return <span className={`arabic ${className}`} lang="ar" dir="rtl">{children}</span>;
}

export function PageHeading({title,ar,description,kicker,actions}:{title:string;ar:string;description:string;kicker:string;actions?:ReactNode}) {
  return <div className="page-title"><div><div className="eyebrow page-kicker">{kicker}</div><h1>{title}</h1><Arabic className="page-arabic">{ar}</Arabic><p>{description}</p></div>{actions&&<div className="page-actions">{actions}</div>}</div>;
}

export function PanelTitle({title,description,action}:{title:string;description?:string;action?:ReactNode}) {
  return <div className="panel-heading"><div><h2>{title}</h2>{description&&<p>{description}</p>}</div>{action}</div>;
}

export function Pill({children,tone="purple"}:{children:ReactNode;tone?:string}) {
  return <span className={`pill tone-${tone}`}>{children}</span>;
}

export function Formula({children}:{children:string}) {
  return <div className="formula" dir="ltr" dangerouslySetInnerHTML={{__html:katex.renderToString(children,{displayMode:true,throwOnError:false,strict:false,trust:false})}}/>;
}

export function Feedback({error,loading,note}:{error?:string|null;loading?:boolean;note?:string}) {
  return error?<div role="alert" className="feedback error"><CircleAlert size={17}/><span>{error}</span></div>:loading?<div role="status" className="feedback"><Loader2 className="spin" size={17}/><span>{note??"Running the analysis…"}</span></div>:null;
}

export function DataTable({head,rows,highlight,activeCol,caption}:{head:ReactNode[];rows:ReactNode[][];highlight?:number[];activeCol?:number;caption?:string}) {
  return <div className="table-scroll"><table className="data-table">{caption&&<caption className="sr-only">{caption}</caption>}<thead><tr>{head.map((h,i)=><th scope="col" key={i} className={activeCol===i?"active-cell":""}>{h}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i} className={highlight?.includes(i)?"winning-row":""}>{row.map((x,j)=>j===0?<th scope="row" key={j}>{x}</th>:<td key={j} className={activeCol===j?"active-cell":""}>{x}</td>)}</tr>)}</tbody></table></div>;
}

export function PayoffTable({matrix,values,probabilities,benchmark,activeState}:{matrix:Matrix;values?:Input[][];probabilities?:Input[];benchmark?:Input[];activeState?:number}) {
  const rows:ReactNode[][]=matrix.alternatives.map((name,i)=>[name,...(values??matrix.values)[i].map(x=>format(x))]);
  if(benchmark) rows.push([<strong key="best">State benchmark</strong>,...benchmark.map(x=>format(x))]);
  if(probabilities) rows.push([<strong key="p">Probability P(eⱼ)</strong>,...probabilities.map(x=>format(x,6))]);
  return <DataTable head={["Alternative",...matrix.states]} rows={rows} activeCol={activeState===undefined?undefined:activeState+1} caption="Decision matrix with alternatives as rows and states as columns"/>;
}

export function Steps({names,steps,label="Numerical substitutions",open=true}:{names:(string|number)[];steps:string[];label?:string;open?:boolean}) {
  return <details className="steps" open={open}><summary>{label}</summary><div className="steps-inner">{steps.map((s,i)=><div key={i}><b>{names[i]}</b><code>{s}</code></div>)}</div></details>;
}

export function Winner({names,result}:{names:string[];result:Evaluation}) {
  return <div className="winner"><div className="winner-icon"><CircleCheck size={22}/></div><div><span className="eyebrow">{result.winners.length>1?"Tied optimal alternatives":"Optimal alternative"}</span><strong>{result.winners.map(i=>names[i]).join(" · ")}</strong></div><div className="winner-score"><b>{format(result.best)}</b><small>{result.direction==="max"?"Maximum":"Minimum"} score</small></div></div>;
}

export function ScoreBars({names,result}:{names:string[];result:Evaluation}) {
  const lo=Math.min(0,...result.scores), hi=Math.max(0,...result.scores), span=hi-lo||1;
  return <div className="score-bars" role="group" aria-label={`${result.label} by alternative`}>{result.scores.map((score,i)=>{
    const win=result.winners.includes(i);
    return <div className="score-bar-row" key={i}><span title={names[i]}>{names[i]}</span><div className="bar-track" aria-hidden="true"><i className="bar-zero" style={{left:`${-lo/span*100}%`}}/><i className={win?"bar-value optimal":"bar-value"} style={{left:`${(Math.min(0,score)-lo)/span*100}%`,width:`${Math.abs(score)/span*100}%`}}/></div><b title={String(score)}>{format(score)}</b></div>;
  })}</div>;
}

export function EvaluationView({matrix,result,chart=true}:{matrix:Matrix;result:Evaluation;chart?:boolean}) {
  return <div className="stack evaluation"><div className="evaluation-title"><h3>{result.label}</h3><Arabic>{result.arabic}</Arabic></div><Formula>{result.formula}</Formula><p className="muted">{result.interpretation}</p><Winner names={matrix.alternatives} result={result}/><DataTable head={["Alternative","Score","Selection"]} highlight={result.winners} rows={matrix.alternatives.map((x,i)=>[x,format(result.scores[i]),result.winners.includes(i)?<Pill key="win" tone="green"><Check size={12}/> Optimal</Pill>:"—"])}/>{chart&&<ScoreBars names={matrix.alternatives} result={result}/>}<Steps names={matrix.alternatives} steps={result.steps}/></div>;
}

const chartColors=["#7556e8","#18a48e","#e89242","#5486e1","#bc65ab","#594c89"];
export function DistributionChart({states,series,label="State probability distribution"}:{states:string[];series:{label:string;values:number[]}[];label?:string}) {
  return <div className="distribution" role="group" aria-label={label}><div className="chart-legend">{series.map((s,i)=><span key={i}><i style={{background:chartColors[i%chartColors.length]}}/>{s.label}</span>)}</div><div className="chart-scroll"><div className="distribution-grid" style={{minWidth:Math.max(280,states.length*Math.max(76,series.length*17))}}><div className="chart-ticks" aria-hidden="true"><span>1</span><span>0.75</span><span>0.5</span><span>0.25</span><span>0</span></div><div className="distribution-columns">{states.map((s,j)=><div className="distribution-group" key={j}><div className="distribution-bars">{series.map((x,i)=><i key={i} title={`${s} · ${x.label}: ${format(x.values[j],6)}`} tabIndex={0} aria-label={`${s}: ${format(x.values[j],6)} (${x.label})`} style={{height:`${100*x.values[j]}%`,background:chartColors[i%chartColors.length]}}/>)}</div><span title={s}>{s}</span></div>)}</div></div></div></div>;
}

export function SensitivityChart({names,result}:{names:string[];result:Uncertainty}) {
  const vals=result.lines.flatMap(l=>[l.best,l.worst]);
  const min=Math.min(...vals), max=Math.max(...vals), span=max-min||1;
  const x=(a:number)=>64+a*626;
  const y=(v:number)=>max===min?118:197-(v-min)/span*158;
  return <div className="sensitivity"><svg viewBox="0 0 725 241" role="img" aria-label="Hurwicz scores across the optimism coefficient, with thick lines on optimal ranges"><rect x="64" y="30" width="626" height="170" rx="4" fill="#faf9fe"/>{[0,.25,.5,.75,1].map(a=><g key={a}><line x1={x(a)} x2={x(a)} y1="30" y2="200" stroke="#e9e6f3"/><text textAnchor="middle" x={x(a)} y="219">{a}</text></g>)}{[0,.25,.5,.75,1].map(a=><g key={a}><line x1="64" x2="690" y1={y(min+span*a)} y2={y(min+span*a)} stroke="#e9e6f3"/><text textAnchor="end" x="57" y={y(min+span*a)+4}>{max===min?(a===.5?format(min):""):format(min+span*a,2)}</text></g>)}<line x1={x(result.alpha)} x2={x(result.alpha)} y1="25" y2="201" stroke="#77708c" strokeDasharray="5 4"/>{result.lines.map((l,i)=>{const color=chartColors[i%chartColors.length];return <g key={i}><line x1={x(0)} x2={x(1)} y1={y(l.worst)} y2={y(l.best)} stroke={color} strokeWidth="1.5"><title>{names[i]}</title></line>{l.interval&&<><line x1={x(l.interval[0])} x2={x(l.interval[1])} y1={y(l.worst+l.slope*l.interval[0])} y2={y(l.worst+l.slope*l.interval[1])} stroke={color} strokeWidth="4"/><circle cx={x(l.interval[0])} cy={y(l.worst+l.slope*l.interval[0])} r="3" fill={color}/></>}</g>;})}<text textAnchor="middle" x="377" y="238">Optimism α</text></svg><div className="chart-legend">{names.map((n,i)=><span key={i}><i style={{background:chartColors[i%chartColors.length]}}/>{n}</span>)}</div></div>;
}

export function Tip({children}:{children:ReactNode}) {
  return <div className="tip"><Sparkles size={19}/><div>{children}</div></div>;
}
