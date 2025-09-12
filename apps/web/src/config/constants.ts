export const INITIAL_MESSAGE = `
Hi, how can I help you?
`;

export const defaultVectorStore = {
  id: "",
  name: "Example",
};

export const DEVELOPER_PROMPT = `
You are a helpful assistant helping users with their queries.

You're main job is to help the find financials about a company.

The current year is 2025.

If anyone asks about year over year financials, use 2023 to 2024 growth.

You have access to many financial reports in the tools. Include any referenced sources in your tool requests.

`;

export function getDeveloperPrompt(): string {
  const now = new Date();
  const dayName = now.toLocaleDateString("en-US", { weekday: "long" });
  const monthName = now.toLocaleDateString("en-US", { month: "long" });
  const year = now.getFullYear();
  const dayOfMonth = now.getDate();
  return `${DEVELOPER_PROMPT.trim()}\n\nToday is ${dayName}, ${monthName} ${dayOfMonth}, ${year}.`;
}
