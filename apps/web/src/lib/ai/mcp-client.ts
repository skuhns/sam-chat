type JsonRpcReq = { jsonrpc: "2.0"; id: string | number; method: string; params?: unknown };
type JsonRpcRes<T = unknown> = {
  jsonrpc: "2.0";
  id: string | number;
  result?: T;
  error?: { message: string };
};

const MCP_URL = "/api/mcp";

export async function mcpRpc<T = unknown>(method: string, params?: unknown): Promise<T> {
  const body: JsonRpcReq = { jsonrpc: "2.0", id: Date.now(), method, params };
  const res = await fetch(MCP_URL, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      accept: "application/json, text/event-stream", // ok even if SSE disabled
    },
    body: JSON.stringify(body),
  });
  const data = (await res.json()) as JsonRpcRes<T>;
  if (data.error) throw new Error(data.error.message);
  return data.result as T;
}

export function mcpCallTool<T = unknown>(name: string, args: Record<string, unknown>) {
  return mcpRpc<T>("tools/call", { name, arguments: args });
}
