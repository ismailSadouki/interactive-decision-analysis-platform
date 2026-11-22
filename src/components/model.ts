import rawProblems from "../../examples/problems.json";

export type Input = string | number;
export type Objective = "profit" | "cost";
export type Direction = "max" | "min";
export type Matrix = { alternatives: string[]; states: string[]; values: Input[][]; objective: Objective };
export type Evaluation = { key:string; label:string; arabic:string; direction:Direction; formula:string; interpretation:string; scores:number[]; steps:string[]; winners:number[]; best:number };
export type Uncertainty = { alpha:number; criteria:Evaluation[]; bestByState:number[]; regret:number[][]; lines:{best:number; worst:number; intercept:number; slope:number; interval:[number,number]|null; comparisons:string[]}[] };
export type Risk = { probabilities:number[]; emv:Evaluation; eol:Evaluation; regret:number[][]; bestByState:number[]; variance:number[]; std:number[]; varianceSteps:string[]; perfect:number; evpi:number; perfectStep:string; evpiStep:string; evpiFormula:string; price:number; buy:boolean };
export type Observation = { name:string; probability:number; joint:number[]; marginalStep:string; posterior:number[]|null; posteriorSteps:string[]; emv:Evaluation|null };
export type Bayesian = { prior:number[]; observations:Observation[]; likelihoods:number[][]; baseline:Evaluation; sample:number; perfect:number; evsi:number; evpi:number; sampleStep:string; perfectStep:string; evsiStep:string; evpiStep:string; price:number; net:number; buy:boolean };
export type NodeType = "decision" | "chance" | "terminal";
export type Branch = { to:string; label:string; immediate:Input; probability?:Input };
export type TreeNode = { id:string; name:string; type:NodeType; branches?:Branch[]; payoff?:Input };
export type Tree = { root:string; nodes:TreeNode[] };
export type SolvedBranch = Branch & { immediate:number; probability?:number; childValue:number; total:number };
export type SolvedNode = Omit<TreeNode,"branches"> & { branches:SolvedBranch[]; value:number; step:string; chosen:number[] };
export type SolvedTree = { root:string; objective:Objective; direction:Direction; value:number; policy:{source:string;target:string}[]; nodes:SolvedNode[]; evaluationOrder:string[] };
export type Staffing = { demands:number[]; starts:number[]; coverage:number[]; total:number; printed:number[]; printedAlternating:number[] };
export type Mode = "assignment"|"staffing"|"certainty"|"uncertainty"|"risk"|"poisson"|"tree"|"bayes";
export type Problem = { id:string; title:string; arabic:string; group:string; mode:Mode; course?:number; icon:string; summary:string; task:string; matrix?:Matrix; probabilities?:number[]; state?:number; alpha?:number; criterion?:string; evidence?:string[]; likelihoods?:number[][]; samplePrice?:number; tree?:Tree; times?:Input[][] | Matrix; demands?:Input[]; rate?:Input; cutoff?:Input; upfront?:Input; replacement?:Input; summands?:number[][]; raw?:number[]; mass?:number; omitted?:number; answerChoices?:string[]; correct?:boolean; solution?:Evaluation|Uncertainty|Risk|Bayesian|SolvedTree|Staffing };
export type Draft = { matrix:Matrix; probabilities:Input[]; probSource:string; known:number; alpha:number; price:Input; evidence:string[]; likelihoods:Input[][]; prior:Input[]; samplePrice:Input; tree:Tree; treeObjective:Objective; label:string };
export type Navigation = "dashboard"|"concepts"|"matrix"|"certainty"|"uncertainty"|"risk"|"trees"|"bayes"|"comparison"|"examples"|"reference";
export type Update = (next: Partial<Draft> | ((old: Draft) => Partial<Draft>)) => void;

export const problems = rawProblems as Problem[];
export const investment = problems.find(p => p.id === "investment")!;
export const expansion = problems.find(p => p.id === "expansion")!;
export const diagnostic = problems.find(p => p.id === "diagnostic")!;

export const MAX_SIZE = 24;
export const defaultEvidence = ["Positive signal", "Negative signal"];
export const defaultLikelihoods = (length:number) => [Array<number>(length).fill(.7), Array<number>(length).fill(.3)];
export const equal = (length:number) => Array<number>(length).fill(1/length);
export const format = (value:Input|null|undefined, decimals=4) => {
  if (typeof value !== "number") return value === null || value === undefined || value === "" ? "—" : value;
  if (value && (Math.abs(value) >= 1e10 || Math.abs(value) < 10**(-decimals))) return value.toExponential(3);
  return new Intl.NumberFormat("en-US",{maximumFractionDigits:decimals}).format(value);
};
export const editing = (x:Input|undefined) => x === undefined ? "" : typeof x === "number" ? String(x) : x;
export const parseNumber = (x:Input) => typeof x === "number" ? x : x.trim() === "" ? NaN : Number(x.trim().replace("−","-").replace("٫","."));

export function makeDraft(problem:Problem, old?:Draft): Draft {
  const matrix = problem.matrix ?? investment.matrix!;
  const n = matrix.states.length;
  const probabilities = problem.probabilities ?? equal(n);
  return {
    matrix, probabilities, known:problem.state ?? 0, alpha:problem.alpha ?? .5, price:0,
    probSource:problem.probabilities ? "Provided by the loaded example" : "Illustrative equal weights · replace with your estimates",
    evidence:problem.evidence ?? defaultEvidence, likelihoods:problem.likelihoods ?? defaultLikelihoods(n), prior:probabilities,
    samplePrice:problem.samplePrice ?? 0, tree:problem.tree ?? old?.tree ?? expansion.tree!,
    treeObjective:problem.tree ? matrix.objective : old?.treeObjective ?? "profit", label:problem.title,
  };
}
export const initialDraft = makeDraft(investment);

export async function analyze<T>(payload:object, signal?:AbortSignal):Promise<T> {
  const response = await fetch("/api/analyze", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload),signal});
  const result = await response.json();
  if (!response.ok || result.error) throw new Error(result.error || "The analysis could not be completed.");
  return result.data as T;
}

export function download(content:Blob, name:string) {
  const url=URL.createObjectURL(content);
  const link=document.createElement("a");
  link.href=url; link.download=name; link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}

export const CATEGORIES = [
  { number:"I", name:"Decision concepts", arabic:"مفهوم القرار", status:"Course" },
  { number:"II", name:"Decision criteria", arabic:"معايير اتخاذ القرار", status:"Course" },
  { number:"III", name:"Decision trees", arabic:"شجرة القرار", status:"Extension" },
  { number:"IV", name:"Bayesian analysis", arabic:"التحليل البايزي", status:"Extension" },
] as const;
