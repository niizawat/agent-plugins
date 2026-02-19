# agent-plugins

Claude Code 用プラグインを集めたマーケットプレイスリポジトリ。

## インストール

### 1. マーケットプレイスを追加

```bash
/plugin marketplace add https://github.com/niizawat/agent-plugins.git
```

### 2. プラグインをインストール

```bash
/plugin install install-cursor-plugin@agent-plugins
```

---

## プラグイン一覧

### `install-cursor-plugin`

Cursor IDE 用プラグインを Claude Code プラグイン形式に変換してインストールするスキル。

**できること:**

- `.cursor-plugin/plugin.json` を持つシングルプラグインを変換
- `.cursor-plugin/marketplace.json` を持つマルチプラグインリポジトリを変換
- `hooks/hooks.json` のイベント名を Claude Code 形式に自動変換
- `rules/*.mdc` のフロントマターを Claude Code 形式 (`paths:`) に変換
- `project` / `user` スコープを指定してインストール先を制御

**使い方（インストール後）:**

インストール後は Claude Code に以下のように話しかけるだけで使える。

```
このCursorプラグインをClaude Codeにインストールして:
https://github.com/example/my-cursor-plugin.git
```

```
~/repos/my-cursor-plugin をインストールして（userスコープで）
```

```
https://github.com/example/multi-plugin-repo.git の awesome-tool だけをインストールして
```

**スコープ別のインストール先:**

| スコープ | プラグイン格納先 |
| ------- | ------------ |
| `project`（デフォルト） | `./.claude/plugins/<name>/` |
| `user` | `~/.claude/plugins/<name>/` |

詳細は [`plugins/install-cursor-plugin/skills/install-cursor-plugin/SKILL.md`](plugins/install-cursor-plugin/skills/install-cursor-plugin/SKILL.md) を参照。

---

## リポジトリ構造

```
agent-plugins/
├── .claude-plugin/
│   └── marketplace.json              # マーケットプレイス定義
└── plugins/
    └── install-cursor-plugin/
        ├── .claude-plugin/
        │   └── plugin.json           # プラグインマニフェスト
        ├── scripts/
        │   ├── convert-plugin.py     # Cursorプラグイン変換スクリプト
        │   └── setup-marketplace.sh  # マーケットプレイス登録・インストールスクリプト
        └── skills/
            └── install-cursor-plugin/
                ├── SKILL.md                  # スキル定義
                └── conversion-reference.md   # 変換仕様リファレンス
```
