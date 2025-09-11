import { z } from "zod";

export const diceParams = z.object({
  sides: z.number().int().min(2),
});

export type DiceParams = z.infer<typeof diceParams>;

export async function roll_dice({ sides }: DiceParams) {
  const value = 1 + Math.floor(Math.random() * sides);
  return {
    content: [{ type: "text", text: `🎲 You rolled a ${value}!` }],
  };
}
