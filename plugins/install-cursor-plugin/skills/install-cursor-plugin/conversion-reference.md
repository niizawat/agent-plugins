# 変換リファレンス

Cursor プラグインから Claude Code プラグインへの変換仕様をまとめたリファレンス。

## マニフェスト変換

### `.cursor-plugin/plugin.json` → `.claude-plugin/plugin.json`

| Cursor フィールド | Claude フィールド | 備考 |
| --------------- | --------------- | ---- |
| `name` | `name` | そのままコピー |
| `version` | `version` | そのままコピー。なければ `"1.0.0"` |
| `description` | `description` | そのままコピー |
| `author` | `author` | そのままコピー |
| `homepage` | `homepage` | そのままコピー |
| `rules` | なし | `rules/*.mdc` ファイルから自動生成 |
| `tools` | なし | Claude には直接対応なし |

**自動追加されるフィールド:**

- `skills` — `skills/<name>/SKILL.md` が存在する場合
- `agents` — `agents/<name>/` が存在する場合
- `commands` — `commands/<name>/` が存在する場合
- `hooks` — `hooks/hooks.json` が存在する場合
- `mcpServers` — `.mcp.json` が存在する場合

---

## ディレクトリ構造の対応

| Cursor | Claude | 処理 |
| ------ | ------ | ---- |
| `skills/` | `skills/` | そのままコピー |
| `agents/` | `agents/` | そのままコピー |
| `commands/` | `commands/` | そのままコピー |
| `.mcp.json` | `.mcp.json` | そのままコピー |
| `hooks/hooks.json` | `hooks/hooks.json` | イベント名を変換（後述） |
| `rules/*.mdc` | `rules/*.md` | フロントマターを変換（後述） |
| `.cursor-plugin/` | `.claude-plugin/` | マニフェストを変換 |

---

## フックイベントマッピング

`hooks/hooks.json` 内の `event` フィールドが以下のように変換される。

| Cursor イベント | Claude イベント | `matcher` | 説明 |
| -------------- | ------------- | --------- | ---- |
| `preToolUse` | `PreToolUse` | — | ツール実行前 |
| `postToolUse` | `PostToolUse` | — | ツール実行後 |
| `beforeShellExecution` | `PreToolUse` | `"Bash"` | シェル実行前（Bash ツール限定） |
| `afterShellExecution` | `PostToolUse` | `"Bash"` | シェル実行後（Bash ツール限定） |
| `onResponse` | `Stop` | — | エージェント応答時 |
| `afterAgentResponse` | `Stop` | — | エージェント応答後 |

### 変換前（Cursor）

```json
[
  {
    "event": "beforeShellExecution",
    "command": "./hooks/check-safety.sh"
  },
  {
    "event": "preToolUse",
    "command": "./hooks/log-tool.sh"
  }
]
```

### 変換後（Claude Code）

```json
[
  {
    "event": "PreToolUse",
    "matcher": "Bash",
    "command": "./hooks/check-safety.sh"
  },
  {
    "event": "PreToolUse",
    "command": "./hooks/log-tool.sh"
  }
]
```

---

## ルールファイル変換（`.mdc` → `.md`）

Cursor の `.mdc` ファイルは YAML フロントマターの `globs:` フィールドでファイルパターンを指定する。
Claude Code では `paths:` フィールドを使う。

### 変換前（Cursor `.mdc`）

```
---
globs: src/**/*.ts, tests/**/*.spec.ts
---

TypeScript ファイルを編集するときは必ずこのルールに従うこと。
```

### 変換後（Claude `.md`）

```markdown
---
paths:
  - src/**/*.ts
  - tests/**/*.spec.ts
---

TypeScript ファイルを編集するときは必ずこのルールに従うこと。
```

### フロントマター変換ルール

1. `globs:` の値をカンマまたは空白で分割してリスト化
2. `paths:` としてYAMLリスト形式で出力
3. `globs:` が空の場合は `paths:` を省略
4. その他のフロントマターフィールドはそのままコピー
5. 本文はそのままコピー

---

## 対応していない変換

以下の Cursor 機能は Claude Code に直接対応するものがないため、変換時にスキップされる:

| Cursor 機能 | 理由 |
| ---------- | ---- |
| `tools` (カスタムツール定義) | Claude Code では MCP サーバーで提供する |
| `context.include` | Claude Code の仕組みが異なる |
| `autoAttach` | Claude Code では手動でスキルを呼び出す |

これらの機能が必要な場合は、手動で Claude Code の対応機能に移行すること。

---

## ディレクトリ構造の完全例

### 変換前（Cursor プラグインリポジトリ）

```
my-cursor-plugin/
├── .cursor-plugin/
│   └── plugin.json
├── skills/
│   └── my-skill/
│       └── SKILL.md
├── hooks/
│   └── hooks.json
├── rules/
│   └── coding-style.mdc
└── .mcp.json
```

### 変換後（Claude Code プラグイン）

```
.claude/plugins/my-cursor-plugin/          ← project スコープの場合
~/.claude/plugins/my-cursor-plugin/        ← user スコープの場合
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── my-skill/
│       └── SKILL.md
├── hooks/
│   └── hooks.json                         ← イベント名が変換済み
├── rules/
│   └── coding-style.md                    ← .mdc → .md に変換済み
└── .mcp.json
```
