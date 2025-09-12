export const toolsList = [
  {
    name: "roll_dice",
    description: "Roll a dice of the given amount of sides.",
    parameters: {
      sides: {
        type: "number",
        description: "The number of sides on the dice",
      },
    },
  },
  {
    name: "value_fetch",
    description:
      "Fetch the value of one or more financial metrics, assume the total value, unless given a period of time. A source document or report can be provided, Fetch KPI values such as (Reported/Adjusted EBITDA, margins, revenue, working capital, QoE adjustments, etc.) from the local SQLite databook. Always call this when the user asks for numeric results. The database is already available—do not ask for documents.",
    parameters: {
      values: {
        type: "array",
        items: { type: "string" },
        description:
          "One or more metrics mentioned by the user to fetch (e.g., 'Net Sales', 'Adjusted EBITDA %').",
      },
      source: {
        type: "string",
        description:
          "Optional sheet or source hint to narrow the search (e.g., 'P&L Statement', 'Quality of Earnings'). Include only if explicitly given by user",
      },
      periods: {
        type: "array",
        items: { type: "string" },
        description:
          "Periods to fetch for, in 'YYYY' or 'YYYY-MM-DD' format (e.g., ['2022'] or ['2022-12-31']). Could be a range of years eg (['2022', '2023']). Include only if explicitly given or inferred by user",
      },
      unit: {
        type: "string",
        description:
          "The unit of measure for the data points. Either 'USD' or '%' based on what the user asks for",
      },
    },
  },
];
