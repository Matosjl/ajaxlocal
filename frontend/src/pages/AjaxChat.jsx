import { useEffect, useRef, useState, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Send, Menu, Loader2, Activity, Database, Zap } from "lucide-react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";

import Sidebar from "../components/ajax/Sidebar";
import MessageBubble from "../components/ajax/MessageBubble";
import Welcome from "../components/ajax/Welcome";
import { applyStreamEvent, streamChat } from "../components/ajax/chatStream";

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

  // ----- bootstrap -----
  const refreshLogs = useCallback(async (sid) => {
    try {
      const [l, s] = await Promise.all([
        axios.get(`${API}/logs?session_id=${sid}&limit=50`),
        axios.get(`${API}/stats?session_id=${sid}`),
      ]);
      setLogs(l.data);
      setStats(s.data);
    } catch (err) {
      if (process.env.NODE_ENV !== "production") console.error("refreshLogs failed", err);
    }
  }, []);

  const selectSession = useCallback(
    async (sid) => {
      setActiveSession(sid);
      try {
        const r = await axios.get(`${API}/sessions/${sid}/messages`);
        setMessages(r.data);
        refreshLogs(sid);
      } catch (err) {
        toast.error("Falha ao carregar sessão");
        if (process.env.NODE_ENV !== "production") console.error(err);
      }
      if (window.innerWidth < 768) setSidebarOpen(false);
    },
    [refreshLogs]
  );

  const fetchSessions = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/sessions`);
      setSessions(r.data);
      setActiveSession((cur) => {
        if (!cur && r.data.length > 0) {
          selectSession(r.data[0].id);
          return cur;
        }
        return cur;
      });
    } catch (err) {
      if (process.env.NODE_ENV !== "production") console.error("fetchSessions failed", err);
    }
  }, [selectSession]);

  const fetchHealth = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/health`);
      setHealth(r.data);
    } catch (err) {
      setHealth({ ok: false });
      if (process.env.NODE_ENV !== "production") console.error("fetchHealth failed", err);
    }
  }, []);

  const fetchCollections = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/rag/collections`);
      setCollections(r.data);
    } catch (err) {
      if (process.env.NODE_ENV !== "production") console.error("fetchCollections failed", err);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    fetchSessions();
    fetchCollections();
  }, [fetchHealth, fetchSessions, fetchCollections]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  // ----- session ops -----
  const createSession = async () => {
    try {
      const r = await axios.post(`${API}/sessions`, {
        title: "Nova conversa",
        provider,
        model,
      });
      await fetchSessions();
      selectSession(r.data.id);
    } catch (err) {
      toast.error("Erro ao criar sessão");
      if (process.env.NODE_ENV !== "production") console.error(err);
    }
  };

  const deleteSession = async (sid) => {
    try {
      await axios.delete(`${API}/sessions/${sid}`);
      if (activeSession === sid) {
        setActiveSession(null);
        setMessages([]);
      }
      fetchSessions();
    } catch (err) {
      toast.error("Erro ao excluir");
      if (process.env.NODE_ENV !== "production") console.error(err);
    }
  };

  // ----- chat send (SSE) -----
  const sendMessage = async () => {
    if (!input.trim() || streaming) return;

    let sid = activeSession;
    if (!sid) {
      try {
        const r = await axios.post(`${API}/sessions`, {
          title: input.slice(0, 40),
          provider,
          model,
        });
        sid = r.data.id;
        setActiveSession(sid);
        await fetchSessions();
      } catch (err) {
        toast.error("Erro ao criar sessão");
        if (process.env.NODE_ENV !== "production") console.error(err);
        return;
      }
    }

    const userMsg = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
    };
    const asstId = `tmp-asst-${Date.now()}`;
    setMessages((m) => [
      ...m,
      userMsg,
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

    const userText = input;
    setInput("");
    setStreaming(true);

    await streamChat({
      API,
      session_id: sid,
      message: userText,
      provider,
      model,
      onEvent: (ev) => setMessages((m) => applyStreamEvent(m, asstId, ev)),
      onDone: () => {
        setStreaming(false);
        setMessages((m) =>
          m.map((msg) => (msg.id === asstId ? { ...msg, streaming: false } : msg))
        );
        refreshLogs(sid);
        fetchSessions();
      },
      onError: (err) => {
        toast.error("Erro: " + err.message);
        setStreaming(false);
        if (process.env.NODE_ENV !== "production") console.error(err);
      },
    });
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
      <Sidebar
        sessions={sessions}
        activeSession={activeSession}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        provider={provider}
        setProvider={setProvider}
        model={model}
        setModel={setModel}
        health={health}
        totalDocs={totalDocs}
        onCreateSession={createSession}
        onSelectSession={selectSession}
        onDeleteSession={deleteSession}
        showSettings={showSettings}
        setShowSettings={setShowSettings}
      />

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
                <span className="flex items-center gap-1">
                  <Zap size={12} /> {stats.total_events} eventos
                </span>
                <span>· {stats.prompt_tokens + stats.completion_tokens} tokens</span>
                <span>· {(stats.total_duration_ms / 1000).toFixed(1)}s</span>
              </div>
            )}
          </div>

          <TabsContent value="chat" className="flex-1 flex flex-col overflow-hidden m-0">
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto chat-scroll px-3 md:px-6 py-6 md:py-8 space-y-6"
            >
              {messages.length === 0 && !streaming && <Welcome />}
              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}
            </div>

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
                    {streaming ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Send size={16} />
                    )}
                  </Button>
                </div>
                <p className="text-[10px] text-zinc-600 mt-2 text-center hidden md:block">
                  Ajax pensa antes de agir · ferramentas sandboxadas · respostas com markdown
                </p>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="logs" className="flex-1 overflow-y-auto chat-scroll p-6 m-0">
            <div className="max-w-4xl mx-auto space-y-3">
              <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                <Activity size={18} className="text-orange-500" />
                Eventos da Sessão
              </h2>
              {logs.length === 0 && (
                <p className="text-sm text-zinc-500">Sem eventos ainda.</p>
              )}
              {logs.map((log) => (
                <LogRow key={log.id} log={log} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="rag" className="flex-1 overflow-y-auto chat-scroll p-6 m-0">
            <div className="max-w-4xl mx-auto space-y-4">
              <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                <Database size={18} className="text-orange-500" />
                Base de Conhecimento (RAG)
              </h2>
              <p className="text-sm text-zinc-400">
                Backend:{" "}
                <span className="text-orange-300 font-mono">{health?.rag_backend}</span>{" "}
                · {totalDocs} documentos indexados
              </p>
              <div className="grid gap-3">
                {collections.map((c) => (
                  <div
                    key={c.name}
                    className="glass-card rounded-lg p-4 flex items-center justify-between"
                  >
                    <div>
                      <p className="font-semibold text-zinc-100">{c.name}</p>
                      <p className="text-xs text-zinc-500">{c.count} documentos</p>
                    </div>
                    <Badge
                      variant="outline"
                      className="border-orange-500/30 text-orange-300"
                    >
                      ativa
                    </Badge>
                  </div>
                ))}
              </div>
              <div className="glass-card rounded-lg p-4 mt-6">
                <p className="text-xs text-zinc-400 mb-2">Reseed via terminal:</p>
                <pre className="text-xs text-orange-300 mono bg-black/40 p-3 rounded">
                  cd /app &amp;&amp; python -m backend.seed_rag
                </pre>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

function LogRow({ log }) {
  return (
    <div
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
            <Badge variant="destructive" className="text-[10px]">
              erro
            </Badge>
          )}
        </div>
        <span className="text-zinc-600">
          {log.duration_ms}ms · {log.prompt_tokens + log.completion_tokens} tk
        </span>
      </div>
      {log.payload && (
        <pre className="text-[10px] text-zinc-500 mt-2 overflow-x-auto">
          {JSON.stringify(log.payload, null, 2).slice(0, 600)}
        </pre>
      )}
    </div>
  );
}
