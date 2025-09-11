import type { MessageItem } from "lib/ai/tools/assistant";
import React from "react";

interface MessageProps {
  message: MessageItem;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  const content = message.content[0];
  if (!content) {
    return null;
  }
  const text = content.text;
  return (
    text && (
      <div className="text-sm">
        {message.role === "user" ? (
          <div className="flex justify-end">
            <div>
              <div className="bg-base-2/100 mr-4 rounded-[16px] px-4 py-2 font-light text-neutral-50 md:ml-24">
                <div>
                  <div>{text}</div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col">
            <div className="flex">
              <div className="bg-base-2/100 mr-4 rounded-[16px] px-4 py-2 font-light text-neutral-200 md:mr-24">
                <div>
                  {text}
                  {content &&
                    content.annotations &&
                    content.annotations
                      .filter(
                        (a) =>
                          a.type === "container_file_citation" &&
                          a.filename &&
                          /\.(png|jpg|jpeg|gif|webp|svg)$/i.test(a.filename),
                      )
                      .map((a, i) => (
                        <img
                          key={i}
                          src={`/api/container_files/content?file_id=${a.fileId}${a.containerId ? `&container_id=${a.containerId}` : ""}${a.filename ? `&filename=${encodeURIComponent(a.filename)}` : ""}`}
                          alt={a.filename || ""}
                          className="mt-2 max-w-full"
                        />
                      ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  );
};

export default Message;
