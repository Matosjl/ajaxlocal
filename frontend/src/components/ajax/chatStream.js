/**
 * Custom hook to apply streaming SSE events onto the assistant placeholder message.
 * Extracted from AjaxChat to reduce component complexity.
 */
export function applyStreamEvent(messages, asstId, ev) {
  return messages.map((msg) => {
    if (msg.id !== asstId) return msg;
    switch (ev.type) {
      case "plan":
        return { ...msg, plan: ev.content, planDirect: ev.direct };
      case "injection_warning":
        return { ...msg, injectionWarning: ev.message };
      case "tool_call":
        return {
          ...msg,
          tool_calls: [
            ...(msg.tool_calls || []),
            { id: ev.id, name: ev.name, arguments: ev.arguments },
          ],
        };
      case "tool_result":
        return {
          ...msg,
          tool_results: [
            ...(msg.tool_results || []),
            { id: ev.id, name: ev.name, ok: ev.ok, content: ev.content },
          ],
        };
      case "token":
        return { ...msg, content: (msg.content || "") + ev.content };
      case "final":
        return { ...msg, content: ev.content };
      case "error":
        return {
          ...msg,
          content: (msg.content || "") + `\n\n**Erro:** ${ev.message}`,
        };
      default:
        return msg;
    }
  });
}

export async function streamChat({ API, session_id, message, provider, model, onEvent, onDone, onError }) {
  try {
    const resp = await fetch(`${API}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id, message, provider, model }),
    });
    if (!resp.body) throw new Error("Sem stream");
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split("\n\n");
      buf = parts.pop() || "";
      for (const part of parts) {
        if (!part.startsWith("data: ")) continue;
        const data = part.slice(6);
        if (data === "[DONE]") continue;
        try {
          onEvent(JSON.parse(data));
        } catch (err) {
          if (process.env.NODE_ENV !== "production") {
            console.error("streamChat: bad SSE frame", err);
          }
        }
      }
    }
    onDone();
  } catch (err) {
    onError(err);
  }
}
