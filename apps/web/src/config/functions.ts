export const roll_dice = async ({ sides }: { sides: number }) => {
  const res = await fetch(`/api/functions/roll_dice?sides=${sides}`).then((res) => res.json());
  return res;
};

export const functionsMap = {
  roll_dice: roll_dice,
};
