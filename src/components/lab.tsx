"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { ArrowLeftRight, BookOpen, ChartNoAxesCombined, ChevronRight, CircleCheck, CircleHelp, GitFork, GraduationCap, LayoutDashboard, LibraryBig, Lightbulb, Menu, Network, PanelTop, Sigma, Table2, X, type LucideIcon } from "lucide-react";
import { BayesianPage, TreePage } from "./advanced";
import { CertaintyPage, ComparisonPage, RiskPage, UncertaintyPage } from "./analysis";
import { Concepts, Dashboard, Reference } from "./dashboard";
import { ExamplesPage, destination } from "./examples";
import { MatrixEditor } from "./matrix";
import { makeDraft, type Navigation, type Problem } from "./model";
import { Arabic } from "./ui";
import { useWorkspace } from "./workspace";

const groups:{label:string;items:{id:Navigation;name:string;icon:LucideIcon}[]}[]=[
  {label:"Workspace",items:[{id:"dashboard",name:"Dashboard",icon:LayoutDashboard},{id:"concepts",name:"Decision Concepts",icon:Lightbulb},{id:"matrix",name:"Decision Matrix",icon:Table2}]},
  {label:"Analysis",items:[{id:"certainty",name:"Certainty",icon:CircleCheck},{id:"uncertainty",name:"Uncertainty",icon:CircleHelp},{id:"risk",name:"Risk Analysis",icon:ChartNoAxesCombined},{id:"trees",name:"Decision Trees",icon:GitFork},{id:"bayes",name:"Bayesian Analysis",icon:Sigma}]},
  {label:"Resources",items:[{id:"comparison",name:"Results Comparison",icon:ArrowLeftRight},{id:"examples",name:"Examples & Exercises",icon:LibraryBig}]},
];
const items=groups.flatMap(group=>group.items.map(item=>({...item,group:group.label})));
const getPage=():Navigation=>{
  const hash=window.location.hash.slice(1);
  return hash==="reference"||items.some(i=>i.id===hash)?hash as Navigation:"dashboard";
};
function subscribe(fn:()=>void){window.addEventListener("hashchange",fn);return ()=>window.removeEventListener("hashchange",fn);}
const start=():Navigation=>"dashboard";

export function Lab() {
  const page=useSyncExternalStore(subscribe,getPage,start);
  const [mobile,setMobile]=useState(false);
  const {draft,update,status}=useWorkspace();
  const meta=items.find(i=>i.id===page);
  const title=meta?.name??"Course Reference";
  useEffect(()=>{window.scrollTo(0,0);document.title=`${title} · DecisionLab`;},[title]);
  useEffect(()=>{const close=(e:KeyboardEvent)=>{if(e.key==="Escape")setMobile(false);};window.addEventListener("keydown",close);return ()=>window.removeEventListener("keydown",close);},[]);
  function load(problem:Problem){update(old=>makeDraft(problem,old));window.location.hash=destination(problem);}
  const bound={draft,update};
  const contents=page==="dashboard"?<Dashboard/>:page==="concepts"?<Concepts/>:page==="matrix"?<MatrixEditor {...bound} status={status}/>:page==="certainty"?<CertaintyPage {...bound}/>:page==="uncertainty"?<UncertaintyPage {...bound}/>:page==="risk"?<RiskPage {...bound}/>:page==="trees"?<TreePage {...bound}/>:page==="bayes"?<BayesianPage {...bound}/>:page==="comparison"?<ComparisonPage {...bound}/>:page==="examples"?<ExamplesPage load={load}/>:<Reference/>;
  return <div className="app-shell"><a className="skip-link" href="#main-workspace" onClick={e=>{e.preventDefault();document.getElementById("main-workspace")?.focus();}}>Skip to content</a>{mobile&&<button className="sidebar-shade" aria-label="Close navigation" onClick={()=>setMobile(false)}/>}
    <aside className={`sidebar ${mobile?"open":""}`} aria-label="DecisionLab navigation"><a href="#dashboard" className="brand" onClick={()=>setMobile(false)}><span className="brand-icon"><Network size={23} strokeWidth={1.9}/></span><span><strong>Decision<span>Lab</span></strong><small>DECISION THEORY</small></span></a><button className="close-side icon-button" aria-label="Close navigation" onClick={()=>setMobile(false)}><X size={20}/></button><nav className="side-nav">{groups.map(g=><section key={g.label} aria-label={g.label}><h2>{g.label}</h2>{g.items.map(({id,name,icon:Icon})=><a className={`nav-item ${id===page?"current":""}`} href={`#${id}`} onClick={()=>setMobile(false)} aria-current={id===page?"page":undefined} key={id}><Icon size={18} strokeWidth={1.8}/><span>{name}</span>{id===page&&<span className="nav-indicator"/>}</a>)}</section>)}</nav><a href="#reference" className="sidebar-foot" onClick={()=>setMobile(false)}><span className="side-foot-icon"><GraduationCap size={19}/></span><span><strong>Academic edition</strong><Arabic>نظرية اتخاذ القرار</Arabic></span><ChevronRight size={14}/></a></aside>
    <div className="workspace"><header className="topbar"><div className="breadcrumbs"><button className="icon-button open-side" aria-label="Open navigation" aria-expanded={mobile} onClick={()=>setMobile(true)}><Menu size={21}/></button><PanelTop className="crumb-icon" size={17} strokeWidth={1.75}/><span className="crumb-root">{meta?.group??"Resources"}</span><ChevronRight size={14} className="crumb-arrow"/><span className="crumb-current">{title}</span></div><div className="top-actions"><span className="language-label" title="English with Arabic terminology">EN <i/> <Arabic>عربي</Arabic></span><a href="#reference" className="button secondary top-reference" aria-label="Course Reference"><BookOpen size={16} strokeWidth={1.8}/><span>Course reference</span></a></div></header><main className="workspace-inner" id="main-workspace" tabIndex={-1}><div key={page} className="view-frame">{contents}</div></main></div>
  </div>;
}
