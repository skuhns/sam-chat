import React from "react";

const LoadingMessage: React.FC = () => {
  return (
    <div className="text-sm">
      <div className="flex flex-col">
        <div className="flex">
          <div className="bg-moss mr-4 rounded-[16px] px-4 py-2 font-light text-black md:mr-24">
            <div className="bg-base h-3 w-3 animate-pulse rounded-full" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingMessage;
