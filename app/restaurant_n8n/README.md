# n8n + Ajax para Restaurante

Sistema de atendimento automatico 24h para restaurantes usando n8n (automação) + Ajax (IA).

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `guia-n8n-restaurante.html` | Guia completo em HTML (abra no navegador) |
| `teste-web.html` | Simulador web para testar o atendimento |
| `fluxo-reservas.json` | Fluxo n8n importavel |

## Teste Rápido

1. Abra `teste-web.html` no navegador
2. Clique nas sugestões ou digite sua pergunta
3. Veja como o atendimento automatico responde!

## Instalação do n8n

```bash
docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n
```

Acesse: http://localhost:5678

## Como Usar

1. Inicie o n8n
2. Importe o fluxo `fluxo-reservas.json`
3. Configure o webhook no WhatsApp/Instagram
4. Pronto! Seu restaurante atende 24h automaticamente

## Benefícios

- Atendimento 24h sem funcionarios extras
- Nunca perde um lead
- Reservas automaticas
- Pedidos pelo WhatsApp
- Custo baixo (R$ 50-200/mes vs R$ 3000+ com funcionarios)
