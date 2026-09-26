# Obsidian MCP Server 

Um servidor [Model Context Protocol (MCP)](https://modelcontextprotocol.io) que conecta seu vault Obsidian diretamente ao Claude e Cursor, permitindo que você gerencie seus to-dos sem reescrever tarefas.

**Versão em inglês:** [README.en.md](README.en.md)

## O que é MCP?

O **Model Context Protocol** é um protocolo aberto que permite integrar ferramentas externas (como seu Obsidian) com IAs (Claude, Cursor, etc). Pense nele como um "adaptador universal" que diz ao Claude: "Ei, você pode usar essas ferramentas para acessar meus to-dos no Obsidian".

Sem MCP, você teria que copiar e colar suas tarefas toda vez. Com MCP, o Claude acessa direto.

## Funcionalidades

- ✅ **Listar todos os to-dos** do seu vault Obsidian automaticamente
- ✅ **Marcar tarefas como completas** diretamente via Claude/Cursor
- ✅ **Ler notas inteiras** para contexto
- ✅ **Funciona com Claude Desktop** e **Cursor** simultaneamente
- ✅ Busca recursiva em todas as pastas
- ✅ Suporte a checkboxes padrão Obsidian (`- [ ]` e `- [x]`)

## Estrutura do Projeto

```
obsidian-mcp-server/
├── src/
│   ├── __init__.py              # Marca a pasta como pacote Python
│   └── obsidian_mcp.py          # Servidor MCP principal (arquivo crítico)
│
├── venv/                        # Ambiente virtual Python (ignorado no git)
│
├── requirements.txt             # Dependências do projeto
├── .env.example                 # Modelo de configuração
├── .gitignore                   # Arquivos ignorados no git
├── README.md                    # Documentação em português
├── README.en.md                 # Documentação em inglês
└── setup.py                     # Metadados do pacote (opcional)
```

### 📄 O que cada arquivo faz:

| Arquivo | Função |
|---------|--------|
| `src/obsidian_mcp.py` | **Coração do projeto**. Define as 3 ferramentas: `get_todos`, `get_note_content`, `update_todo`. Usa `MCPServer` para comunicar com Claude/Cursor via protocolo MCP |
| `venv/bin/python3` | Python isolado com pacotes MCP instalados. Quando Claude chama o servidor, executa este Python |
| `requirements.txt` | Lista pacotes: `mcp>=0.2.0` e `python-dotenv>=1.0.0`. Instalados com `pip install -r requirements.txt` |
| `.env` | Seu arquivo local (não commitado) com `OBSIDIAN_VAULT_PATH=/Users/você/Documents` |
| `claude_desktop_config.json` | Config que Claude Desktop lê em `~/Library/Application Support/Claude/` para conhecer o servidor |
| `mcp.json` | Config que Cursor lê em `~/.cursor/` para conhecer o servidor |

## 🛠️ Instalação

### Pré-requisitos

- macOS (testado em 11.0+)
- Python 3.11 ou superior
- Homebrew (para instalar Python)
- Claude Desktop ou Cursor instalados
- Um vault Obsidian existente

### Passo 1: Clone ou Crie o Projeto


```bash
# Se clonando do GitHub:
git clone git@github.com:SEU-USUARIO/obsidian-mcp.git
cd obsidian-mcp

# Ou crie do zero:
mkdir obsidian-mcp
cd obsidian-mcp
```

### Passo 2: Crie o Ambiente Virtual Python

```bash
python3.11 -m venv venv
source venv/bin/activate
```

Seu prompt deve aparecer assim:
```
(venv) obsidian-mcp %
```

### Passo 3: Instale as Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Isso instala:
- `mcp` (2.2.0+) — o protocolo MCP
- `python-dotenv` — para ler variáveis de ambiente

### Passo 4: Crie o Arquivo `.env`

```bash
# Copie o template:
cp .env.example .env

# Abra e substitua o caminho:
nano .env
```

Encontre o caminho do seu vault:
1. Abra Obsidian
2. Vá em **Configurações** → **Sobre**
3. Procure por **Vault location:**
4. Copie o caminho completo e cole no `.env`

Exemplo:
```env
OBSIDIAN_VAULT_PATH=/Users/pauline/Documents/MeuVault
```

Salve (Ctrl+X, depois `y` e Enter).

### Passo 5: Teste o Servidor Localmente

```bash
python3 src/obsidian_mcp.py
```

Se funcionar, o terminal fica esperando (nenhum erro deve aparecer). Aperte **Ctrl+C** para sair.

## ⚙️ Configuração (Claude Desktop + Cursor)

### Claude Desktop

1. Crie a pasta de configuração:
```bash
mkdir -p ~/Library/Application\ Support/Claude
```

2. Crie o arquivo `claude_desktop_config.json`:
```bash
cat > ~/Library/Application\ Support/Claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "obsidian-mcp": {
      "command": "/caminho/completo/obsidian-mcp/venv/bin/python3",
      "args": [
        "/caminho/completo/obsidian-mcp/src/obsidian_mcp.py"
      ],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/Users/seu-usuario/Documents/seu-vault"
      }
    }
  }
}
EOF
```

**Substitua:**
- `/caminho/completo/obsidian-mcp` → o caminho real (ex: `/Users/pauline/Documents/obsidian-mcp`)
- `/Users/seu-usuario/Documents/seu-vault` → seu vault

3. Reinicie Claude Desktop (Cmd+Q e abra de novo)

### Cursor

1. Crie a pasta:
```bash
mkdir -p ~/.cursor
```

2. Crie o arquivo `mcp.json`:
```bash
cat > ~/.cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "obsidian-mcp": {
      "command": "/caminho/completo/obsidian-mcp/venv/bin/python3",
      "args": [
        "/caminho/completo/obsidian-mcp/src/obsidian_mcp.py"
      ],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/Users/seu-usuario/Documents/seu-vault"
      }
    }
  }
}
EOF
```

3. Reinicie Cursor (Cmd+Q e abra de novo)

## 💬 Como Usar

### No Claude Desktop

Abra uma conversa e pergunte qualquer coisa relacionada a tarefas:

```
Quais são meus to-dos no Obsidian?
```

Claude vai:
1. Chamar a ferramenta `get_todos`
2. Receber JSON com todas as tarefas (167 no seu caso!)
3. Formatar e exibir de forma legível

Também pode fazer:
```
Marca como completa a tarefa "Fazer o deploy" no arquivo Projects/projeto-x.md na linha 5
```

Claude vai chamar `update_todo` automaticamente.

### No Cursor

Acesse a aba do Claude (lado esquerdo) e faça as mesmas perguntas. O comportamento é idêntico.

## 🔍 Como Funciona por Dentro

```
Claude/Cursor (IAs)
       ↓
claude_desktop_config.json / mcp.json (configs)
       ↓
Executor do SO (lê config e roda comando Python)
       ↓
/venv/bin/python3 src/obsidian_mcp.py (servidor rodando)
       ↓
MCPServer ("escuta" requisições MCP)
       ↓
Funções decoradas com @mcp.tool():
  - get_todos()         → Varre .rglob("*.md"), extrai checkboxes
  - get_note_content()  → Abre arquivo e retorna conteúdo
  - update_todo()       → Escreve [ ] ou [x] e salva arquivo
       ↓
Respostas JSON
       ↓
Claude/Cursor exibe para você
```

## 📝 Estrutura do Código

### `src/obsidian_mcp.py` - A Joia da Coroa

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("obsidian-mcp")

@mcp.tool()
def get_todos(folder: Optional[str] = None) -> str:
    """Ferramenta 1: Lista todos os to-dos"""
    # Varre vault_path recursivamente com .rglob("*.md")
    # Procura linhas com "- [ ]" ou "- [x]"
    # Retorna JSON com {file, line, completed, text}

@mcp.tool()
def get_note_content(note_path: str) -> str:
    """Ferramenta 2: Lê nota inteira"""
    # Abre arquivo e retorna conteúdo puro

@mcp.tool()
def update_todo(note_path: str, line_number: int, completed: bool) -> str:
    """Ferramenta 3: Marca tarefa como feita/não feita"""
    # Lê arquivo, substitui [ ] por [x] (ou vice-versa), salva

if __name__ == "__main__":
    mcp.run()  # Inicia servidor MCP via stdio
```

### Fluxo de uma Tarefa

1. **Usuário**: "Me mostra meus to-dos"
2. **Claude**: Chama `get_todos()` via MCP
3. **Servidor** (seu código):
   - Lê variável `OBSIDIAN_VAULT_PATH`
   - Percorre todas as pastas com `.rglob("*.md")`
   - Para cada arquivo, busca linhas com `"- [ ]"` ou `"- [x]"`
   - Retorna JSON: `{"todos": [...], "count": 167}`
4. **Claude**: Recebe JSON, formata bonito e mostra
5. **Você**: Vê seus 167 to-dos listados

## 🐛 Troubleshooting

### "Não tenho acesso ao seu Obsidian"

Significa que Claude não conseguiu conectar ao servidor. Verifique:

1. **Arquivo de config existe?**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Caminho do Python está correto?**
   ```bash
   ls /caminho/que/voce/colocou/venv/bin/python3
   ```
   Se não existir, use o caminho real (rode `which python3` dentro do venv ativado)

3. **Vault path está correto?**
   ```bash
   ls /Users/seu-usuario/seu-vault
   ```

4. **Reiniciou o Claude Desktop após editar config?**

### "ModuleNotFoundError: No module named 'mcp'"

Significa que está rodando o Python errado (não o do venv). Verifique o caminho em `claude_desktop_config.json`:

```bash
# Deve ser ESTE:
/Users/pauline/Documents/obsidian-mcp/venv/bin/python3

# Não este:
python3.11
```

## 📚 Recursos

- [Model Context Protocol - Documentação Oficial](https://modelcontextprotocol.io)
- [Python MCP SDK](https://py.sdk.modelcontextprotocol.io)
- [Claude Desktop Setup](https://support.anthropic.com/en/articles/8784710-claude-desktop)
- [Obsidian API](https://docs.obsidian.md/)

# Exemplos de Uso - Filtros Avançados

Este documento mostra como usar as 3 formas de filtro no Obsidian MCP Server.

---

## 1️⃣ Tags Inline (`#tag`)

### Arquivo: `Projects/oloroke-notes.md`

```markdown
# Melhorias Oloroke

- [ ] Implementar autenticação OAuth #urgente #backend
- [ ] Melhorar performance do carrossel #performance #frontend
- [ ] Adicionar testes unitários #testing #backend
- [x] Revisar UI/UX #design #completed
- [ ] Documentar API #documentation #backend
```

### Como chamar no Claude:

```
Me mostre todas as tarefas com tag #urgente do oloroke
```

Claude automaticamente chama:
```python
get_todos(folder="Projects/oloroke-notes", tag="urgente")
```

Retorna:
```json
{
  "todos": [
    {
      "file": "Projects/oloroke-notes.md",
      "line": 2,
      "completed": false,
      "text": "Implementar autenticação OAuth",
      "tags": ["urgente", "backend"],
      "priority": null,
      "project": null
    }
  ],
  "count": 1
}
```

### Exemplos de perguntas:

```
Quais tarefas têm #backend?
Mostre as tarefas com #testing
Me execute todas as tarefas #urgente do oloroke
```

---

## 2️⃣ Prioridade com Emoji (`🔴🟡🟢⚫`)

### Arquivo: `Projects/oloroke-notes.md`

```markdown
# Melhorias Oloroke

- [ ] 🔴 Implementar autenticação OAuth
- [ ] 🟡 Melhorar performance do carrossel
- [ ] 🟢 Adicionar testes unitários
- [x] 🔵 Revisar UI/UX
- [ ] 🟡 Documentar API
- [ ] ⚫ Migração do banco de dados (bloqueado)
```

### Legenda de Emojis:

| Emoji | Significado | Flag |
|-------|-------------|------|
| 🔴 | Alta prioridade | `priority="high"` |
| 🟡 | Média prioridade | `priority="medium"` |
| 🟢 | Baixa prioridade | `priority="low"` |
| ⚫ | Bloqueado | `priority="blocked"` |

### Como chamar no Claude:

```
Me mostre as tarefas com prioridade alta do oloroke
```

Claude automaticamente chama:
```python
get_todos(folder="Projects/oloroke-notes", priority="high")
```

Retorna:
```json
{
  "todos": [
    {
      "file": "Projects/oloroke-notes.md",
      "line": 2,
      "completed": false,
      "text": "Implementar autenticação OAuth",
      "tags": [],
      "priority": "high",
      "project": null
    }
  ],
  "count": 1
}
```

### Exemplos de perguntas:

```
Quais são as tarefas vermelhas (🔴)?
Me mostre tudo que está bloqueado (⚫)
Execute as tarefas com prioridade média
```

---

## 3️⃣ YAML Frontmatter (Mais Estruturado)

### Arquivo: `Projects/oloroke-notes.md`

```markdown
---
projeto: oloroke
prioridade: alta
tags: [urgente, backend]
responsavel: Pauline
deadline: 2024-12-31
---

# Melhorias Oloroke

- [ ] Implementar autenticação OAuth
- [ ] Melhorar performance do carrossel
- [x] Revisar UI/UX

---
projeto: oloroke
prioridade: média
tags: [testing, refactor]
---

## Testes e Refactor

- [ ] Adicionar testes unitários
- [ ] Limpar código legado
```

### Estrutura do Frontmatter:

```yaml
---
projeto: nome-do-projeto          # Identifica o projeto
prioridade: alta|média|baixa      # Prioridade geral da nota
tags: [tag1, tag2, tag3]          # Tags aplicadas a TODOS os to-dos
responsavel: Nome da Pessoa        # Quem é responsável
deadline: YYYY-MM-DD              # Prazo (você pode usar para filtrar)
---
```

### Como chamar no Claude:

```
Me mostre todas as tarefas do projeto oloroke com prioridade alta
```

Claude chama:
```python
get_todos(folder="Projects/oloroke-notes", priority="high")
```

Retorna:
```json
{
  "todos": [
    {
      "file": "Projects/oloroke-notes.md",
      "line": 0,
      "completed": false,
      "text": "Implementar autenticação OAuth",
      "tags": ["urgente", "backend"],
      "priority": "high",
      "project": "oloroke"
    },
    {
      "file": "Projects/oloroke-notes.md",
      "line": 1,
      "completed": false,
      "text": "Melhorar performance do carrossel",
      "tags": ["urgente", "backend"],
      "priority": "high",
      "project": "oloroke"
    }
  ],
  "count": 2
}
```

### Exemplos de perguntas:

```
Quais tarefas do projeto oloroke existem?
Me mostre tudo sobre o projeto terreiro-app
Execute as tarefas do projeto petlove com prioridade alta
```

---

## 🎯 Combinando Todos os Métodos

### Arquivo: `Projects/oloroke-notes.md`

```markdown
---
projeto: oloroke
tags: [oloroke, app]
---

# Oloroke - Tarefas Prioritárias

## Backend

- [ ] 🔴 Implementar autenticação OAuth #urgente #backend
- [ ] 🟡 Melhorar performance do carrossel #performance #backend
- [ ] 🟢 Adicionar testes unitários #testing

## Frontend

- [ ] 🔴 Revisar design da interface #urgente #design
- [ ] 🟡 Implementar dark mode #ui #frontend
- [ ] ⚫ Migração para TypeScript #blocked #refactor
```

Aqui você tem:
1. **Frontmatter**: Identifica projeto `oloroke` e tags gerais
2. **Tags inline**: Especifica `#urgente`, `#backend`, `#testing`, etc
3. **Emoji**: Mostra prioridade visual `🔴🟡🟢⚫`

### Exemplos de perguntas poderosas:

```
"Me execute todas as tarefas urgentes (#urgente) do projeto oloroke"
→ get_todos(folder="Projects/oloroke-notes", tag="urgente", project="oloroke")

"Quais são as tarefas bloqueadas que preciso destravar?"
→ get_todos(priority="blocked")

"Me mostre o que precisa fazer no backend (#backend) com prioridade alta?"
→ get_todos(tag="backend", priority="high")

"Quais tarefas do projeto oloroke com tag #urgente ainda não foram feitas?"
→ get_todos(folder="Projects/oloroke-notes", tag="urgente", completed=False)
```

---

## 📊 Comparação: Qual Usar?

| Método | Pros | Contras | Melhor Para |
|--------|------|---------|------------|
| **Tags Inline** | Flexível, fácil de adicionar | Pode poluir a linha | Categorizações rápidas |
| **Emoji** | Visual, intuitivo | Limitado a 4 prioridades | Visão rápida de urgência |
| **Frontmatter** | Estruturado, rico em metadata | Mais work pra manter | Projetos complexos |
| **Todos 3** | Máxima flexibilidade | Nenhum! | Recomendado! |

---

## 🔧 Instalação da Versão Avançada

1. Substitua `src/obsidian_mcp.py` pelo `obsidian_mcp_advanced.py`

2. Atualize `requirements.txt`:
```bash
cat > requirements.txt << 'EOF'
mcp>=0.2.0
python-dotenv>=1.0.0
pyyaml>=6.0
EOF
```

3. Reinstale as dependências:
```bash
pip install -r requirements.txt
```

4. Reinicie Claude Desktop e Cursor

---

## 💡 Dicas Pro

### 1. Organize por projeto
```markdown
---
projeto: oloroke
---
```

### 2. Use tags para categorias
```markdown
- [ ] Tarefa #backend #urgente #oauth
```

### 3. Combine com emojis para rápida visualização
```markdown
- [ ] 🔴 #urgente Coisa crítica
```

### 4. Adicione metadata útil no frontmatter
```yaml
---
projeto: oloroke
deadline: 2024-12-31
responsavel: Pauline
revisado_em: 2024-09-25
---
```

### 5. Use para agregar notas relacionadas
Crie uma pasta por projeto:
```
Projects/
├── oloroke-notes.md
├── terreiro-app-notes.md
└── petlove-improvements.md
```

Então pergunte:
```
"Quais são as tarefas da pasta Projects?"
```

---

## 🚀 Exemplos Reais de Conversas

### Conversa 1: Explorar um projeto

```
Você: Quais são os projetos que tenho?
Claude: [lista via list_projects()]

Você: Me mostre as tarefas do oloroke com prioridade alta
Claude: [chama get_todos(project="oloroke", priority="high")]
         Mostra 3 tarefas 🔴

Você: Execute a primeira delas (OAuth)
Claude: [chama update_todo()]
        Marca como completa e confirma
```

### Conversa 2: Filtrar por contexto

```
Você: Estou trabalhando em testes agora
Claude: Entendido, me mostre só as tarefas com tag #testing
Claude: [chama get_todos(tag="testing")]
         Mostra 2 tarefas de teste

Você: Marca a primeira como completa
Claude: [chama update_todo()]
```

### Conversa 3: Combinar filtros

```
Você: Qual é meu trabalho mais urgente no backend do oloroke?
Claude: [chama get_todos(
  folder="Projects/oloroke-notes",
  tag="backend",
  priority="high",
  completed=False
)]
Mostra: "Implementar autenticação OAuth"
```

---

Pronto! Agora você tem **3 formas poderosas** de organizar suas tarefas no Obsidian e o Claude consegue filtrar exatamente o que você precisa. 

## Licença

MIT - Use livremente! Se fizer melhorias, considere fazer um pull request 

## Contribuições

Encontrou um bug ou tem uma ideia? Abra uma [issue](https://github.com/seu-usuario/obsidian-mcp/issues) ou faça um [pull request](https://github.com/seu-usuario/obsidian-mcp/pulls)!

---

**=Criado por Pauline Oliveira**

Dúvidas? Abra uma issue no GitHub ou mande mensagem!
