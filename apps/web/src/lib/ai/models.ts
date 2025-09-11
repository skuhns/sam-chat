export const DEFAULT_CHAT_MODEL: string = "gpt-4.1-nano";

export interface ChatModel {
  id: ChatModelIds;
  name: string;
  description: string;
}

export type ChatModelIds = "gpt-4.1-nano" | "gpt-4.1";

export const chatModels: Array<ChatModel> = [
  {
    id: "gpt-4.1-nano",
    name: "GPT 4.1 Nano",
    description: "Cheap model to keep my costs low, for guest users",
  },
  {
    id: "gpt-4.1",
    name: "GPT 4.1",
    description: "For admin use in case I need to actually use this",
  },
];
