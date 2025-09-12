Databook Ingestion + Query System

This project ingests messy Excel databooks into a structured SQLite database and exposes them through a Next.js chatbot. The goal is to let an LLM answer questions like:
• “What was gross profit margin % over the last 3 years?”
• “How does Adjusted EBITDA compare to Reported EBITDA, based on QoE adjustments?”

Approach
• Ingestion (Python):
• Detects table blocks in Excel sheets, accounting for broken rows, in row unit definitions, and horrid formatting
• Normalizes column headers, collapsing year-end datetimes (e.g. 2022-12-31 0:00:00) to years when they form a confirmed sequence.
• Extracts facts with row/column headers, units (USD, %), and source file, sheet, and cell for full traceability.
• Normalization:
• Fuzzy-maps financial KPIs (e.g., “Net Sales”, “Adjusted EBITDA”, “Working Capital”) to canonical values.
• Stores both raw facts and pre-computed known values for faster and more accurate queries
• Storage:
• SQLite database committed with the repo for portability and easy local use.
• Query Layer (Next.js / TypeScript):
• value_fetch tool tries known KPIs first, falls back to fuzzy row/col searches.

Assumptions
• There is no manual altering or cleanup of the documents before ingestion
• Conflicting results across databooks are resolved by prioritizing Databook_One_SANITIZED.xlsx
• No sheets or files have the same name.
• Storage is cheap, and we prefer to duplicate. This is not a storage efficient solution. SQLite is in place for ease of dev/test. Snowflake would be a good candidate for storage here.

How to Run

    The project is available at

    1.	Ingest the databooks
    under `apps/data` activate the python env and run script.
    ```
    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m databook_ingest.run
    ```
    2. Inspect `databooks.sqlite` in the tool of your choice.
    3. Drag `databooks.sqlite` into `apps/web/db`
    4. Run the local Nest.js app `npm install` `npm run dev`
