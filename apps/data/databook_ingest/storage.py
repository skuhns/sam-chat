import sqlite3

from .value_matching import best_known_value, parse_known_period
from .source_matching import best_known_sheet

from .utils import ensure_dirs

FACTS_TABLE = "facts"
KPI_FACTS_TABLE = "kpi_facts"
SOURCE_FACTS_TABLE = "known_sources"


# ---------- SQLITE ----------
def init_sqlite(db_path: str) -> sqlite3.Connection:
    ensure_dirs(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {FACTS_TABLE} (
            fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file TEXT,
            sheet TEXT,
            table_r0 INTEGER,
            table_c0 INTEGER,
            row_idx INTEGER,
            col_idx INTEGER,
            row_header TEXT,
            col_header TEXT,
            raw_text TEXT,
            unit TEXT,
            scale REAL,
            value_real REAL,
            parse_status TEXT,
            inferred_table_name TEXT
        );
        """
    )
    cur.execute(f"CREATE INDEX IF NOT EXISTS ix_{FACTS_TABLE}_sheet ON {FACTS_TABLE}(sheet);")
    cur.execute(f"CREATE INDEX IF NOT EXISTS ix_{FACTS_TABLE}_headers ON {FACTS_TABLE}(row_header, col_header);")
    cur.execute(f"CREATE INDEX IF NOT EXISTS ix_{FACTS_TABLE}_pos ON {FACTS_TABLE}(row_idx, col_idx);")

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {KPI_FACTS_TABLE} (
            known_fact_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            fact_id           INTEGER NOT NULL,
            known_value       TEXT NOT NULL,
            known_period      TEXT,            -- YYYY or ISO date YYYY-MM-DD
            match_score       REAL,            -- 0..100 (rapidfuzz score)
            match_rule        TEXT,            -- notes (e.g., 'percent_gate', 'unitless')
            created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(fact_id) REFERENCES facts(fact_id) ON DELETE CASCADE
        );
    """)
    cur.execute(f"CREATE INDEX IF NOT EXISTS ix_{KPI_FACTS_TABLE}_lookup ON {KPI_FACTS_TABLE}(known_value, known_period);")
    cur.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS ux_{KPI_FACTS_TABLE}_fact ON {KPI_FACTS_TABLE}(fact_id);")

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {SOURCE_FACTS_TABLE} (
            known_sheet_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            file            TEXT NOT NULL,
            sheet           TEXT NOT NULL,     -- raw sheet name from workbook
            known_sheet     TEXT NOT NULL,     -- canonical, e.g., 'P&L Statement'
            match_score     REAL,              -- 0..100 rapidfuzz score
            match_rule      TEXT,              -- notes (e.g., 'synonym_gate')
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS ux_{SOURCE_FACTS_TABLE}_file_sheet ON {SOURCE_FACTS_TABLE}(file, sheet);")
    cur.execute(f"CREATE INDEX IF NOT EXISTS ix_{SOURCE_FACTS_TABLE}_known ON {SOURCE_FACTS_TABLE}(known_sheet);")
    
    conn.commit()
    return conn

def insert_facts(conn, facts):
    if not facts:
        print("insert_facts: no facts to insert")
        return

    required = {"file","sheet","table_r0","table_c0","row_idx","col_idx",
                "row_header","col_header","raw_text","unit","scale","value_real"}
    missing = required - set(facts[0].keys())
    if missing:
        print(f"insert_facts: missing keys in fact rows: {missing}")
        # You can raise here if you prefer:
        # raise KeyError(f"Missing keys: {missing}")

    cur = conn.cursor()
    rows = [
        (
            f["file"], f["sheet"], f["table_r0"], f["table_c0"], f["row_idx"], f["col_idx"],
            f["row_header"], f["col_header"], f["raw_text"], f["unit"], f["scale"], f["value_real"],
            f["parse_status"], f["inferred_table_name"]
        )
        for f in facts
    ]

    cur.executemany(
        f"""INSERT INTO {FACTS_TABLE} (
            file, sheet, table_r0, table_c0, row_idx, col_idx,
            row_header, col_header, raw_text, unit, scale, value_real,
            parse_status, inferred_table_name
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    print(f"Inserted {len(facts)} facts into DB")

def populate_known_facts(conn: sqlite3.Connection, score_threshold: int = 83) -> int:
    """
    For any fact not yet present in known_facts, attempt to map (row_header, unit, col_header)
    to (known_value, known_period). Insert rows with match_score >= threshold.
    Returns number of rows inserted.
    """
    cur = conn.cursor()
    cur.execute(f"""
        SELECT f.fact_id, f.row_header, f.col_header, f.unit
        FROM facts f
        LEFT JOIN {KPI_FACTS_TABLE} k ON k.fact_id = f.fact_id
        WHERE k.fact_id IS NULL
    """)
    rows = cur.fetchall()

    inserts = []
    for fact_id, row_header, col_header, unit in rows:
        canon, score, rule = best_known_value(row_header or "", unit or "")
        if canon and score >= score_threshold:
            period = parse_known_period(col_header or "")
            inserts.append((fact_id, canon, period, float(score), rule))

    if inserts:
        cur.executemany(f"""
            INSERT INTO {KPI_FACTS_TABLE} (fact_id, known_value, known_period, match_score, match_rule)
            VALUES (?,?,?,?,?)
        """, inserts)
        conn.commit()
    return len(inserts)

def populate_known_sheets(conn: sqlite3.Connection, score_threshold: int = 88) -> int:
    """
    For each distinct (file, sheet) in facts not yet mapped, add a row to known_sheets.
    """
    cur = conn.cursor()
    cur.execute(f"""
        SELECT f.file, f.sheet
        FROM {FACTS_TABLE} f
        LEFT JOIN {SOURCE_FACTS_TABLE} ks ON ks.file = f.file AND ks.sheet = f.sheet
        GROUP BY f.file, f.sheet
        HAVING ks.file IS NULL
    """)
    rows = cur.fetchall()

    inserts = []
    for file, sheet in rows:
        canon, score, rule = best_known_sheet(sheet or "", threshold=score_threshold)
        if canon:
            inserts.append((file, sheet, canon, float(score), rule))
    if inserts:
        cur.executemany(f"""
            INSERT INTO {SOURCE_FACTS_TABLE} (file, sheet, known_sheet, match_score, match_rule)
            VALUES (?, ?, ?, ?, ?)
        """, inserts)
        conn.commit()
    return len(inserts)