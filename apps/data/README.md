Databook Ingest

This project ingests messy Excel “databooks” (financial statements, P&L sheets, etc.) into a normalized SQLite database so the data can be queried consistently.

It was designed for interview purposes, but the approach is production-inspired: we preserve lineage, handle odd formatting, and keep the pipeline modular.

⸻

How it works

Parsing strategy: 1. Load sheets as raw text
We don’t let Pandas guess headers — every cell comes in as a string. This ensures we don’t lose blanks, #N/A, or special formatting. 2. Segment into tables
• Scan for non-empty row blocks, then within them detect non-empty column blocks.
• Trim empty borders.
• Each detected rectangle is treated as a candidate table. 3. Header inference
• Identify header rows and columns by checking if most cells are text (vs. numeric).
• Build “header paths” by concatenating multi-row/col headers so each data cell can be labeled. 4. Units & scales
• Look at the top-left of the table for hints like "$ in thousands", "millions", "%".
• Allow inline overrides: if a unit marker appears inside the header, everything beneath/to the right adopts that scale.
• Store both the raw text and the normalized numeric value (value_real). 5. Table naming
• If the first row of a table has only one text cell, we treat it as the table name.
• Otherwise, check the cell above the table’s top-left, or fall back to a generic sheet heading. 6. Value parsing
• Handle parentheses as negatives, commas, percents, dashes as missing, and Excel error codes.
• Store both the parsed number and a parse_status (ok, blank, error_code, dash, non_numeric). 7. Write to SQLite
Each fact becomes a row with:
• lineage (file, sheet, row_idx, col_idx),
• labels (row_header, col_header, inferred_table_name),
• units & scale,
• raw text and parsed value.
