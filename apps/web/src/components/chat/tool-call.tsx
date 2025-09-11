import React from "react";

import type { ToolCallItem } from "lib/ai/tools/assistant";

interface ToolCallProps {
  toolCall: ToolCallItem;
}

function ApiCallCell({ toolCall }: ToolCallProps) {
  return (
    <div className="relative mb-[-8px] flex w-[70%] flex-col">
      <div>
        <div className="flex flex-col rounded-[16px] text-sm">
          <div className="flex gap-2 rounded-b-none p-3 pl-0 font-semibold text-gray-700">
            <div className="text-moss ml-[-8px] flex items-center gap-2">
              <div className="text-sm font-medium">
                {toolCall.status === "completed"
                  ? `Called ${toolCall.name}`
                  : `Calling ${toolCall.name}...`}
              </div>
            </div>
          </div>

          <div className="bg-base-2 mt-2 ml-4 rounded-xl py-2">
            <div className="mx-6 max-h-96 overflow-y-scroll border-b p-2 text-xs">
              {JSON.stringify(toolCall.parsedArguments, null, 2)}
            </div>
            <div className="mx-6 max-h-96 overflow-y-scroll p-2 text-xs">
              {toolCall.output ? (
                <div> {JSON.stringify(JSON.parse(toolCall.output), null, 2)}</div>
              ) : (
                <div className="flex items-center gap-2 py-2 text-zinc-500">
                  Waiting for result...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function FileSearchCell({ toolCall }: ToolCallProps) {
  return (
    <div className="mb-[-16px] ml-[-8px] flex items-center gap-2 text-blue-500">
      <div className="mb-0.5 text-sm font-medium">
        {toolCall.status === "completed" ? "Searched files" : "Searching files..."}
      </div>
    </div>
  );
}

function WebSearchCell({ toolCall }: ToolCallProps) {
  return (
    <div className="mb-[-16px] ml-[-8px] flex items-center gap-2 text-blue-500">
      <div className="text-sm font-medium">
        {toolCall.status === "completed" ? "Searched the web" : "Searching the web..."}
      </div>
    </div>
  );
}

function McpCallCell({ toolCall }: ToolCallProps) {
  return (
    <div className="relative mb-[-8px] flex w-[70%] flex-col">
      <div>
        <div className="flex flex-col rounded-[16px] text-sm">
          <div className="flex gap-2 rounded-b-none p-3 pl-0 font-semibold text-gray-700">
            <div className="ml-[-8px] flex items-center gap-2 text-blue-500">
              <div className="text-sm font-medium">
                {toolCall.status === "completed"
                  ? `Called ${toolCall.name} via MCP tool`
                  : `Calling ${toolCall.name} via MCP tool...`}
              </div>
            </div>
          </div>

          <div className="mt-2 ml-4 rounded-xl bg-[#fafafa] py-2">
            <div className="mx-6 max-h-96 overflow-y-scroll border-b p-2 text-xs">
              {JSON.stringify(toolCall.parsedArguments, null, 2)}
            </div>
            <div className="mx-6 max-h-96 overflow-y-scroll p-2 text-xs">
              {toolCall.output ? (
                (() => {
                  try {
                    const parsed = JSON.parse(toolCall.output!);
                    return JSON.stringify(parsed, null, 2);
                  } catch {
                    return toolCall.output!;
                  }
                })()
              ) : (
                <div className="flex items-center gap-2 py-2 text-zinc-500">
                  Waiting for result...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function CodeInterpreterCell({ toolCall }: ToolCallProps) {
  return (
    <div className="relative mb-[-8px] flex w-[70%] flex-col">
      <div className="flex flex-col rounded-[16px] text-sm">
        <div className="flex gap-2 rounded-b-none p-3 pl-0 font-semibold text-gray-700">
          <div className="ml-[-8px] flex items-center gap-2 text-blue-500">
            <div className="text-sm font-medium">
              {toolCall.status === "completed" ? "Code executed" : "Running code interpreter..."}
            </div>
          </div>
        </div>
        <div className="mt-2 ml-4 rounded-xl bg-[#fafafa] py-2">
          <div className="mx-6 p-2 text-xs">{toolCall.code || ""}</div>
        </div>
        {toolCall.files && toolCall.files.length > 0 && (
          <div className="mt-2 ml-4 flex flex-wrap gap-2">
            {toolCall.files.map((f) => (
              <a
                key={f.file_id}
                href={`/api/container_files/content?file_id=${f.file_id}${
                  f.container_id ? `&container_id=${f.container_id}` : ""
                }${f.filename ? `&filename=${encodeURIComponent(f.filename)}` : ""}`}
                download
                className="inline-flex items-center gap-1 rounded-full bg-[#ededed] px-3 py-1 text-xs text-zinc-500"
              >
                {f.filename || f.file_id}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ToolCall({ toolCall }: ToolCallProps) {
  return (
    <div className="flex justify-start pt-2">
      {(() => {
        switch (toolCall.tool_type) {
          case "function_call":
            return <ApiCallCell toolCall={toolCall} />;
          case "file_search_call":
            return <FileSearchCell toolCall={toolCall} />;
          case "web_search_call":
            return <WebSearchCell toolCall={toolCall} />;
          case "mcp_call":
            return <McpCallCell toolCall={toolCall} />;
          case "code_interpreter_call":
            return <CodeInterpreterCell toolCall={toolCall} />;
          default:
            return null;
        }
      })()}
    </div>
  );
}
