# Obsidian MCP Server

Um servidor [MCP](https://modelcontextprotocol.io) que conecta seu vault do Obsidian ao Claude Desktop e ao Cursor, para que a IA leia, filtre e conclua seus to-dos sem você precisar copiar e colar tarefas.

🇬🇧 [English version](README.md)

## O que ele faz

| Ferramenta | Descrição |
|------------|-----------|
| `get_todos` | Lista to-dos (`- [ ]` / `- [x]`) de todo o vault, com filtros `folder`, `tag`, `priority`, `completed` e `language` |
| `update_todo` | Marca um to-do como concluído/pendente (pelo caminho da nota e número da linha) |
| `get_note_content` | Retorna o conteúdo completo de uma nota |
| `list_projects` | Lista os projetos encontrados no frontmatter das notas |
| `get_supported_languages` | Lista os idiomas aceitos para palavras de prioridade |

### Organizando seus to-dos (tudo opcional e combinável)

- **Tags inline:** `- [ ] Corrigir login #urgente #backend`
- **Emoji de prioridade:** 🔴 alta · 🟡 média · 🟢 baixa · ⚫ bloqueada
- **Frontmatter YAML:** `projeto`/`project`, `prioridade`/`priority`, `tags`

```markdown
---
projeto: oloroke
prioridade: alta
tags: [backend]
---
- [ ] 🔴 Implementar OAuth #urgente
```

As palavras de prioridade funcionam em **pt, en, es, fr, de, it**. Para adicionar outro idioma, veja [src/examples/add_custom_language.py](src/examples/add_custom_language.py).

Exemplos de pedidos: *"Mostre minhas tarefas #backend de alta prioridade"* · *"O que está bloqueado em Projects/oloroke?"* · *"Marque a linha 5 de Projects/x.md como concluída"*

## Requisitos

- macOS, Python 3.11+
- Claude Desktop ou Cursor
- Um vault do Obsidian

## Instalação

```bash
git clone git@github.com:apaulineoliveira/obsidian-mcp.git
cd obsidian-mcp
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # defina OBSIDIAN_VAULT_PATH com o caminho completo do seu vault
```

Registre o servidor na configuração do seu cliente, usando **caminhos absolutos**:

- Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Cursor: `~/.cursor/mcp.json`

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

Feche totalmente (Cmd+Q) e reabra o cliente. Depois é só perguntar: *"Quais são meus to-dos no Obsidian?"*

## Problemas comuns

- **Claude não enxerga o servidor:** confira se o JSON de configuração é válido, se os caminhos existem e se reiniciou o cliente.
- **`ModuleNotFoundError: mcp`:** o `command` deve apontar para `venv/bin/python3`, não para o Python do sistema.
- **Nenhum to-do retornado:** verifique o `OBSIDIAN_VAULT_PATH` e se as tarefas usam o formato `- [ ]`.

## Encontrou um bug?

Abra uma [issue](https://github.com/apaulineoliveira/obsidian-mcp/issues) informando: o que você fez, o que esperava, o que aconteceu, seu SO/versão do Python e a mensagem de erro, se houver.

## Como contribuir

1. Faça um fork e crie uma branch (`git checkout -b feature/minha-mudanca`)
2. Faça sua alteração e teste localmente
3. Commit seguindo [Conventional Commits](https://www.conventionalcommits.org) (ex.: `feat(filtering): ...`)
4. Abra um pull request explicando o quê e por quê

## Licença

MIT — criado por Pauline Oliveira.
