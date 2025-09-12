import { z } from "zod";
export const runtime = "nodejs";
import path from "path";
import Database from "better-sqlite3";
import { FACTS_TABLE, KNOWN_FACTS_TABLE, KNOWN_VALUES } from "./constants";

type QueryParams = {
  dbPath: string;
  value: string;
  period?: string;
  unit?: string;
};

export type KnownFactRow = {
  fact_id: number;
  file: string;
  sheet: string;
  row_header: string;
  col_header: string;
  unit: string | null;
  value_real: number | null;
  known_value: string;
  known_period: string | null;
};

export type FactRow = {
  fact_id: number;
  file: string;
  sheet: string;
  row_header: string;
  col_header: string;
  unit: string | null;
  value_real: number | null;
  raw_text: string | null;
};

export const fetchParams = z.object({
  values: z.array(z.string()),
  source: z.string().optional(),
  periods: z.array(z.string()).optional(),
  unit: z.union([z.literal("USD"), z.literal("%")]).optional(),
});

// ---------------- fuzzy matching helpers ----------------
const norm = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z0-9% ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();

function jaccardTokens(a: string, b: string): number {
  const A = new Set(norm(a).split(" ").filter(Boolean));
  const B = new Set(norm(b).split(" ").filter(Boolean));
  if (A.size === 0 || B.size === 0) return 0;
  let inter = 0;
  for (const t of A) if (B.has(t)) inter++;
  const union = A.size + B.size - inter;
  return inter / union;
}

function fuzzyMatchKnown(value: string, threshold = 0.6): { canonical?: string; score: number } {
  const vnorm = norm(value);
  let best: { canonical?: string; score: number } = { score: 0 };

  for (const [canonical, alts] of Object.entries(KNOWN_VALUES)) {
    // compare against canonical and each alias
    const candidates = [canonical, ...alts];
    for (const cand of candidates) {
      const cnorm = norm(cand);
      let s = jaccardTokens(vnorm, cnorm);
      // substring bonus (helps "revenue growth" ~ "revenue")
      if (vnorm.includes(cnorm) || cnorm.includes(vnorm)) s += 0.2;
      if (cnorm.includes("%") === vnorm.includes("%")) s += 0.05; // tiny unit-shape nudge
      if (s > best.score) best = { canonical, score: s };
    }
  }
  return best.score >= threshold ? best : { score: best.score }; // only return canonical if above threshold
}
const DB_PATH = path.join(process.cwd(), "db", "databook.sqlite");
const isYear = (s?: string) => !!s && /^\d{4}$/.test(s);

const PREFERRED_FILES = ["Databook_One_SANITIZED.xlsx"]; // highest priority first

function dedupeByPeriodPreferFile<T extends { col_header: string; file: string }>(
  rows: T[],
  preferredFiles: string[] = PREFERRED_FILES,
): T[] {
  const rank = new Map(preferredFiles.map((f, i) => [f, i]));
  const bestByPeriod = new Map<string, T>();

  for (const r of rows) {
    const key = r.col_header ?? ""; // period label
    const current = bestByPeriod.get(key);
    if (!current) {
      bestByPeriod.set(key, r);
      continue;
    }
    const curRank = rank.has(current.file)
      ? (rank.get(current.file) as number)
      : Number.POSITIVE_INFINITY;
    const newRank = rank.has(r.file) ? (rank.get(r.file) as number) : Number.POSITIVE_INFINITY;

    // prefer lower rank (i.e., earlier in PREFERRED_FILES). If equal, keep the first seen.
    if (newRank < curRank) {
      bestByPeriod.set(key, r);
    }
  }
  return Array.from(bestByPeriod.values());
}
// ---------------- route ----------------
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);

    const values = searchParams.getAll("values");
    const source = searchParams.get("source") || undefined;
    const periods = searchParams.getAll("periods") || [];
    const unit = (searchParams.get("unit") || undefined) as "USD" | "%" | undefined;

    const parsed = fetchParams.safeParse({ values, source, periods, unit });
    if (!parsed.success) {
      return new Response(
        JSON.stringify({ error: "Invalid parameters", issues: parsed.error.issues }),
        { status: 400 },
      );
    }

    const safeValues = parsed.data.values.filter(Boolean);
    const safePeriods = parsed.data.periods ?? [];

    let result: Array<{
      queryValue: string;
      period?: string;
      periodLabel: string;
      value: number | null;
    }> = [];

    if (safeValues.length === 0) {
      return new Response(JSON.stringify({ results: [] }), { status: 200 });
    }

    // For each input value, try known_facts first (via fuzzy canonical); if none, fall back to free-text facts
    const queryPairs =
      safePeriods.length > 0
        ? safeValues.flatMap((v) => safePeriods.map((p) => ({ v, p })))
        : safeValues.map((v) => ({ v, p: undefined as string | undefined }));

    for (const { v, p } of queryPairs) {
      // 1) try fuzzy → canonical → known_facts
      const { canonical } = fuzzyMatchKnown(v);
      let rows: (KnownFactRow | FactRow)[] = [];

      if (canonical) {
        const krows = fetchKnownValue({ dbPath: DB_PATH, value: canonical, period: p });
        if (krows.length > 0) {
          rows = krows;
        }
      }

      // 2) fallback to free-text facts when no known rows
      if (rows.length === 0) {
        rows = fetchFact({ dbPath: DB_PATH, value: v, period: p, unit });
      }

      const pruned = dedupeByPeriodPreferFile(rows);

      // shape the output (simple: period + value)
      for (const r of pruned) {
        result.push({
          queryValue: v,
          period: p,
          periodLabel: r.col_header,
          value: r.value_real,
        });
      }
    }

    return new Response(JSON.stringify({ results: result }), { status: 200 });
  } catch (error) {
    console.error("Error in value_fetch:", error);
    return new Response(JSON.stringify({ error: "Error fetching value" }), { status: 500 });
  }
}

// ---------------- DB helpers ----------------
export function fetchFact({ dbPath, value, period, unit }: QueryParams): FactRow[] {
  const db = new Database(dbPath, { readonly: true, fileMustExist: true });

  let sql = `
    SELECT f.fact_id, f.file, f.sheet, f.row_header, f.col_header,
           f.unit, f.value_real, f.raw_text
    FROM ${FACTS_TABLE} f
    LEFT JOIN ${KNOWN_FACTS_TABLE} kf ON kf.fact_id = f.fact_id
    WHERE (LOWER(f.row_header) LIKE ? OR LOWER(f.col_header) LIKE ?)
  `;
  const params: any[] = [`%${value.toLowerCase()}%`, `%${value.toLowerCase()}%`];

  if (period) {
    if (isYear(period)) {
      // exact year only; explicitly exclude date-like strings
      sql += " AND f.col_header = ? AND f.col_header NOT LIKE (? || '-%')";
      params.push(period, period);
    } else {
      // full date (or other exact label)
      sql += " AND f.col_header = ?";
      params.push(period);
    }
  }

  if (unit === "USD") {
    sql += " AND f.unit = 'USD'";
  } else if (unit === "%") {
    sql += " AND f.unit = '%'";
  }

  const stmt = db.prepare(sql);
  const rows = stmt.all(...params) as FactRow[];
  db.close();
  return rows;
}

export function fetchKnownValue({ dbPath, value, period }: QueryParams): KnownFactRow[] {
  const db = new Database(dbPath, { readonly: true, fileMustExist: true });

  let sql = `
    SELECT f.fact_id, f.file, f.sheet, f.row_header, f.col_header,
           f.unit, f.value_real,
           kf.known_value, kf.known_period
    FROM ${FACTS_TABLE} f
    JOIN ${KNOWN_FACTS_TABLE} kf ON kf.fact_id = f.fact_id
    WHERE kf.known_value = ?
  `;
  const params: any[] = [value];

  if (period) {
    if (isYear(period)) {
      // exact year only; explicitly exclude date-like strings
      sql += " AND f.col_header = ? AND f.col_header NOT LIKE (? || '-%')";
      params.push(period, period);
    } else {
      // full date (or other exact label)
      sql += " AND f.col_header = ?";
      params.push(period);
    }
  }

  const stmt = db.prepare(sql);
  const rows = stmt.all(...params) as KnownFactRow[];
  db.close();
  return rows;
}
