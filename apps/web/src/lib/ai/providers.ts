import { customProvider, extractReasoningMiddleware, wrapLanguageModel } from "ai";
import { gateway } from "@ai-sdk/gateway";

export const myProvider = customProvider({
  languageModels: {
    "chat-model": gateway.languageModel("xai/grok-2-vision-1212"),
    "chat-model-reasoning": wrapLanguageModel({
      model: gateway.languageModel("xai/grok-3-mini"),
      middleware: extractReasoningMiddleware({ tagName: "think" }),
    }),
    "title-model": gateway.languageModel("xai/grok-2-1212"),
    "artifact-model": gateway.languageModel("xai/grok-2-1212"),
  },
});
