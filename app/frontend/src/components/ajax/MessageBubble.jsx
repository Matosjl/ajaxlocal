import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Bot, User, Brain, ShieldAlert, ChevronRight, Loader2 } from "lucide-react";
import ToolCallCard from "./ToolCallCard";

// Stable constants — avoid new array identity on every render
const REMARK_PLUGINS = [remarkGfm];
const REHYPE_PLUGINS = [rehypeHighlight];

export default function MessageBubble({ msg }) {
  if (msg.role === "tool") return null;

  if (msg.role === "user") {
    return (
      <div
        data-testid={`msg-user-${msg.id}`}
        className="flex gap-3 max-w-4xl mx-auto justify-end"
      >
        <div className="bg-orange-500/10 border border-orange-500/20 rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[80%] ajax-bubble-user">
          <p className="text-sm text-zinc-100 whitespace-pre-wrap">{msg.content}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center flex-shrink-0">
          <User size={15} className="text-zinc-400" />
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid={`msg-asst-${msg.id}`}
      className="flex gap-3 max-w-4xl mx-auto ajax-bubble-asst"
    >
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center flex-shrink-0">
        <Bot size={15} className="text-zinc-950" />
      </div>
      <div className="flex-1 space-y-3 min-w-0">
        {msg.injectionWarning && (
          <div className="tool-card-error rounded-lg p-3 text-xs flex items-center gap-2 text-red-300">
            <ShieldAlert size={14} />
            {msg.injectionWarning}
          </div>
        )}
        {msg.plan && (
          <details className="plan-glow rounded-lg overflow-hidden bg-orange-500/5 border border-orange-500/20">
            <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-orange-300 flex items-center gap-2 select-none">
              <Brain size={13} /> Plano (Chain of Thought)
              {msg.planDirect && (
                <span className="ml-auto text-[10px] text-zinc-500">resposta direta</span>
              )}
              <ChevronRight size={12} className="ml-auto transition group-open:rotate-90" />
            </summary>
            <pre className="text-xs text-zinc-300 px-3 pb-3 whitespace-pre-wrap font-sans leading-relaxed">
              {msg.plan}
            </pre>
          </details>
        )}
        {msg.tool_calls?.map((tc) => {
          const result = msg.tool_results?.find((r) => r.id === tc.id);
          return <ToolCallCard key={tc.id} call={tc} result={result} />;
        })}
        {msg.content && (
          <div className={`markdown-body ${msg.streaming ? "typing-cursor" : ""}`}>
            <ReactMarkdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={REHYPE_PLUGINS}>
              {msg.content}
            </ReactMarkdown>
          </div>
        )}
        {msg.streaming && !msg.content && (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Loader2 size={12} className="animate-spin" /> pensando...
          </div>
        )}
      </div>
    </div>
  );
}
