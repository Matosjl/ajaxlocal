import {
  Bot,
  Plus,
  Trash2,
  Settings,
  Cpu,
  Database,
  X,
  MessageCircle,
} from "lucide-react";
import { Button } from "../ui/button";
import { ScrollArea } from "../ui/scroll-area";
import { Badge } from "../ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Input } from "../ui/input";

const WHATSAPP_URL =
  "https://wa.me/5551981521264?text=Ol%C3%A1%20Jos%C3%A9%20Lorenzo%2C%20vi%20o%20Ajax%20Super-Agent%20e%20gostaria%20de%20conversar";

export default function Sidebar({
  sessions,
  activeSession,
  sidebarOpen,
  setSidebarOpen,
  provider,
  setProvider,
  model,
  setModel,
  health,
  totalDocs,
  onCreateSession,
  onSelectSession,
  onDeleteSession,
  showSettings,
  setShowSettings,
}) {
  const closeOnMobile = () => {
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  return (
    <>
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
          data-testid="sidebar-backdrop"
        />
      )}
      <aside
        data-testid="sidebar"
        className={`${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0 fixed md:relative top-0 left-0 h-[100dvh] md:h-auto z-40 md:z-auto w-[82vw] max-w-[320px] md:w-72 md:max-w-none border-r border-zinc-800/80 bg-[#0d0d10] flex flex-col transition-transform duration-200`}
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
            onClick={() => {
              onCreateSession();
              closeOnMobile();
            }}
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
                onClick={() => onSelectSession(s.id)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm group flex items-center justify-between ${
                  activeSession === s.id
                    ? "bg-orange-500/10 text-orange-300 border border-orange-500/20"
                    : "text-zinc-400 hover:bg-zinc-900"
                }`}
              >
                <span className="truncate flex-1">{s.title || "Sem título"}</span>
                <Trash2
                  size={13}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }}
                  className="opacity-0 group-hover:opacity-60 hover:opacity-100 transition"
                />
              </button>
            ))}
          </div>
        </ScrollArea>

        <div className="p-3 border-t border-zinc-800/80 space-y-2 text-xs text-zinc-500">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Database size={12} /> RAG
            </span>
            <Badge
              variant="outline"
              className="text-[10px] border-zinc-800 text-zinc-400"
            >
              {health?.rag_backend || "—"} · {totalDocs} docs
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Cpu size={12} /> Provider
            </span>
            <Badge
              variant="outline"
              className="text-[10px] border-zinc-800 text-zinc-400"
            >
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
                <DialogTitle className="text-zinc-100">
                  Configurações do Agente
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-3">
                <div>
                  <label className="text-xs text-zinc-400 block mb-1.5">Provider</label>
                  <Select value={provider} onValueChange={setProvider}>
                    <SelectTrigger
                      data-testid="provider-select"
                      className="bg-zinc-900 border-zinc-800"
                    >
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
                    Ex: openrouter/auto, anthropic/claude-3.5-sonnet, llama3.1,
                    qwen2.5-coder:7b
                  </p>
                </div>
                <div className="text-xs text-zinc-500 border-t border-zinc-800 pt-3 space-y-1">
                  <div>OpenRouter: {health?.openrouter_configured ? "✅" : "❌"}</div>
                  <div>
                    Supabase DB: {health?.supabase_db_configured ? "✅" : "❌"} (backend
                    RAG: {health?.rag_backend})
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <a
            data-testid="dev-credits"
            href={WHATSAPP_URL}
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
    </>
  );
}
