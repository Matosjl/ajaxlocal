"""Seed the RAG with curated programming knowledge: Python, Java, C, C++, C#, Go,
plus fullstack web (React, Next.js, TypeScript, Node.js, FastAPI) and mobile (React Native, Flutter, PWA).

Run: cd /app && python -m backend.seed_rag
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from agent_core import LLMRouter, RAGStore  # noqa: E402

PROGRAMMING_KNOWLEDGE = [
    # ---- PYTHON ----
    {"titulo": "Python — Decoradores", "linguagem": "python", "content": """Decoradores em Python são funções que envolvem outras funções para adicionar comportamento sem modificar o código original.
Sintaxe:
def meu_decorator(func):
    def wrapper(*args, **kwargs):
        print('antes')
        r = func(*args, **kwargs)
        print('depois')
        return r
    return wrapper

@meu_decorator
def saudacao(nome):
    print(f'Olá {nome}')
Equivale a: saudacao = meu_decorator(saudacao). Usado para logging, cache (functools.lru_cache), validação, autorização."""},

    {"titulo": "Python — List/Dict Comprehensions", "linguagem": "python", "content": """Comprehensions são forma idiomática e performática de criar listas/dicionários:
Lista: [x*2 for x in range(10) if x%2==0]
Dict:  {k: v for k, v in pares}
Set:   {x for x in items}
Gerador: (x*x for x in range(1000))  # lazy, economiza memória
Regra: se a expressão tem mais de 2 condições ou é complexa, prefira loop tradicional para legibilidade."""},

    {"titulo": "Python — Async/Await", "linguagem": "python", "content": """Programação assíncrona com asyncio:
import asyncio
async def buscar(url):
    await asyncio.sleep(1)
    return url
async def main():
    resultados = await asyncio.gather(buscar('a'), buscar('b'))
asyncio.run(main())
Use para I/O paralelo (HTTP, DB). NÃO use para CPU-bound (use multiprocessing). Bibliotecas async: httpx, aiohttp, asyncpg, motor."""},

    {"titulo": "Python — Context Managers (with)", "linguagem": "python", "content": """Context managers garantem cleanup mesmo com exceções:
with open('f.txt') as f:  # __enter__ / __exit__
    data = f.read()
Customizado:
from contextlib import contextmanager
@contextmanager
def transacao(db):
    db.begin()
    try: yield db; db.commit()
    except: db.rollback(); raise
"""},

    {"titulo": "Python — Type Hints e Pydantic", "linguagem": "python", "content": """Type hints (Python 3.5+) melhoram autocomplete e detectam bugs:
def soma(a: int, b: int) -> int: return a+b
from typing import Optional, List, Dict
nomes: List[str] = []
config: Dict[str, int] = {}
Pydantic v2:
from pydantic import BaseModel
class User(BaseModel):
    nome: str
    idade: int = 0
u = User(nome='Ana')  # validação automática"""},

    # ---- JAVA ----
    {"titulo": "Java — Streams API", "linguagem": "java", "content": """Streams permitem operações funcionais em coleções:
List<Integer> pares = numeros.stream()
    .filter(n -> n % 2 == 0)
    .map(n -> n * 2)
    .collect(Collectors.toList());
Operações intermediárias (filter, map, sorted) são lazy. Terminais (collect, count, forEach) disparam execução. Use parallelStream() para paralelismo automático em coleções grandes."""},

    {"titulo": "Java — Records (Java 14+)", "linguagem": "java", "content": """Records são classes imutáveis concisas:
public record Pessoa(String nome, int idade) {}
Gera automaticamente: construtor, getters (nome(), idade()), equals, hashCode, toString. Substitui boilerplate de POJOs/DTOs. Pode ter validação compacta:
public record Pessoa(String nome, int idade) {
    public Pessoa { if (idade < 0) throw new IllegalArgumentException(); }
}"""},

    {"titulo": "Java — Optional", "linguagem": "java", "content": """Optional<T> evita NullPointerException:
Optional<User> u = repo.findById(id);
String nome = u.map(User::getNome).orElse('Anônimo');
u.ifPresent(System.out::println);
Antipadrão: NÃO use Optional como campo de classe ou parâmetro — use só como retorno."""},

    # ---- C ----
    {"titulo": "C — Ponteiros básicos", "linguagem": "c", "content": """Ponteiros guardam endereços de memória:
int x = 10;
int *p = &x;       // p aponta pra x
printf('%d', *p);  // dereferência, imprime 10
*p = 20;           // x agora é 20
Aritmética: p+1 avança sizeof(tipo) bytes. Cuidado com ponteiros não-inicializados (UB) e ponteiros pendurados (após free)."""},

    {"titulo": "C — malloc/free e memory leaks", "linguagem": "c", "content": """Alocação dinâmica:
int *arr = malloc(100 * sizeof(int));
if (!arr) { /* erro */ }
// usar...
free(arr);
arr = NULL;  // boa prática: evita uso após free
Para CADA malloc DEVE existir um free. Use ferramentas: valgrind --leak-check=full ./programa. calloc(n, size) zera memória; realloc(p, n) redimensiona."""},

    {"titulo": "C — strings e buffer overflow", "linguagem": "c", "content": """C não tem tipo string nativo — são arrays de char terminados em '\\0'.
INSEGURO: gets(buf), strcpy(buf, src), sprintf(buf, ...)
SEGURO:   fgets(buf, sizeof(buf), stdin), strncpy + null terminator manual, snprintf(buf, sizeof(buf), ...)
SEMPRE valide o tamanho do destino. Buffer overflow é a vulnerabilidade clássica em C."""},

    # ---- C++ ----
    {"titulo": "C++ — RAII e smart pointers", "linguagem": "cpp", "content": """RAII (Resource Acquisition Is Initialization): recursos vivem na stack, destrutor libera.
#include <memory>
std::unique_ptr<int> p = std::make_unique<int>(42);  // sem new
std::shared_ptr<int> s = std::make_shared<int>(10);  // contagem de referência
// liberação automática ao sair do escopo
Evite new/delete crus. unique_ptr para posse exclusiva, shared_ptr quando vários donos, weak_ptr para ciclos."""},

    {"titulo": "C++ — Move semantics", "linguagem": "cpp", "content": """Move semantics evitam cópias caras:
std::vector<int> v1 = {1,2,3};
std::vector<int> v2 = std::move(v1);  // transfere posse, v1 fica vazio
Construtor de move: T(T&& other) noexcept. Use std::move quando NÃO for usar mais o original. Em retorno por valor o compilador já aplica RVO/move."""},

    {"titulo": "C++ — Templates", "linguagem": "cpp", "content": """Templates permitem genéricos em tempo de compilação:
template<typename T>
T maximo(T a, T b) { return a > b ? a : b; }
maximo(3, 5);    // T = int
maximo(1.5, 2.0); // T = double
Concepts (C++20):
template<std::integral T> T dobro(T x) { return x*2; }"""},

    # ---- C# ----
    {"titulo": "C# — LINQ", "linguagem": "csharp", "content": """LINQ (Language Integrated Query) permite consultas em coleções:
var pares = numeros.Where(n => n % 2 == 0).Select(n => n * 2).ToList();
Sintaxe de query:
var resultado = from u in users where u.Idade > 18 orderby u.Nome select u.Email;
Funciona em IEnumerable, IQueryable (LINQ to SQL/EF). Lazy por padrão — ToList() materializa."""},

    {"titulo": "C# — async/await", "linguagem": "csharp", "content": """C# tem async/await built-in:
public async Task<string> BuscarAsync(string url) {
    using var client = new HttpClient();
    return await client.GetStringAsync(url);
}
NUNCA chame .Result ou .Wait() em código async — causa deadlock. Use Task.WhenAll para paralelizar. ConfigureAwait(false) em libraries para evitar capturar contexto."""},

    {"titulo": "C# — Records (C# 9+)", "linguagem": "csharp", "content": """Records são tipos de referência imutáveis:
public record Pessoa(string Nome, int Idade);
var p = new Pessoa('Ana', 30);
var p2 = p with { Idade = 31 };  // cópia com mudança
Equals/GetHashCode/ToString gerados. Record struct (C# 10+) para value type."""},

    # ---- GO ----
    {"titulo": "Go — Goroutines e channels", "linguagem": "go", "content": """Concorrência simples e barata em Go:
go func() { fmt.Println('async') }()  // goroutine
ch := make(chan int)
go func() { ch <- 42 }()
v := <-ch  // recebe
select {
case v := <-ch1: ...
case <-time.After(time.Second): timeout
}
Goroutines são leves (~2KB stack inicial). Use channels para comunicação. sync.WaitGroup para sincronizar."""},

    {"titulo": "Go — Error handling idiomático", "linguagem": "go", "content": """Go usa retornos de erro explícitos:
data, err := os.ReadFile('f.txt')
if err != nil {
    return fmt.Errorf('lendo arquivo: %w', err)  // %w embrulha
}
Verifique erros sempre. Use errors.Is(err, target) e errors.As(err, &targetType). NÃO ignore com _ exceto quando intencional."""},

    {"titulo": "Go — Interfaces implícitas", "linguagem": "go", "content": """Interfaces em Go são satisfeitas implicitamente:
type Writer interface { Write([]byte) (int, error) }
type MeuLogger struct{}
func (m MeuLogger) Write(p []byte) (int, error) { fmt.Print(string(p)); return len(p), nil }
// MeuLogger satisfaz Writer SEM declarar
var w Writer = MeuLogger{}  // funciona
Princípio: interfaces pequenas (1-3 métodos), declaradas no consumidor, não no produtor."""},

    # ---- PADRÕES GERAIS ----
    {"titulo": "Padrão — DRY (Don't Repeat Yourself)", "linguagem": "geral", "content": """Cada peça de conhecimento deve ter uma única representação no sistema. Quando você copia-cola código, está criando um bug futuro: ao mudar uma cópia, esquece as outras. Extraia funções, módulos, classes utilitárias. Mas cuidado com over-engineering: 2 ocorrências similares ainda podem ser coincidência."""},

    {"titulo": "Padrão — SOLID", "linguagem": "geral", "content": """5 princípios de orientação a objetos:
S - Single Responsibility: uma classe, uma razão pra mudar.
O - Open/Closed: aberto pra extensão, fechado pra modificação.
L - Liskov: subclasses devem substituir a base sem quebrar.
I - Interface Segregation: interfaces pequenas e específicas.
D - Dependency Inversion: dependa de abstrações, não de implementações concretas (use injeção de dependência)."""},

    {"titulo": "Padrão — REST API design", "linguagem": "geral", "content": """REST API básica:
GET    /users          - lista
GET    /users/:id      - obtém
POST   /users          - cria (body JSON)
PUT    /users/:id      - substitui inteiro
PATCH  /users/:id      - atualiza parcial
DELETE /users/:id      - remove
Status: 200 ok, 201 criado, 204 sem conteúdo, 400 erro do cliente, 401 sem auth, 403 proibido, 404 não encontrado, 500 erro server.
Versionamento: /v1/users. Filtros via query: ?status=active&limit=10."""},

    {"titulo": "Padrão — Git workflow básico", "linguagem": "geral", "content": """Comandos essenciais:
git init / git clone <url>
git status / git diff
git add . / git commit -m 'msg'
git pull --rebase / git push
git checkout -b feature/x  # nova branch
git merge feature/x        # ou git rebase
git log --oneline --graph
Conventional commits: feat:, fix:, docs:, refactor:, test:. Sempre commit pequenos e atômicos."""},

    # ---- FULLSTACK WEB ----
    {"titulo": "React 19 — Hooks e Patterns", "linguagem": "javascript", "content": """React 19 traz melhorias de performance e novos hooks.
Hooks essenciais:
- useState: const [count, setCount] = useState(0)
- useEffect: executa side effects (fetch, subscriptions). Sempre limpe no return.
- useContext: acesso a contextos sem Consumer.
- useCallback / useMemo: memoize funções e valores para performance.
- useRef: referência mutável que não dispara re-render (acessar DOM, timers).
Padrões:
- Custom Hooks: extraia lógica reutilizável (useFetch, useLocalStorage).
- Compound Components: componentes que trabalham juntos (Tabs, Select).
- Render Props / HOCs: menos usados hoje, preferir composição com children."""},

    {"titulo": "React 19 — Server Components e Suspense", "linguagem": "javascript", "content": """Server Components (RSC) rodam no servidor, não enviam JS pro cliente:
- Acesso direto a banco de dados, APIs internas, file system.
- Não podem usar useState, useEffect, event handlers (só Client Components).
- Next.js App Router usa RSC por padrão.
Suspense:
- <Suspense fallback={<Loading />}><ComponentAsync /></Suspense>
- Permite streaming de HTML — o servidor envia partes da página conforme ficam prontas.
- useTransition: marca updates como não-urgentes (ex: filtro de lista)."""},

    {"titulo": "Next.js 15 — App Router e Data Fetching", "linguagem": "javascript", "content": """Next.js 15 com App Router (app/):
- Layouts aninhados: app/layout.tsx aplica em todas as páginas filhas.
- Rotas dinâmicas: app/blog/[slug]/page.tsx — params recebido como prop.
- Server Actions: funções async que rodam no servidor, chamadas direto do client:
  'use server'
  async function createPost(formData: FormData) { ... }
- Data fetching: fetch() é automaticamente cacheado; use { cache: 'no-store' } para dados dinâmicos.
- Revalidação: revalidatePath('/') ou revalidateTag('posts') para ISR.
- Middleware: middleware.ts na raiz para auth, redirects, headers."""},

    {"titulo": "TypeScript — Fundamentos para Web", "linguagem": "typescript", "content": """TypeScript essencial para projetos modernos:
Tipos básicos: string, number, boolean, null, undefined, any, unknown, never.
Interfaces vs Types:
  interface User { id: number; name: string; }
  type User = { id: number; name: string; }
  // Interface permite merge (declaration merging), type permite unions.
Generics:
  function identidade<T>(arg: T): T { return arg; }
  const lista = useState<string[]>([]);
Utility Types:
  Partial<T>, Required<T>, Pick<T, K>, Omit<T, K>, Record<K, T>
Strict mode: tsconfig.json { "strict": true } — detecta null/undefined, implicit any, etc.
Dicas: use unknown em vez de any; use satisfies para validar tipos sem mudar o tipo inferido."""},

    {"titulo": "Tailwind CSS — Utility-First e Design System", "linguagem": "css", "content": """Tailwind CSS é um framework utility-first:
- Classes atômicas: flex, justify-center, bg-blue-500, p-4, rounded-lg
- Responsivo: sm:, md:, lg:, xl: prefixos (mobile-first)
- Estados: hover:, focus:, active:, disabled:, dark:
- Componentes com @apply (ou melhor, extrair em componentes React):
  .btn-primary { @apply px-4 py-2 bg-blue-500 text-white rounded; }
Configuração: tailwind.config.js para customizar cores, fontes, breakpoints, plugins.
Dica: use o plugin tailwindcss-animate para animações simples e @tailwindcss/typography para prose."""},

    {"titulo": "FastAPI — APIs Python Modernas", "linguagem": "python", "content": """FastAPI é um framework moderno para APIs em Python:
from fastapi import FastAPI
app = FastAPI()
@app.get('/items/{item_id}')
async def read_item(item_id: int, q: str | None = None):
    return {'item_id': item_id, 'q': q}
Benefícios:
- Async nativo (async/await) — alta performance em I/O.
- Validação automática com Pydantic models.
- Documentação automática: /docs (Swagger UI) e /redoc.
- Dependency Injection: Depends() para reutilizar lógica (DB, auth).
- Background tasks: BackgroundTasks para jobs não-bloqueantes.
Estrutura recomendada:
  app/
  ├── main.py
  ├── routers/
  ├── models.py (Pydantic)
  ├── database.py
  └── dependencies.py"""},

    {"titulo": "Node.js / Express — APIs REST", "linguagem": "javascript", "content": """Express é o framework minimalista mais popular para Node.js:
const express = require('express');
const app = express();
app.use(express.json());
app.get('/users', (req, res) => { res.json(users); });
app.post('/users', (req, res) => { ... });
app.listen(3000);
Middlewares:
- app.use(cors()) para CORS
- app.use(helmet()) para headers de segurança
- app.use(morgan('dev')) para logging
- Middleware custom: const auth = (req, res, next) => { ...; next(); }
Estrutura de projeto:
  src/
  ├── controllers/
  ├── routes/
  ├── middlewares/
  ├── models/
  └── app.js
Dica: use Zod para validação de schemas e dotenv para variáveis de ambiente."""},

    {"titulo": "Prisma ORM — Type-Safe Database", "linguagem": "typescript", "content": """Prisma é um ORM moderno para Node.js/TypeScript:
schema.prisma:
  generator client { provider = 'prisma-client-js' }
  datasource db { provider = 'postgresql' url = env('DATABASE_URL') }
  model User { id Int @id @default(autoincrement()) email String @unique name String? posts Post[] }
Comandos:
  npx prisma migrate dev --name init
  npx prisma generate
  npx prisma studio
Uso:
  import { PrismaClient } from '@prisma/client'
  const prisma = new PrismaClient()
  const users = await prisma.user.findMany({ include: { posts: true } })
Vantagens: type-safe queries, migrations automáticas, Prisma Studio (GUI), suporte a PostgreSQL, MySQL, MongoDB, SQLite."""},

    # ---- MOBILE ----
    {"titulo": "React Native — Fundamentos e Expo", "linguagem": "javascript", "content": """React Native cria apps nativos com React:
- Componentes nativos: View, Text, Image, ScrollView, FlatList (virtualização)
- Estilos: StyleSheet.create({ ... }) — baseado em CSS mas com camelCase
- Navegação: @react-navigation/native com stack, tab, drawer navigators
- Expo: framework que simplifica React Native — não precisa configurar Android/iOS nativo.
  npx create-expo-app MeuApp
  npx expo start
Hooks mobile:
- useColorScheme() para dark/light mode
- useWindowDimensions() para responsivo
- Platform.OS para código específico ('ios' | 'android')
Performance:
- FlatList em vez de ScrollView para listas longas (lazy rendering)
- useMemo/useCallback para otimizar renders
- Hermes engine (ativado por padrão no Expo) para startup rápido"""},

    {"titulo": "Flutter — Widgets e State Management", "linguagem": "dart", "content": """Flutter usa widgets como blocos de construção:
- StatelessWidget: imutável, só depende de props
- StatefulWidget: mantém estado com setState()
- InheritedWidget / Provider / Riverpod / Bloc: state management
Estrutura de projeto:
  lib/
  ├── main.dart
  ├── screens/
  ├── widgets/
  ├── models/
  └── services/
Widgets essenciais:
  Scaffold (estrutura), AppBar, Column, Row, Stack, ListView, GridView
  GestureDetector, InkWell (toques), FutureBuilder, StreamBuilder
Navegação:
  Navigator.push(context, MaterialPageRoute(builder: (_) => DetailPage()))
  // ou GoRouter para URLs declarativas
Comandos:
  flutter create meu_app
  flutter run
  flutter build apk / flutter build ios"""},

    {"titulo": "PWA — Progressive Web Apps", "linguagem": "javascript", "content": """PWAs são sites que funcionam como apps nativos:
Requisitos:
- HTTPS (service workers precisam)
- Web App Manifest (manifest.json): nome, ícones, theme, display mode
- Service Worker: cache de assets, offline support, push notifications
Criar PWA com React:
  npx create-react-app meu-pwa --template cra-template-pwa
  // ou Next.js com next-pwa plugin
Recursos:
- Install prompt: usuário pode "instalar" no home screen
- Background sync: sincroniza dados quando online
- Push API: notificações push (com server de notificações)
Lighthouse no Chrome DevTools audita PWA e dá score de 0-100."""},

    # ---- DEVOPS / FERRAMENTAS ----
    {"titulo": "Docker — Containers para Desenvolvimento", "linguagem": "geral", "content": """Docker containeriza aplicações:
Dockerfile exemplo para Node.js:
  FROM node:20-alpine
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci
  COPY . .
  EXPOSE 3000
  CMD [\"node\", \"server.js\"]
Comandos:
  docker build -t meu-app .
  docker run -p 3000:3000 meu-app
  docker-compose up -d  # para múltiplos serviços
Docker Compose (docker-compose.yml):
  services:
    app: { build: ., ports: ['3000:3000'] }
    db: { image: postgres:15, environment: { POSTGRES_PASSWORD: secret } }
Dica: multi-stage builds para imagens menores (build em uma stage, runtime em outra)."""},

    {"titulo": "SEO — Fundamentos para Web", "linguagem": "geral", "content": """SEO (Search Engine Optimization) essencial:
On-page:
- <title> único e descritivo em cada página
- <meta name='description'> com resumo relevante
- Headings hierárquicos: h1 (1 por página), h2, h3...
- Alt text em imagens
- URLs amigáveis (slug) e canonical tags
- Structured Data (JSON-LD): Schema.org para rich snippets
Performance:
- Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1
- Lazy loading de imagens (loading='lazy')
- Compressão gzip/brotli, imagens WebP/AVIF
Next.js SEO:
  import { Metadata } from 'next'
  export const metadata: Metadata = { title: '...', description: '...' }
  // ou generateMetadata() para dados dinâmicos"""},
]


def main():
    db_url = os.environ.get("SUPABASE_DB_URL")
    print(f"[seed] Supabase DB: {'configurado' if db_url else 'NÃO configurado, usando fallback local'}")

    llm = LLMRouter(
        provider="ollama",
        model=os.environ.get("OLLAMA_MODEL", "llama3.1"),
        ollama_url=os.environ.get("OLLAMA_URL", "http://localhost:11434"),
    )
    rag = RAGStore(database_url=db_url or None)
    print(f"[seed] Backend RAG: {rag.backend}")

    rag.clear_collection("programacao")
    contents = [item["content"] for item in PROGRAMMING_KNOWLEDGE]
    print(f"[seed] gerando embeddings para {len(contents)} documentos...")
    embs = llm.embed(contents)
    for item, emb in zip(PROGRAMMING_KNOWLEDGE, embs):
        rag.add(
            item["content"], emb,
            collection="programacao",
            metadata={"titulo": item["titulo"], "linguagem": item["linguagem"]},
        )
    print(f"[seed] OK — {len(contents)} documentos inseridos na coleção 'programacao'.")
    print(f"[seed] Coleções: {rag.list_collections()}")


if __name__ == "__main__":
    main()
