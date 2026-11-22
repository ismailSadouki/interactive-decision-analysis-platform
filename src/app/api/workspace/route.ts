import { eq } from "drizzle-orm";
import { NextResponse } from "next/server";
import { db } from "@/db";
import { workspaces } from "@/db/schema";

export const dynamic = "force-dynamic";
const key = (r: Request) => {
  const value = r.headers.get("x-workspace-key") ?? "";
  return /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value) ? value : null;
};
const json = (payload: object, status = 200) => NextResponse.json(payload, { status, headers: { "Cache-Control": "no-store" } });

export async function GET(request: Request) {
  const id = key(request);
  if (!id) return json({ error: "A workspace key is required." }, 400);
  try {
    const [row] = await db.select({ draft: workspaces.draft }).from(workspaces).where(eq(workspaces.id,id)).limit(1);
    return json({ draft: row?.draft ?? null });
  } catch {
    return json({ error: "Cloud saving is temporarily unavailable." }, 503);
  }
}

export async function PUT(request: Request) {
  const id = key(request);
  if (!id) return json({ error: "A workspace key is required." }, 400);
  if (Number(request.headers.get("content-length")) > 150_000) return json({ error: "The draft is too large." }, 413);
  const text = await request.text();
  if (text.length > 150_000) return json({ error: "The draft is too large." }, 413);
  let draft: Record<string, unknown>;
  try {
    draft = JSON.parse(text);
    if (!draft || typeof draft !== "object" || Array.isArray(draft) || !draft.matrix) throw new Error();
  } catch {
    return json({ error: "Invalid workspace draft." }, 400);
  }
  try {
    await db.insert(workspaces).values({ id,draft }).onConflictDoUpdate({ target: workspaces.id, set: { draft,updatedAt:new Date() } });
    return json({ saved:true });
  } catch {
    return json({ error: "Cloud saving is temporarily unavailable." }, 503);
  }
}
