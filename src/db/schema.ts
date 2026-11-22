import { jsonb, pgTable, timestamp, uuid } from "drizzle-orm/pg-core";

export const workspaces = pgTable("decision_workspaces", {
  id: uuid("id").primaryKey(),
  draft: jsonb("draft").$type<Record<string, unknown>>().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});
