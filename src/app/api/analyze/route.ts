import { spawn } from "node:child_process";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function evaluate(input: string): Promise<{ data?: unknown; error?: string }> {
  return new Promise((resolve, reject) => {
    // The Python module and fixture paths are explicitly included in next.config.ts.
    const child = spawn(/*turbopackIgnore: true*/ process.env.DECISION_PYTHON || "python3", ["-m", "decision_engine.api"], {
      cwd: process.cwd(),
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1", OPENBLAS_NUM_THREADS: "1" },
      stdio: ["pipe", "pipe", "pipe"],
    });
    let output = "", errors = "";
    const timer = setTimeout(() => { child.kill(); reject(new Error("Decision engine timed out")); }, 12_000);
    child.stdout.setEncoding("utf-8").on("data", (text: string) => { output += text; if (output.length > 2_500_000) child.kill(); });
    child.stderr.setEncoding("utf-8").on("data", (text: string) => { errors = (errors + text).slice(-1500); });
    child.stdin.on("error", () => { /* A prematurely closed process is handled below. */ });
    child.on("error", (err) => { clearTimeout(timer); reject(err); });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (code !== 0) { reject(new Error(errors || "Decision engine unavailable")); return; }
      try { resolve(JSON.parse(output)); } catch (e) { reject(e); }
    });
    child.stdin.end(input);
  });
}

export async function POST(request: Request) {
  if (Number(request.headers.get("content-length")) > 150_000) {
    return NextResponse.json({ error: "This model exceeds the request size limit." }, { status: 413 });
  }
  try {
    const input = await request.text();
    if (input.length > 150_000) return NextResponse.json({ error: "This model exceeds the request size limit." }, { status: 413 });
    const result = await evaluate(input);
    return NextResponse.json(result, { status: result.error ? 422 : 200 });
  } catch (error) {
    console.error("Decision engine request failed", error);
    return NextResponse.json({ error: "The analysis engine is temporarily unavailable. Try again." }, { status: 503 });
  }
}
