import { useEffect, useRef, useState, useCallback } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { toast } from "sonner";
import {
  Bot,
  User,
  Send,
  Plus,
  Trash2,
  Settings,
  Brain,
  Wrench,
  Activity,
  ShieldAlert,
  ChevronRight,
  Cpu,
  Database,
  Zap,
  Loader2,
  Menu,
  X,
  MessageCircle,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AjaxChat() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [provider, setProvider] = useState("openrouter");
  const [model, setModel] = useState("openrouter/auto");
  const [health, setHealth] = useState(null);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [collections, setCollections] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const scrollRef = useRef(null);

  // Close sidebar when selecting session on mobile
  const closeSidebarOnMobile = () => {
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  // ----- bootstrap -----
  const fetchSessions = useCallback(async () => {
    const r = await axios.get(`${API}/sessions`);
    setSessions(r.data);
    if (!activeSession && r.data.length > 0) {
      selectSession(r.data[0].id);
    }
  }, [activeSession]);

  const fetchHealth = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/health`);
      setHealth(r.data);
    } catch (e) {
      setHealth({ ok: false });
    }
  }, []);

  const fetchCollections = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/rag/collections`);
      setCollections(r.data);
    } catch {}
  }, []);

  useEffect(() => {
    fetchHealth();
    fetchSessions();
    fetchCollections();
  }, [fetchHealth, fetchSessions, fetchCollections]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // ----- session ops -----
  const createSession = async () => {
    const r = await axios.post(`${API}/sessions`, {
      title: "Nova conversa",
      provider,
      model,
    });
    await fetchSessions();
    selectSession(r.data.id);
  };

  const selectSession = async (sid) => {
    setActiveSession(sid);
    const r = await axios.get(`${API}/sessions/${sid}/messages`);
    setMessages(r.data);
    refreshLogs(sid);
    closeSidebarOnMobile();
  };

  const deleteSession = async (sid, e) => {
    e.stopPropagation();
    await axios.delete(`${API}/sessions/${sid}`);
    if (activeSession === sid) {
      setActiveSession(null);
      setMessages([]);
    }
    fetchSessions();
  };

  const refreshLogs = async (sid) => {
    const [l, s] = await Promise.all([
      axios.get(`${API}/logs?session_id=${sid}&limit=50`),
      axios.get(`${API}/stats?session_id=${sid}`),
    ]);
    setLogs(l.data);
    setStats(s.data);
  };

  // ----- chat send (SSE) -----
  const sendMessage = async () => {
    if (!input.trim() || streaming) return;
    let sid = activeSession;
    if (!sid) {
      const r = await axios.post(`${API}/sessions`, { title: input.slice(0, 40), provider, model });
      sid = r.data.id;
      setActiveSession(sid);
      await fetchSessions();
    }

    const userMsg = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, userMsg]);

    const userText = input;
    setInput("");
    setStreaming(true);

    // Add streaming assistant placeholder
    const asstId = `tmp-asst-${Date.now()}`;
    setMessages((m) => [
      ...m,
      {
        id: asstId,
        role: "assistant",
        content: "",
        plan: null,
        tool_calls: [],
        tool_results: [],
        streaming: true,
      },
    ]);

    try {
      const resp = await fetch(`${API}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sid, message: userText, provider, model }),
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
            const ev = JSON.parse(data);
            applyStreamEvent(asstId, ev);
          } catch (e) {
            console.warn("parse SSE", e);
          }
        }
      }
      setStreaming(false);
      setMessages((m) =>
        m.map((msg) => (msg.id === asstId ? { ...msg, streaming: false } : msg))
      );
      refreshLogs(sid);
      fetchSessions();
    } catch (e) {
      toast.error("Erro: " + e.message);
      setStreaming(false);
    }
  };

  const applyStreamEvent = (asstId, ev) => {
    setMessages((m) =>
      m.map((msg) => {
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
            return { ...msg, content: (msg.content || "") + `\n\n**Erro:** ${ev.message}` };
          default:
            return msg;
        }
      })
    );
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const totalDocs = collections.reduce((a, c) => a + (c.count || 0), 0);

  return (
    <div className="flex h-[100dvh] overflow-hidden grain bg-[#0a0a0c]">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      {/* Sidebar */}
      <aside
        data-testid="sidebar"
        className={`${sidebarOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0 fixed md:relative top-0 left-0 h-[100dvh] md:h-auto z-40 md:z-auto w-[82vw] max-w-[320px] md:w-72 md:max-w-none border-r border-zinc-800/80 bg-[#0d0d10] flex flex-col transition-transform duration-200`}
      >
        <div className="p-5 border-b border-zinc-800/80">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center">
              <Bot size={20} className="text-zinc-950" />
            </div>
            <div className="flex-1">
              <h1 className="text-base font-bold tracking-tight text-zinc-100">AJAX</h1>
              <p className="text-[11px] text-zinc-500 -mt-0.5">super-agente local</p>
            </div>
            <button
              data-testid="sidebar-close-btn"
              onClick={() => setSidebarOpen(false)}
              className="md:hidden text-zinc-500 hover:text-zinc-200"
            >
              <X size={20} />
            </button>
          </div>
          <Button
            data-testid="new-session-btn"
            onClick={() => { createSession(); closeSidebarOnMobile(); }}
            className="w-full mt-4 bg-orange-500 hover:bg-orange-600 text-zinc-950 font-medium"
          >
            <Plus size={16} className="mr-1" />
            Nova conversa
          </Button>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {sessions.length === 0 && (
              <p className="text-xs text-zinc-600 px-3 py-4 text-center">
                Nenhuma conversa ainda
              </p>
            )}
            {sessions.map((s) => (
              <button
                key={s.id}
                data-testid={`session-${s.id}`}
                onClick={() => selectSession(s.id)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm group flex items-center justify-between ${
                  activeSession === s.id
                    ? "bg-orange-500/10 text-orange-300 border border-orange-500/20"
                    : "text-zinc-400 hover:bg-zinc-900"
                }`}
              >
                <span className="truncate flex-1">{s.title || "Sem título"}</span>
                <Trash2
                  size={13}
                  onClick={(e) => deleteSession(s.id, e)}
                  className="opacity-0 group-hover:opacity-60 hover:opacity-100 transition"
                />
              </button>
            ))}
          </div>
        </ScrollArea>

        <div className="p-3 border-t border-zinc-800/80 space-y-2 text-xs text-zinc-500">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Database size={12} />
              RAG
            </span>
            <Badge variant="outline" className="text-[10px] border-zinc-800 text-zinc-400">
              {health?.rag_backend || "—"} · {totalDocs} docs
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Cpu size={12} />
              Provider
            </span>
            <Badge variant="outline" className="text-[10px] border-zinc-800 text-zinc-400">
              {provider}
            </Badge>
          </div>
          <Dialog open={showSettings} onOpenChange={setShowSettings}>
            <DialogTrigger asChild>
              <Button
                data-testid="settings-btn"
                variant="ghost"
                size="sm"
                className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
              >
                <Settings size={14} className="mr-2" />
                Configurações
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-[#0d0d10] border-zinc-800">
              <DialogHeader>
                <DialogTitle className="text-zinc-100">Configurações do Agente</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-3">
                <div>
                  <label className="text-xs text-zinc-400 block mb-1.5">Provider</label>
                  <Select value={provider} onValueChange={setProvider}>
                    <SelectTrigger data-testid="provider-select" className="bg-zinc-900 border-zinc-800">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0d0d10] border-zinc-800">
                      <SelectItem value="openrouter">OpenRouter (cloud)</SelectItem>
                      <SelectItem value="ollama">Ollama (local)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs text-zinc-400 block mb-1.5">Modelo</label>
                  <Input
                    data-testid="model-input"
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="bg-zinc-900 border-zinc-800 font-mono text-sm"
                  />
                  <p className="text-[10px] text-zinc-600 mt-1">
                    Ex: openrouter/auto, anthropic/claude-3.5-sonnet, llama3.1, qwen2.5-coder:7b
                  </p>
                </div>
                <div className="text-xs text-zinc-500 border-t border-zinc-800 pt-3 space-y-1">
                  <div>OpenRouter: {health?.openrouter_configured ? "✅" : "❌"}</div>
                  <div>Supabase DB: {health?.supabase_db_configured ? "✅" : "❌"} (backend RAG: {health?.rag_backend})</div>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          {/* Developer credits */}
          <a
            data-testid="dev-credits"
            href="https://wa.me/5551981521264?text=Ol%C3%A1%20Jos%C3%A9%20Lorenzo%2C%20vi%20o%20Ajax%20Super-Agent%20e%20gostaria%20de%20conversar"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 block text-center text-[10px] text-zinc-600 hover:text-orange-400 transition border-t border-zinc-900/80 pt-2"
          >
            <span className="block">desenvolvido por</span>
            <span className="block text-zinc-400 font-semibold flex items-center justify-center gap-1 mt-0.5">
              <MessageCircle size={10} /> José Lorenzo
            </span>
            <span className="block mono text-zinc-600 text-[10px]">(51) 98152-1264</span>
          </a>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <Tabs defaultValue="chat" className="flex flex-col h-full ajax-tabs">
          <div className="border-b border-zinc-800/80 px-4 md:px-6 py-3 flex items-center justify-between bg-[#0a0a0c] gap-2">
            <button
              data-testid="sidebar-toggle"
              onClick={() => setSidebarOpen(true)}
              className="md:hidden text-zinc-400 hover:text-zinc-100 p-1"
            >
              <Menu size={22} />
            </button>
            <TabsList className="bg-zinc-900 border border-zinc-800">
              <TabsTrigger data-testid="tab-chat" value="chat" className="data-[state=active]:bg-orange-500 data-[state=active]:text-zinc-950">
                Chat
              </TabsTrigger>
              <TabsTrigger data-testid="tab-logs" value="logs" className="data-[state=active]:bg-orange-500 data-[state=active]:text-zinc-950">
                <span className="hidden sm:inline">Observabilidade</span>
                <span className="sm:hidden">Logs</span>
              </TabsTrigger>
              <TabsTrigger data-testid="tab-rag" value="rag" className="data-[state=active]:bg-orange-500 data-[state=active]:text-zinc-950">
                RAG
              </TabsTrigger>
            </TabsList>
            {stats && (
              <div className="hidden md:flex items-center gap-3 text-xs text-zinc-500">
                <span className="flex items-center gap-1"><Zap size={12} /> {stats.total_events} eventos</span>
                <span>· {stats.prompt_tokens + stats.completion_tokens} tokens</span>
                <span>· {(stats.total_duration_ms / 1000).toFixed(1)}s</span>
              </div>
            )}
          </div>

          {/* CHAT */}
          <TabsContent value="chat" className="flex-1 flex flex-col overflow-hidden m-0">
            <div ref={scrollRef} className="flex-1 overflow-y-auto chat-scroll px-3 md:px-6 py-6 md:py-8 space-y-6">
              {messages.length === 0 && !streaming && (
                <Welcome />
              )}
              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}
            </div>

            {/* Composer */}
            <div className="border-t border-zinc-800/80 p-3 md:p-4 bg-[#0a0a0c] ajax-composer safe-bottom">
              <div className="max-w-4xl mx-auto">
                <div className="relative">
                  <Textarea
                    data-testid="chat-input"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={onKeyDown}
                    disabled={streaming}
                    placeholder="Pergunte ao Ajax..."
                    className="min-h-[60px] max-h-40 resize-none bg-zinc-900/50 border-zinc-800 pr-14 focus-visible:ring-orange-500/50 text-sm"
                  />
                  <Button
                    data-testid="send-btn"
                    onClick={sendMessage}
                    disabled={streaming || !input.trim()}
                    size="icon"
                    className="absolute bottom-2 right-2 h-9 w-9 bg-orange-500 hover:bg-orange-600 text-zinc-950 disabled:bg-zinc-800 disabled:text-zinc-600"
                  >
                    {streaming ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                  </Button>
                </div>
                <p className="text-[10px] text-zinc-600 mt-2 text-center hidden md:block">
                  Ajax pensa antes de agir · ferramentas sandboxadas · respostas com markdown
                </p>
              </div>
            </div>
          </TabsContent>

          {/* LOGS */}
          <TabsContent value="logs" className="flex-1 overflow-y-auto chat-scroll p-6 m-0">
            <div className="max-w-4xl mx-auto space-y-3">
              <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                <Activity size={18} className="text-orange-500" />
                Eventos da Sessão
              </h2>
              {logs.length === 0 && <p className="text-sm text-zinc-500">Sem eventos ainda.</p>}
              {logs.map((log) => (
                <div
                  key={log.id}
                  data-testid={`log-${log.id}`}
                  className="glass-card rounded-lg p-3 text-xs font-mono"
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <Badge
                        className={
                          log.type === "tool_call"
                            ? "bg-orange-500/20 text-orange-300 border-orange-500/30"
                            : log.type === "plan"
                            ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                            : "bg-zinc-800 text-zinc-400"
                        }
                      >
                        {log.type}
                      </Badge>
                      <span className="text-zinc-300">{log.name}</span>
                      {log.status === "error" && (
                        <Badge variant="destructive" className="text-[10px]">erro</Badge>
                      )}
                    </div>
                    <span className="text-zinc-600">{log.duration_ms}ms · {log.prompt_tokens + log.completion_tokens} tk</span>
                  </div>
                  {log.payload && (
                    <pre className="text-[10px] text-zinc-500 mt-2 overflow-x-auto">
                      {JSON.stringify(log.payload, null, 2).slice(0, 600)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          </TabsContent>

          {/* RAG */}
          <TabsContent value="rag" className="flex-1 overflow-y-auto chat-scroll p-6 m-0">
            <div className="max-w-4xl mx-auto space-y-4">
              <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                <Database size={18} className="text-orange-500" />
                Base de Conhecimento (RAG)
              </h2>
              <p className="text-sm text-zinc-400">
                Backend: <span className="text-orange-300 font-mono">{health?.rag_backend}</span> ·
                {" "}{totalDocs} documentos indexados
              </p>
              <div className="grid gap-3">
                {collections.map((c) => (
                  <div key={c.name} className="glass-card rounded-lg p-4 flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-zinc-100">{c.name}</p>
                      <p className="text-xs text-zinc-500">{c.count} documentos</p>
                    </div>
                    <Badge variant="outline" className="border-orange-500/30 text-orange-300">
                      ativa
                    </Badge>
                  </div>
                ))}
              </div>
              <div className="glass-card rounded-lg p-4 mt-6">
                <p className="text-xs text-zinc-400 mb-2">Reseed via terminal:</p>
                <pre className="text-xs text-orange-300 mono bg-black/40 p-3 rounded">
                  cd /app && python -m backend.seed_rag
                </pre>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

function Welcome() {
  const cards = [
    { icon: Brain, title: "Pense antes de agir", desc: "Ajax planeja em Chain of Thought antes de chamar ferramentas." },
    { icon: Wrench, title: "10+ ferramentas", desc: "Arquivos, shell, Python, código, web, RAG, SQL e mais." },
    { icon: ShieldAlert, title: "Guardrails", desc: "SQL só SELECT, comandos perigosos bloqueados, segredos redactados." },
    { icon: Database, title: "RAG de programação", desc: "Python, Java, C/C++, C#, Go já indexados." },
  ];
  return (
    <div className="max-w-3xl mx-auto py-12">
      <div className="text-center mb-8">
        <div className="inline-flex w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500 to-orange-700 items-center justify-center mb-4">
          <Bot size={32} className="text-zinc-950" />
        </div>
        <h2 className="text-3xl font-bold text-zinc-100">Olá, sou o Ajax</h2>
        <p className="text-zinc-400 mt-2">
          Seu super-agente de programação e automação local. Manda ver.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3 ajax-welcome-grid">
        {cards.map((c, i) => (
          <div key={i} className="glass-card rounded-lg p-4">
            <c.icon size={18} className="text-orange-500 mb-2" />
            <p className="text-sm font-semibold text-zinc-100">{c.title}</p>
            <p className="text-xs text-zinc-400 mt-1">{c.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ msg }) {
  if (msg.role === "user") {
    return (
      <div data-testid={`msg-user-${msg.id}`} className="flex gap-3 max-w-4xl mx-auto justify-end">
        <div className="bg-orange-500/10 border border-orange-500/20 rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[80%] ajax-bubble-user">
          <p className="text-sm text-zinc-100 whitespace-pre-wrap">{msg.content}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center flex-shrink-0">
          <User size={15} className="text-zinc-400" />
        </div>
      </div>
    );
  }
  if (msg.role === "tool") {
    return null; // tool messages handled inside assistant message
  }

  return (
    <div data-testid={`msg-asst-${msg.id}`} className="flex gap-3 max-w-4xl mx-auto ajax-bubble-asst">
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
              {msg.planDirect && <span className="ml-auto text-[10px] text-zinc-500">resposta direta</span>}
              <ChevronRight size={12} className="ml-auto transition group-open:rotate-90" />
            </summary>
            <pre className="text-xs text-zinc-300 px-3 pb-3 whitespace-pre-wrap font-sans leading-relaxed">
              {msg.plan}
            </pre>
          </details>
        )}
        {msg.tool_calls?.map((tc) => {
          const result = msg.tool_results?.find((r) => r.id === tc.id);
          return (
            <ToolCallCard key={tc.id} call={tc} result={result} />
          );
        })}
        {msg.content && (
          <div className={`markdown-body ${msg.streaming ? "typing-cursor" : ""}`}>
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
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

function ToolCallCard({ call, result }) {
  const [open, setOpen] = useState(false);
  let args = {};
  try { args = JSON.parse(call.arguments); } catch {}
  const ok = result?.ok !== false;
  return (
    <div className={`rounded-lg ${ok ? "tool-card" : "tool-card-error"} text-xs`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-3 py-2 flex items-center gap-2 text-left"
      >
        <Wrench size={12} className={ok ? "text-orange-400" : "text-red-400"} />
        <span className="font-mono text-zinc-200">{call.name}</span>
        <span className="text-zinc-500 truncate flex-1">
          ({Object.keys(args).join(", ")})
        </span>
        {!result && <Loader2 size={12} className="animate-spin text-zinc-500" />}
        {result && (
          <Badge className={ok ? "bg-green-500/15 text-green-400 border-green-500/20 text-[10px]" : "bg-red-500/15 text-red-400 border-red-500/20 text-[10px]"}>
            {ok ? "ok" : "erro"}
          </Badge>
        )}
      </button>
      {open && (
        <div className="border-t border-orange-500/15 px-3 py-2 space-y-2 font-mono">
          <div>
            <span className="text-zinc-600">args:</span>
            <pre className="text-zinc-300 mt-1 overflow-x-auto">{JSON.stringify(args, null, 2)}</pre>
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
