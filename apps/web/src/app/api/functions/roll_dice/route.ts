export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);

    const raw = searchParams.get("sides");
    const sides = raw ? parseInt(raw, 10) : 6;

    const safeSides = Number.isFinite(sides) && sides > 0 ? sides : 6;

    const value = 1 + Math.floor(Math.random() * safeSides);

    return new Response(JSON.stringify({ result: value }), {
      status: 200,
    });
  } catch (error) {
    console.error("Error generating dice roll:", error);
    return new Response(JSON.stringify({ error: "Error generating dice roll" }), {
      status: 500,
    });
  }
}
