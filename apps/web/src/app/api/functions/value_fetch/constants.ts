export const FACTS_TABLE = "facts";
export const KNOWN_FACTS_TABLE = "kpi_facts";

export type UNIT = "USD" | "%";
export const KNOWN_VALUES: Record<string, string[]> = {
  "Reported EBITDA": [
    "reported ebitda",
    "ebitda (reported)",
    "ebitda - reported",
    "ebitda reported",
  ],
  "Reported EBITDA %": [
    "reported ebitda %",
    "ebitda margin",
    "ebitda %",
    "ebitda % of sales",
    "ebitda percentage",
  ],
  "Net Sales": ["net sales", "sales", "revenue", "net revenues", "total revenue", "net turnover"],
  "Gross Profit": [
    "gross profit",
    "gross income",
    "gross earnings",
    "profit (gross)",
    "gross result",
  ],
  "Net Profit": [
    "net profit",
    "net income",
    "net earnings",
    "earnings",
    "profit after tax",
    "pat",
    "profit (net)",
  ],
  "Gross Margin": [
    "gross margin",
    "gross margin %",
    "gross profit %",
    "gm%",
    "gross margin percent",
    "gross profit margin",
  ],
  "Operating Expense %": [
    "operating expense %",
    "opex %",
    "operating expenses as % of sales",
    "opex ratio",
    "operating expense percentage",
  ],
  "Adjusted EBITDA": [
    "adjusted ebitda",
    "ebitda (adj.)",
    "ebitda adjusted",
    "normalized ebitda",
    "adj. ebitda",
  ],
  "Adjusted EBITDA %": [
    "adjusted ebitda %",
    "adj. ebitda %",
    "adjusted ebitda margin",
    "adj. ebitda margin",
    "adjusted ebitda percentage",
  ],
  "Total Adjustments": [
    "total adjustments",
    "adjustments",
    "ebitda adjustments",
    "total adj.",
    "sum of adjustments",
  ],
  "Adjusted Working Capital": [
    "adjusted working capital",
    "adj. working capital",
    "working capital (adj.)",
    "working capital adjusted",
  ],
  "Reported Working Capital": [
    "reported working capital",
    "working capital",
    "reported wc",
    "wc reported",
    "net working capital",
  ],
};
