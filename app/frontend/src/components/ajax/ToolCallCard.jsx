import { useState } from "react";
import { Wrench, Loader2 } from "lucide-react";
import { Badge } from "../ui/badge";

function safeParseArgs(raw) {
  try {
    return JSON.parse(raw || "{}");
  } catch (err) {
    if (process.env.NODE_ENV !== "production") {
      console.error("ToolCallCard: invalid JSON arguments", err);
    }
    return {};
  }
}

export default function ToolCallCard({ call, result }) {
  const [open, setOpen] = useState(false);
  const args = safeParseArgs(call.arguments);
  const ok = result?.ok !== false;

  return (
    <div className={`rounded-lg ${ok ? "tool-card" : "tool-card-error"} text-xs`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-3 py-2 flex items-center gap-2 text-left"
        data-testid={`tool-card-${call.name}`}
      >
        <Wrench size={12} className={ok ? "text-orange-400" : "text-red-400"} />
        <span className="font-mono text-zinc-200">{call.name}</span>
        <span className="text-zinc-500 truncate flex-1">
          ({Object.keys(args).join(", ")})
        </span>
        {!result && <Loader2 size={12} className="animate-spin text-zinc-500" />}
        {result && (
          <Badge
            className={
              ok
                ? "bg-green-500/15 text-green-400 border-green-500/20 text-[10px]"
                : "bg-red-500/15 text-red-400 border-red-500/20 text-[10px]"
            }
          >
            {ok ? "ok" : "erro"}
          </Badge>
        )}
      </button>
      {open && (
        <div className="border-t border-orange-500/15 px-3 py-2 space-y-2 font-mono">
          <div>
            <span className="text-zinc-600">args:</span>
            <pre className="text-zinc-300 mt-1 overflow-x-auto">
              {JSON.stringify(args, null, 2)}
            </pre>
          </div>
          {result && (
            <div>
              <span className="text-zinc-600">resultado:</span>
              <pre className="text-zinc-400 mt-1 overflow-x-auto whitespace-pre-wrap">
                {(result.content || "").slice(0, 2000)}
                {(result.content || "").length > 2000 && "\n... [truncado]"}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
