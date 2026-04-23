"""Seed the RAG with curated programming knowledge: Python, Java, C, C++, C#, Go.

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
]


def main():
    db_url = os.environ.get("SUPABASE_DB_URL")
    print(f"[seed] Supabase DB: {'configurado' if db_url else 'NÃO configurado, usando fallback local'}")

    llm = LLMRouter(
        provider="openrouter",
        openrouter_key=os.environ.get("OPENROUTER_API_KEY"),
        model=os.environ.get("OPENROUTER_MODEL", "openrouter/auto"),
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
