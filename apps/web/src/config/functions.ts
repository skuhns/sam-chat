export const roll_dice = async ({ sides }: { sides: number }) => {
  const res = await fetch(`/api/functions/roll_dice?sides=${sides}`).then((res) => res.json());
  return res;
};

export const value_fetch = async ({
  values,
  source,
  periods,
  unit,
}: {
  values: string[];
  source?: string;
  periods?: string[];
  unit?: string;
}) => {
  const params = new URLSearchParams();
  values.forEach((v) => params.append("values", v));
  if (source) params.append("source", source);
  if (periods) periods.forEach((p) => params.append("periods", p));
  if (unit) params.append("unit", unit);
  const res = await fetch(`/api/functions/value_fetch?${params.toString()}`);
  return res.json();
};

export const functionsMap = {
  roll_dice: roll_dice,
  value_fetch: value_fetch,
};
