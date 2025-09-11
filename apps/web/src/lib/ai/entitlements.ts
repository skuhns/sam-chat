import type { ChatModel } from "./models";

interface Entitlements {
  maxMessagesPerDay: number;
  availableChatModelIds: Array<ChatModel["id"]>;
}

//TODO - move if I ever do real auth
type UserType = "guest" | "admin";

export const entitlementsByUserType: Record<UserType, Entitlements> = {
  guest: {
    maxMessagesPerDay: 20,
    availableChatModelIds: ["gpt-4.1-nano"],
  },
  admin: {
    maxMessagesPerDay: 100,
    availableChatModelIds: ["gpt-4.1-nano", "gpt-4.1"],
  },
};
