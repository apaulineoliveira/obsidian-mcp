# Obsidian MCP Server 🧠🔗

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

## 🌟 Próximos Passos

Ideias para expandir o projeto:

- [ ] Filtrar to-dos por tags (`#urgente #trabalho`)
- [ ] Agendar tarefas (ler data de criação)
- [ ] Suporte a subtarefas (indentação)
- [ ] Sincronização bidirecional com Notion/Asana
- [ ] CLI próprio (`obsidian-mcp list --completed`)
- [ ] Webhooks para atualizar em tempo real
- [ ] Suporte a outros formatos (YAML frontmatter, etc)

## 📚 Recursos

- [Model Context Protocol - Documentação Oficial](https://modelcontextprotocol.io)
- [Python MCP SDK](https://py.sdk.modelcontextprotocol.io)
- [Claude Desktop Setup](https://support.anthropic.com/en/articles/8784710-claude-desktop)
- [Obsidian API](https://docs.obsidian.md/)

## Licença

MIT - Use livremente! Se fizer melhorias, considere fazer um pull request 

## Contribuições

Encontrou um bug ou tem uma ideia? Abra uma [issue](https://github.com/seu-usuario/obsidian-mcp/issues) ou faça um [pull request](https://github.com/seu-usuario/obsidian-mcp/pulls)!

---

**=Criado por Pauline Oliveira**

Dúvidas? Abra uma issue no GitHub ou mande mensagem!