# DJEN Monitor

> Painel de consulta de publicações judiciais via API Comunica PJe.  
> Frontend estático + Serverless Function Python hospedados na **Vercel**.

---

## Sumário

1. [Estrutura do Projeto](#estrutura-do-projeto)
2. [Como Funciona](#como-funciona)
3. [Deploy na Vercel — Passo a Passo](#deploy-na-vercel--passo-a-passo)
4. [Desenvolvimento Local](#desenvolvimento-local)
5. [A Serverless Function](#a-serverless-function)
6. [A API Comunica PJe](#a-api-comunica-pje)
7. [Solução de Problemas](#solução-de-problemas)
8. [Próximos Passos](#próximos-passos)

---

## Estrutura do Projeto

```
djen-monitor/
│
├── public/
│   └── index.html          # Painel web completo (HTML + CSS + JS em um arquivo)
│
├── api/
│   └── v1/
│       └── comunicacao.py  # Serverless Function: proxy para a API PJe
│
├── vercel.json             # Configuração de rotas e builds da Vercel
├── requirements.txt        # Dependências Python (vazio — usa só stdlib)
├── .gitignore
└── README.md
```

---

## Como Funciona

O browser **nunca chama a API PJe diretamente** — isso causaria erro de CORS.
Em vez disso, chama `/api/v1/comunicacao` que é executado na Vercel como função Python:

```
[Browser]
    │
    │  GET /api/v1/comunicacao?numeroOab=307844&ufOab=SP&...
    ▼
[Vercel — comunicacao.py]          ← executa server-side, sem CORS
    │
    │  GET https://comunicaapi.pje.jus.br/api/v1/comunicacao?...
    ▼
[API Comunica PJe]
    │
    │  { "items": [...], "count": 42 }
    ▼
[Vercel — devolve ao browser]
    │
    ▼
[Browser renderiza a tabela]
```

---

## Deploy na Vercel — Passo a Passo

### Pré-requisitos

- Conta no **GitHub**: https://github.com
- Conta na **Vercel**: https://vercel.com (login com a conta GitHub)
- **Git** instalado localmente

Verificar se Git está instalado:
```bash
git --version
# git version 2.x.x
```

---

### 1. Criar o repositório no GitHub

**Opção A — pelo site (mais fácil):**

1. Acesse https://github.com/new
2. Preencha:
   - **Repository name:** `djen-monitor`
   - **Visibility:** Private ✅ (recomendado — contém OABs do escritório)
   - Deixe desmarcado "Add README" e "Add .gitignore"
3. Clique em **Create repository**
4. Copie a URL que aparecer (ex: `https://github.com/seu-usuario/djen-monitor.git`)

---

### 2. Subir os arquivos pelo terminal

Abra o terminal na pasta do projeto e execute:

```bash
# Entre na pasta do projeto
cd caminho/para/djen-monitor

# Inicia o repositório Git local
git init

# Adiciona todos os arquivos
git add .

# Primeiro commit
git commit -m "feat: painel DJEN Monitor com proxy Vercel"

# Conecta ao repositório do GitHub (substitua pela URL copiada no passo 1)
git remote add origin https://github.com/seu-usuario/djen-monitor.git

# Sobe os arquivos
git push -u origin main
```

> Se aparecer erro `error: src refspec main does not match any`, rode:
> ```bash
> git branch -M main
> git push -u origin main
> ```

Confirme no GitHub que os arquivos aparecem no repositório.

---

### 3. Importar na Vercel

1. Acesse https://vercel.com/dashboard
2. Clique em **"Add New… → Project"**
3. Na lista de repositórios, localize **`djen-monitor`** e clique em **"Import"**
4. Na tela de configuração:
   - **Framework Preset:** `Other`
   - **Root Directory:** `.` (deixe o padrão)
   - **Build & Output Settings:** deixe tudo em branco
   - **Environment Variables:** não precisa por enquanto
5. Clique em **"Deploy"**

A Vercel vai:
- Detectar o `vercel.json`
- Fazer build do `public/index.html` como estático
- Registrar `api/v1/comunicacao.py` como Serverless Function Python
- Gerar uma URL pública (ex: `https://djen-monitor.vercel.app`)

O deploy leva cerca de **1–2 minutos**.

---

### 4. Testar o deploy

**Teste a função proxy diretamente no browser:**

```
https://djen-monitor.vercel.app/api/v1/comunicacao?numeroOab=307844&ufOab=SP&page=0&size=5
```

Deve retornar um JSON da API PJe. Se retornar `{"items": [], "count": 0}`, a função está funcionando — apenas não há publicações para esse filtro.

**Acesse o painel:**

```
https://djen-monitor.vercel.app
```

---

### 5. Deploy automático (a partir de agora)

Qualquer `git push` para a branch `main` dispara um novo deploy automaticamente:

```bash
# Depois de alterar qualquer arquivo:
git add .
git commit -m "fix: ajuste no painel"
git push
# → Vercel detecta, faz build e publica em ~1 min
```

A URL não muda.

---

## Desenvolvimento Local

Para testar sem fazer deploy a cada mudança, use o **Vercel CLI**:

### Instalar Vercel CLI

```bash
npm install -g vercel
```

### Autenticar

```bash
vercel login
# Abre o browser para login com a conta Vercel
```

### Rodar localmente

```bash
cd djen-monitor
vercel dev
```

O terminal mostra:
```
> Ready! Available at http://localhost:3000
```

O ambiente local replica exatamente o que vai rodar na Vercel:
- `http://localhost:3000` → serve `public/index.html`
- `http://localhost:3000/api/v1/comunicacao?...` → executa `comunicacao.py`

> **Sem Vercel CLI:** você também pode usar o `servidor.py` dos arquivos anteriores
> para testes locais rápidos — ele simula o mesmo comportamento.

---

## A Serverless Function

**Arquivo:** `api/v1/comunicacao.py`

A Vercel detecta automaticamente qualquer arquivo `.py` dentro de `api/` e o expõe
como endpoint HTTP. O caminho do arquivo vira a rota:

```
api/v1/comunicacao.py  →  /api/v1/comunicacao
```

A classe deve se chamar `handler` e herdar de `BaseHTTPRequestHandler`:

```python
from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json

API_BASE = "https://comunicaapi.pje.jus.br"

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Lê os query params (ex: ?numeroOab=307844&ufOab=SP&page=0&size=100)
        parsed = urllib.parse.urlparse(self.path)
        query  = parsed.query

        # Monta URL da API real
        target = f"{API_BASE}/api/v1/comunicacao?{query}"

        # Faz a requisição server-side (sem CORS)
        req = urllib.request.Request(target, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read()

        # Devolve ao browser
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
```

### Limites da Vercel (plano gratuito)

| Recurso | Limite gratuito |
|---------|----------------|
| Execuções/mês | 100.000 |
| Duração máxima por execução | 10 segundos |
| Memória | 1024 MB |
| Bandwidth | 100 GB/mês |

> ⚠️ **Atenção ao timeout de 10s.** Se uma OAB tiver muitas publicações com várias
> páginas, a função pode ultrapassar esse limite. Ver seção [Solução de Problemas](#solução-de-problemas).

---

## A API Comunica PJe

### Endpoint

```
GET https://comunicaapi.pje.jus.br/api/v1/comunicacao
```

### Parâmetros

| Parâmetro | Tipo | Descrição | Exemplo |
|-----------|------|-----------|---------|
| `numeroOab` | string | Número da OAB | `307844` |
| `ufOab` | string | UF da OAB | `SP` |
| `numeroProcesso` | string | Nº completo sem máscara | `00003466320248260210` |
| `dataDisponibilizacaoInicio` | string | Data inicial YYYY-MM-DD | `2026-05-19` |
| `dataDisponibilizacaoFim` | string | Data final YYYY-MM-DD | `2026-05-19` |
| `page` | integer | Página (começa em 0) | `0` |
| `size` | integer | Itens por página (max 100) | `100` |

### Resposta

```json
{
  "count": 42,
  "items": [
    {
      "id": "abc123",
      "numeroProcesso": "0001234-56.2024.8.26.0100",
      "tipoComunicacao": "Intimação",
      "dataDisponibilizacao": "2026-05-18T00:00:00",
      "nomeDestinatario": "JOAO DA SILVA",
      "nomeOrgao": "1ª Vara Cível - TJ-SP",
      "texto": "<p>Conteúdo da publicação...</p>"
    }
  ]
}
```

---

## Solução de Problemas

### Erro 504 — Function timeout

**Causa:** A busca retornou muitas páginas e ultrapassou os 10s do plano gratuito.

**Solução:** Reduza o intervalo de datas ou o número de OABs por busca. Para buscas
grandes, use o `servidor.py` localmente (sem limite de tempo).

Para contornar no futuro: migrar para Vercel Pro (60s) ou Railway (sem limite).

---

### Erro 500 na função

**Verifique os logs da Vercel:**

1. Acesse https://vercel.com/dashboard
2. Clique no projeto → **"Functions"**
3. Clique na função `comunicacao` → veja os logs de erro

---

### O painel abre mas a busca não retorna dados

Teste a função diretamente:
```
https://seu-projeto.vercel.app/api/v1/comunicacao?numeroOab=307844&ufOab=SP&page=0&size=5
```

- Se retornar JSON → a função está ok, verifique os parâmetros
- Se retornar erro HTML da Vercel → problema no deploy, veja os logs

---

### `vercel dev` não encontra Python

```bash
# Instale Python 3 e garanta que está no PATH
python3 --version

# No Windows, pode ser necessário usar:
python --version
```

---

### Push rejeitado pelo GitHub

```bash
# Se a branch local não for 'main':
git branch -M main
git push -u origin main

# Se o repositório já tiver commits (conflito):
git pull origin main --allow-unrelated-histories
git push
```

---

## Próximos Passos

| Melhoria | O que fazer |
|----------|-------------|
| **Autenticação** | Adicionar senha simples com Vercel Environment Variables |
| **Histórico** | Integrar Vercel KV (Redis) ou PlanetScale (MySQL) para salvar buscas |
| **Notificação** | Vercel Cron Jobs (plano Pro) para busca diária automática + e-mail via Resend |
| **Múltiplos usuários** | Adicionar login com NextAuth ou Clerk |
| **Escala** | Migrar backend para Railway com FastAPI + PostgreSQL |

### Adicionar variável de ambiente na Vercel

Para guardar tokens ou configurações sem expor no código:

1. Vercel Dashboard → Projeto → **Settings → Environment Variables**
2. Adicione: `PJE_TOKEN` = `seu_valor`
3. Em `comunicacao.py`:

```python
import os
token = os.environ.get("PJE_TOKEN", "")
```

---

## Referências

- Vercel Serverless Functions (Python): https://vercel.com/docs/functions/runtimes/python
- Vercel CLI: https://vercel.com/docs/cli
- API Comunica PJe: https://comunicaapi.pje.jus.br
- Git — guia rápido: https://training.github.com/downloads/pt_BR/github-git-cheat-sheet/
