import { useRef, useState, type ChangeEvent } from "react";
import { ArrowDownToLine, ArrowRight, Check, ChevronDown, FileSpreadsheet, Plus, ShieldCheck, Trash2, UploadCloud } from "lucide-react";
import { analyze, defaultEvidence, defaultLikelihoods, download, editing, equal, investment, makeDraft, MAX_SIZE, type Draft, type Matrix, type Update } from "./model";
import { Feedback, Formula, PageHeading, PanelTitle, Pill, Tip } from "./ui";
import type { SaveState } from "./workspace";

export function csvTable(text:string):string[][] {
  const source=text.replace(/^\ufeff/,"");
  const rows:string[][]=[];
  let row:string[]=[], field="", quoted=false;
  for(let i=0;i<source.length;i++) {
    const c=source[i];
    if(quoted) {
      if(c==='"'&&source[i+1]==='"') { field+='"'; i++; }
      else if(c==='"') quoted=false;
      else field+=c;
    } else if(c==='"'&&!field) quoted=true;
    else if(c===",") { row.push(field); field=""; }
    else if(c==="\r"||c==="\n") {
      if(c==="\r"&&source[i+1]==="\n") i++;
      row.push(field); if(row.some(x=>x.trim())) rows.push(row); row=[]; field="";
    } else field+=c;
  }
  if(quoted) throw new Error("The CSV contains an unclosed quoted cell.");
  row.push(field); if(row.some(x=>x.trim())) rows.push(row);
  return rows;
}
const quoted=(x:string)=>`"${x.replaceAll('"','""')}"`;
const spreadsheetLabel=(x:string)=>/^[=+\-@\r\t]/.test(x)?`'${x}`:x;
const freshName=(root:string,names:string[])=>{let n=names.length+1;while(names.includes(`${root} ${n}`))n++;return `${root} ${n}`;};

export function MatrixEditor({draft,update,status}:{draft:Draft;update:Update;status:SaveState}) {
  const {matrix}=draft;
  const upload=useRef<HTMLInputElement>(null);
  const exportMenu=useRef<HTMLDetailsElement>(null);
  const [notice,setNotice]=useState({error:"",success:"",loading:false});
  const [validated,setValidated]=useState("");
  const shape=`${matrix.alternatives.length} × ${matrix.states.length}`;
  function change(fn:(m:Matrix)=>Matrix) { setNotice({error:"",success:"",loading:false}); update(old=>({matrix:fn(old.matrix)})); }
  function addRow() { change(m=>({...m,alternatives:[...m.alternatives,freshName("Alternative",m.alternatives)],values:[...m.values,Array<number>(m.states.length).fill(0)]})); }
  function removeRow(i:number) { change(m=>({...m,alternatives:m.alternatives.filter((_,k)=>k!==i),values:m.values.filter((_,k)=>k!==i)})); }
  function addState() {
    setNotice({error:"",success:"",loading:false});
    update(old=>({matrix:{...old.matrix,states:[...old.matrix.states,freshName("State",old.matrix.states)],values:old.matrix.values.map(r=>[...r,0])},
      probabilities:[...old.probabilities,0],prior:[...old.prior,0],likelihoods:old.likelihoods.map((r,i)=>[...r,i===0?1:0])}));
  }
  function removeState(j:number) {
    setNotice({error:"",success:"",loading:false});
    update(old=>({matrix:{...old.matrix,states:old.matrix.states.filter((_,i)=>i!==j),values:old.matrix.values.map(r=>r.filter((_,i)=>i!==j))},
      known:old.known===j?0:old.known-(old.known>j?1:0),probabilities:old.probabilities.filter((_,i)=>i!==j),prior:old.prior.filter((_,i)=>i!==j),
      likelihoods:old.likelihoods.map(r=>r.filter((_,i)=>i!==j))}));
  }
  async function importFile(e:ChangeEvent<HTMLInputElement>) {
    const file=e.target.files?.[0];e.target.value="";if(!file)return;
    setNotice({error:"",success:"",loading:true});
    try {
      if(file.size>2_000_000)throw new Error("Choose a CSV or Excel file smaller than 2 MB.");
      const rows=file.name.toLowerCase().endsWith(".xlsx")?await (await import("read-excel-file/browser")).readSheet(file,1):csvTable(await file.text());
      if(rows.length<2||rows[0].length<2)throw new Error("Use a header row for states and a first column for alternative names.");
      const cell=(x:unknown)=>typeof x==="string"||typeof x==="number"?String(x).trim():"";
      const next={objective:matrix.objective,states:rows[0].slice(1).map(cell),alternatives:rows.slice(1).map(r=>cell(r[0])),values:rows.slice(1).map(r=>r.slice(1).map(cell))};
      const clean=await analyze<Matrix>({action:"validate",matrix:next});
      update(old=>makeDraft({ ...investment, matrix:clean, title:file.name },old));
      setNotice({error:"",success:`Imported ${file.name}`,loading:false});
      setValidated(JSON.stringify(clean));
    } catch(e) { setNotice({error:(e as Error).message,success:"",loading:false}); }
  }
  async function getClean() { return analyze<Matrix>({action:"validate",matrix}); }
  async function exportFile(kind:"csv"|"xlsx") {
    if(exportMenu.current)exportMenu.current.open=false;
    setNotice({error:"",success:"",loading:true});
    try {
      const clean=await getClean();
      if(kind==="csv") {
        const lines=[["Alternative",...clean.states.map(x=>quoted(spreadsheetLabel(x)))].join(","),...clean.values.map((r,i)=>[quoted(spreadsheetLabel(clean.alternatives[i])),...r].join(","))].join("\r\n");
        download(new Blob(["\ufeff",lines],{type:"text/csv;charset=utf-8"}),"decision-matrix.csv");
      } else {
        const {default:write}=await import("write-excel-file/browser");
        const data=[["Alternative",...clean.states],...clean.values.map((r,i)=>[clean.alternatives[i],...r])].map(row=>row.map(x=>typeof x==="number"?{type:Number,value:x}:{type:String,value:String(x)}));
        await write(data).toFile("decision-matrix.xlsx");
      }
      setNotice({error:"",success:`${kind.toUpperCase()} export ready`,loading:false});
    } catch(e) { setNotice({error:(e as Error).message,success:"",loading:false}); }
  }
  async function validate() {
    setNotice({error:"",success:"",loading:true});
    try { await getClean();setValidated(JSON.stringify(matrix));setNotice({error:"",success:"Matrix validated and ready to analyze.",loading:false}); }
    catch(e) { setNotice({error:(e as Error).message,success:"",loading:false}); }
  }
  function startBlank() {
    const next={alternatives:["Alternative 1","Alternative 2"],states:["State 1","State 2"],values:[[0,0],[0,0]],objective:matrix.objective};
    update({matrix:next,probabilities:equal(2),prior:equal(2),evidence:defaultEvidence,likelihoods:defaultLikelihoods(2),known:0,label:"Untitled decision model",probSource:"Illustrative equal weights · replace with your estimates"});
    setNotice({error:"",success:"Started a blank matrix.",loading:false});
  }
  return <div className="stack page-content"><PageHeading kicker="Module II · Problem setup" title="Decision Matrix" ar="بناء مصفوفة القرار" description="Build a payoff matrix to model your alternatives under each possible state of nature." actions={<a className="button secondary" href="#examples"><FileSpreadsheet size={16}/> Load an example</a>}/>
    <section className="panel stack"><PanelTitle title="Payoff matrix" description={draft.label} action={<span className={`save-status ${status}`}><i/>{status==="saved"?"Workspace saved":status==="local"?"Saved on this device":status==="saving"?"Saving…":"Opening workspace…"}</span>}/>
      <div className="matrix-tools"><div className="segmented" role="group" aria-label="Payoff objective"><button type="button" className={matrix.objective==="profit"?"selected":""} aria-pressed={matrix.objective==="profit"} onClick={()=>change(m=>({...m,objective:"profit"}))}>Maximize profit</button><button type="button" className={matrix.objective==="cost"?"selected":""} aria-pressed={matrix.objective==="cost"} onClick={()=>change(m=>({...m,objective:"cost"}))}>Minimize cost</button></div><div className="button-group"><input ref={upload} type="file" accept=".csv,.xlsx" hidden onChange={importFile}/><button className="button secondary compact" onClick={()=>upload.current?.click()}><UploadCloud size={16}/> Import</button><details className="export-menu" ref={exportMenu}><summary className="button secondary compact"><ArrowDownToLine size={16}/> Export <ChevronDown size={13}/></summary><div><button onClick={()=>exportFile("csv")}>Download CSV</button><button onClick={()=>exportFile("xlsx")}>Download Excel (.xlsx)</button></div></details></div></div>
      <div className="table-scroll matrix-wrap"><table className="matrix-edit" aria-label="Editable decision matrix"><thead><tr><th scope="col"><span>Alternatives</span><small>Rows · aᵢ</small></th>{matrix.states.map((s,j)=><th scope="col" key={j}><div className="matrix-cell-header"><input aria-label={`State ${j+1} name`} value={s} maxLength={70} onChange={e=>change(m=>({...m,states:m.states.map((x,k)=>k===j?e.target.value:x)}))}/><button className="icon-button danger" aria-label={`Remove state ${j+1}`} title={`Remove state ${j+1}`} disabled={matrix.states.length<=1} onClick={()=>removeState(j)}><Trash2 size={15}/></button></div><small>e{j+1}</small></th>)}<th className="delete-cell" aria-label="Row actions"/></tr></thead><tbody>{matrix.alternatives.map((name,i)=><tr key={i}><th scope="row"><input aria-label={`Alternative ${i+1} name`} value={name} maxLength={70} onChange={e=>change(m=>({...m,alternatives:m.alternatives.map((x,k)=>k===i?e.target.value:x)}))}/></th>{matrix.values[i].map((v,j)=><td key={j}><input inputMode="decimal" aria-label={`Payoff for alternative ${i+1}, state ${j+1}`} value={editing(v)} maxLength={32} onChange={e=>change(m=>({...m,values:m.values.map((r,k)=>k===i?r.map((x,l)=>l===j?e.target.value:x):r)}))}/></td>)}<td className="delete-cell"><button className="icon-button danger" aria-label={`Remove alternative ${i+1}`} title={`Remove alternative ${i+1}`} disabled={matrix.alternatives.length<=1} onClick={()=>removeRow(i)}><Trash2 size={16}/></button></td></tr>)}</tbody></table></div>
      <div className="matrix-tools"><div className="button-group"><button className="button soft compact" onClick={addRow} disabled={matrix.alternatives.length>=MAX_SIZE}><Plus size={16}/> Add alternative</button><button className="button soft compact" onClick={addState} disabled={matrix.states.length>=MAX_SIZE}><Plus size={16}/> Add state</button></div><button className="button ghost compact" onClick={startBlank}>Start blank</button></div>
      <Feedback error={notice.error} loading={notice.loading} note="Checking the matrix…"/>{notice.success&&<div className="feedback success" role="status"><Check size={17}/>{notice.success}</div>}
      <div className="analysis-footer"><span><Pill tone="neutral">{shape}</Pill> {matrix.alternatives.length} alternatives · {matrix.states.length} states</span><div className="button-group"><button className="button secondary" onClick={validate} disabled={notice.loading}><ShieldCheck size={16}/> {validated===JSON.stringify(matrix)?"Validated":"Validate matrix"}</button><a href="#comparison" className="button primary">Compare criteria <ArrowRight size={16}/></a></div></div>
    </section><section className="panel stack"><PanelTitle title="Mathematical representation" description="Alternatives form the rows. Each column is an external state; each entry is a payoff or cost for that pairing."/><Formula>{String.raw`R=(r_{ij})\in\mathbb{R}^{${matrix.alternatives.length}\times ${matrix.states.length}},\qquad R(a_i,e_j)=r_{ij}`}</Formula><Tip><b>Course notation.</b> The professor writes n for the number of alternatives and m for the number of states; the brief reverses those letters. Both describe the same row–column structure. CSV and Excel files use the first row for state names and the first column for alternative names.</Tip></section>
  </div>;
}