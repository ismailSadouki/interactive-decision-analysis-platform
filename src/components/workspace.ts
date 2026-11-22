"use client";

import { useCallback, useEffect, useState } from "react";
import { analyze, type Draft, initialDraft, type Update } from "./model";

const localDraft = "decisionlab-draft-v1";
const localKey = "decisionlab-workspace-key-v1";
const goodDraft = (x: unknown): x is Draft => {
  if (!x || typeof x !== "object") return false;
  const d = x as Partial<Draft>;
  return !!d.matrix && Array.isArray(d.matrix.states) && Array.isArray(d.matrix.values) &&
    Array.isArray(d.probabilities) && !!d.tree && Array.isArray(d.tree.nodes) && Array.isArray(d.prior) && Array.isArray(d.evidence) && Array.isArray(d.likelihoods);
};
function generateKey() {
  if (crypto.randomUUID) return crypto.randomUUID();
  const a = crypto.getRandomValues(new Uint8Array(16));
  a[6]=(a[6]&15)|64; a[8]=(a[8]&63)|128;
  const hex=Array.from(a,b=>b.toString(16).padStart(2,"0")).join("");
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}

export type SaveState = "loading"|"saving"|"saved"|"local";
export function useWorkspace() {
  const [draft,setDraft]=useState<Draft>(initialDraft);
  const [browserKey,setBrowserKey]=useState<string|null>(null);
  const [ready,setReady]=useState(false);
  const [saved,setSaved]=useState<string|null>(null);
  const [localOnly,setLocalOnly]=useState(false);
  useEffect(()=>{
    let active=true;
    async function restore() {
      try {
        const key=localStorage.getItem(localKey) || generateKey();
        localStorage.setItem(localKey,key);
        if (!active) return;
        setBrowserKey(key);
        const raw=localStorage.getItem(localDraft);
        if (raw) {
          const data=JSON.parse(raw);
          if (goodDraft(data)) { setDraft(data); setReady(true); return; }
        }
        const res=await fetch("/api/workspace",{headers:{"x-workspace-key":key},cache:"no-store",signal:AbortSignal.timeout(2500)});
        if (res.ok && active) {
          const {draft:data}=await res.json();
          if (goodDraft(data) && active) { setDraft(data); setSaved(JSON.stringify(data)); }
        }
      } catch { if (active) setLocalOnly(true); }
      finally { if (active) setReady(true); }
    }
    void restore();
    return ()=>{active=false;};
  },[]);
  const json=JSON.stringify(draft);
  useEffect(()=>{
    if (!ready) return;
    try { localStorage.setItem(localDraft,json); } catch { /* Storage may be disabled. */ }
    if (!browserKey || json===saved) return;
    let active=true;
    const controller=new AbortController();
    const timer=setTimeout(async()=>{
      try {
        const res=await fetch("/api/workspace",{method:"PUT",headers:{"Content-Type":"application/json","x-workspace-key":browserKey},body:json,signal:controller.signal});
        if (!active) return;
        if (res.ok) { setSaved(json); setLocalOnly(false); }
        else setLocalOnly(true);
      } catch { if (active) setLocalOnly(true); }
    },450);
    return ()=>{active=false;clearTimeout(timer);controller.abort();};
  },[ready,browserKey,json,saved]);
  const update: Update=useCallback(next=>setDraft(old=>({...old,...(typeof next === "function" ? next(old):next)})),[]);
  const status:SaveState=!ready?"loading":localOnly?"local":saved===json?"saved":"saving";
  return {draft,update,status,ready};
}

export function useAnalysis<T>(payload:object|null, delay=125) {
  const key=payload ? JSON.stringify(payload) : "";
  const [state,setState]=useState<{key:string;data?:T;error?:string}>({key:""});
  useEffect(()=>{
    if (!key) return;
    const controller=new AbortController();
    const timeout=setTimeout(()=>{
      analyze<T>(JSON.parse(key),controller.signal).then(data=>{
        if (!controller.signal.aborted) setState({key,data});
      }).catch((e:Error)=>{
        if (!controller.signal.aborted) setState({key,error:e.message});
      });
    },delay);
    return ()=>{clearTimeout(timeout);controller.abort();};
  },[key,delay]);
  return {data:state.key===key?state.data:undefined,error:state.key===key?state.error:undefined,loading:!!key&&state.key!==key};
}
