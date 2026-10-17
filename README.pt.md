# Obsidian MCP Server

Um servidor [MCP](https://modelcontextprotocol.io) que conecta seu vault do Obsidian ao Claude Desktop e ao Cursor, para que a IA busque nas suas notas, leia e atualize seus metadados e gerencie seus to-dos sem você precisar copiar e colar nada.

🇬🇧 [English version](README.md)

## O que ele faz

| Ferramenta | Descrição |
|------------|-----------|
| `search_notes` | Busca notas por texto ou regex, por tags e por campos do frontmatter (tudo combinável), retornando as linhas encontradas com seus números |
| `list_tags` | Lista todas as tags do vault (inline e frontmatter) com a quantidade de notas que usam cada uma |
| `get_frontmatter` | Retorna o frontmatter YAML de uma nota em JSON |
| `update_frontmatter` | Cria, altera ou remove chaves do frontmatter, mantendo comentários, ordem das chaves e o corpo da nota intactos |
| `get_todos` | Lista to-dos (`- [ ]` / `- [x]`), com filtros `folder`, `tag`, `priority`, `completed` e `language` |
| `update_todo` | Marca um to-do como concluído/pendente (pelo caminho da nota e número da linha) |
| `get_note_content` | Retorna o conteúdo completo de uma nota |
| `list_projects` | Lista os projetos encontrados no frontmatter das notas |
| `get_supported_languages` | Lista os idiomas aceitos para palavras de prioridade |

Exemplos de pedidos:

- *"Encontre notas que falam de OAuth em Projects"* · *"Busque a regex `TODO\(\w+\)`"*
- *"Quais notas têm a tag #projeto e `status: rascunho`?"*
- *"Defina `status: concluído` no frontmatter de Projects/oloroke.md"*
- *"Mostre minhas tarefas #backend de alta prioridade"* · *"Marque a linha 5 de Projects/x.md como concluída"*

### Organizando suas notas (tudo opcional e combinável)

- **Tags inline:** `- [ ] Corrigir login #urgente #backend`. Tags aninhadas funcionam como no Obsidian: filtrar por `projeto` também encontra `#projeto/api`. Tags dentro de blocos de código, URLs (`pagina#ancora`) e links (`[[Nota#Seção]]`) são ignoradas.
- **Emoji de prioridade:** 🔴 alta · 🟡 média · 🟢 baixa · ⚫ bloqueada
- **Frontmatter YAML:** `projeto`/`project`, `prioridade`/`priority`, `tags` (lista ou `"a, b"`) e qualquer campo próprio que você queira usar na busca

```markdown
---
projeto: oloroke
prioridade: alta
status: rascunho
tags: [backend]
---
- [ ] 🔴 Implementar OAuth #urgente
```

As palavras de prioridade funcionam em **pt, en, es, fr, de, it**. Para adicionar outro idioma, veja [src/examples/add_custom_language.py](src/examples/add_custom_language.py).

### Segurança

O servidor só acessa arquivos dentro de `OBSIDIAN_VAULT_PATH`:

- Caminhos absolutos, `..` que saem do vault e symlinks que apontam para fora dele são rejeitados.
- `.obsidian/`, `.trash/` e `.git/` nunca são lidos nem alterados; só notas `.md` podem ser abertas ou editadas.
- As escritas são atômicas (arquivo temporário + rename), mantêm as quebras de linha do arquivo e são recusadas se o frontmatter existente tiver YAML inválido.

## Requisitos

- Python 3.11+
- Claude Desktop ou Cursor
- Um vault do Obsidian

## Instalação

### 1. Instalar

```bash
git clone git@github.com:apaulineoliveira/obsidian-mcp.git
cd obsidian-mcp
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Pegue os caminhos absolutos que serão usados no próximo passo:

```bash
echo "$PWD/venv/bin/python3"      # command
echo "$PWD/src/obsidian_mcp.py"   # script
```

### 2a. Claude Desktop

Abra o arquivo de configuração (ou vá em *Settings → Developer → Edit Config*):

| SO | Caminho |
|----|---------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

Adicione o servidor dentro de `mcpServers` (mantenha os servidores que já estiverem lá):

```json
{
  "mcpServers": {
    "obsidian-mcp": {
      "command": "/caminho/abs/obsidian-mcp/venv/bin/python3",
      "args": ["/caminho/abs/obsidian-mcp/src/obsidian_mcp.py"],
      "env": { "OBSIDIAN_VAULT_PATH": "/caminho/abs/do/seu/vault" }
    }
  }
}
```

No Windows, use `venv\\Scripts\\python.exe` e escape as barras invertidas (`C:\\Users\\eu\\vault`).

Feche totalmente o Claude Desktop (Cmd+Q / sair pela bandeja) e abra de novo. As ferramentas aparecem no menu 🔨 / conectores da caixa de mensagem.

### 2b. Cursor

Use o mesmo bloco `mcpServers` em um destes arquivos:

- `~/.cursor/mcp.json` — disponível em todos os projetos
- `.cursor/mcp.json` dentro de um projeto — só para aquele projeto

Depois abra *Cursor Settings → MCP*: o `obsidian-mcp` deve aparecer com um ponto verde e a lista de ferramentas. As ferramentas são usadas pelo modo **Agent** do chat.

### Configurando o caminho do vault

`OBSIDIAN_VAULT_PATH` deve ser o caminho absoluto da pasta do vault (a que contém `.obsidian/`). Ele é lido, em ordem de prioridade, de:

1. O bloco `env` da configuração do cliente (recomendado)
2. Um arquivo `.env` na raiz do repositório (`cp .env.example .env`)
3. Padrão: `~/Obsidian`

## Problemas comuns

- **O servidor não aparece:** valide o JSON de configuração, confirme que os dois caminhos existem e reinicie o cliente por completo.
- **`ModuleNotFoundError: mcp`:** o `command` deve apontar para o Python do venv, não para o do sistema.
- **`Vault não encontrado`:** o `OBSIDIAN_VAULT_PATH` está errado ou não é absoluto.
- **`Caminho fora do vault`:** use caminhos relativos ao vault, ex.: `Projects/x.md`.
- **Logs:** o Claude Desktop grava em `~/Library/Logs/Claude/mcp-server-obsidian-mcp.log` (macOS) ou `%APPDATA%\Claude\logs` (Windows); o Cursor mostra em *Output → MCP Logs*.
- **Testar o servidor manualmente:** `npx @modelcontextprotocol/inspector venv/bin/python3 src/obsidian_mcp.py`

## Arquitetura

O código segue uma arquitetura em camadas (limpa / hexagonal). As dependências só apontam para dentro: `adapters → application → core`.

```
src/
├── obsidian_mcp.py      Composição: conecta adapters e serviços e sobe o servidor
├── core/                Regras de domínio. Só biblioteca padrão; sem MCP, disco ou YAML
│   ├── paths.py         Regras de caminho (traversal, pastas internas, só .md)
│   ├── frontmatter.py   Separa/monta o bloco de frontmatter, via a porta FrontmatterCodec
│   ├── tags.py          Regras de tags do Obsidian (aninhadas, sem caixa, blocos de código)
│   ├── search.py        Consulta, correspondência, trechos e ranking
│   ├── todos.py         Leitura de checkboxes, filtros e marcação
│   ├── i18n.py          Palavras de prioridade por idioma
│   ├── ports.py         Interfaces NoteRepository e FrontmatterCodec
│   └── errors.py        Erros de domínio
├── application/         Casos de uso que orquestram o core pelas portas
│   ├── notes.py         Conteúdo, frontmatter, tags e projetos
│   ├── todos.py         Listar e concluir to-dos
│   └── search.py        Busca de notas
└── adapters/            O mundo externo
    ├── filesystem.py    NoteRepository em disco (symlinks, escrita atômica)
    ├── yaml_codec.py    FrontmatterCodec com ruamel.yaml (round-trip)
    └── mcp_server.py    Tools MCP: argumentos → casos de uso → JSON
```

Onde colocar cada mudança:

- **Nova regra sobre notas** (ex.: ler wikilinks): uma função em `core/`, testada com strings simples.
- **Nova capacidade**: um método em um serviço de `application/`, testado com um repositório em memória.
- **Nova tool**: um método em `VaultTools` e o nome em `TOOL_NAMES` (`adapters/mcp_server.py`).
- **Novo armazenamento** (ex.: API REST do Obsidian): uma classe que implemente `NoteRepository`, conectada em `obsidian_mcp.py`.

## Desenvolvimento

```bash
pip install -r requirements-dev.txt
pytest
```

Os testes espelham as camadas: `tests/core` (funções puras), `tests/application` (repositório em memória) e `tests/adapters` (disco, YAML e MCP reais).

## Encontrou um bug?

Abra uma [issue](https://github.com/apaulineoliveira/obsidian-mcp/issues) informando: o que você fez, o que esperava, o que aconteceu, seu SO/versão do Python e a mensagem de erro, se houver.

## Como contribuir

1. Faça um fork e crie uma branch (`git checkout -b feature/minha-mudanca`)
2. Faça sua alteração, adicione testes e rode `pytest`
3. Commit seguindo [Conventional Commits](https://www.conventionalcommits.org) (ex.: `feat(search): ...`)
4. Abra um pull request explicando o quê e por quê

## Licença

MIT — criado por Pauline Oliveira.
