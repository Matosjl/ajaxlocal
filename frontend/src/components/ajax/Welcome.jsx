import { Bot, Brain, Wrench, ShieldAlert, Database } from "lucide-react";

const CARDS = [
  {
    icon: Brain,
    title: "Pense antes de agir",
    desc: "Ajax planeja em Chain of Thought antes de chamar ferramentas.",
  },
  {
    icon: Wrench,
    title: "10+ ferramentas",
    desc: "Arquivos, shell, Python, código, web, RAG, SQL e mais.",
  },
  {
    icon: ShieldAlert,
    title: "Guardrails",
    desc: "SQL só SELECT, comandos perigosos bloqueados, segredos redactados.",
  },
  {
    icon: Database,
    title: "RAG de programação",
    desc: "Python, Java, C/C++, C#, Go já indexados.",
  },
];

export default function Welcome() {
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
        {CARDS.map((c) => (
          <div key={c.title} className="glass-card rounded-lg p-4">
            <c.icon size={18} className="text-orange-500 mb-2" />
            <p className="text-sm font-semibold text-zinc-100">{c.title}</p>
            <p className="text-xs text-zinc-400 mt-1">{c.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
