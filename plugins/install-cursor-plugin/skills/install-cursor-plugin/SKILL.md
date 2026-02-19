# Install Cursor Plugin Skill

Cursor IDE 用プラグインを Claude Code プラグイン形式に変換してインストールするスキル。

## トリガーフレーズ

以下のフレーズを受け取ったときにこのスキルを使用すること:

- 「Cursor プラグインを Claude Code にインストールして」
- 「このCursorプラグインをインストールしたい」
- 「install cursor plugin」
- 「.cursor-plugin/ を持つリポジトリの URL やパスが与えられた」
- 「Cursor の plugin を変換して」
- 「cursor plugin convert」

## 前提条件

- Python 3.10 以上がインストールされていること
- `claude` CLI が利用可能であること
- このスキルのスクリプト（`SKILL_DIR/../../scripts/`）にアクセスできること

スクリプトのパスを動的に解決するには:

```bash
SKILL_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
SCRIPTS_DIR="${SKILL_DIR}/../../scripts"
```

## ワークフロー

### ステップ 1: ソースを確認する

ユーザーから以下を確認する:

- **ソース**: GitリポジトリのURL、またはローカルディレクトリのパス
- **スコープ**: `project`（デフォルト）または `user`
- **対象プラグイン**: マルチプラグインリポジトリの場合は名前を確認

### ステップ 2: リポジトリをクローン（URLの場合）

```bash
# URLが与えられた場合
TEMP_DIR=$(mktemp -d)
git clone <URL> "${TEMP_DIR}/repo"
SOURCE_DIR="${TEMP_DIR}/repo"

# ローカルパスの場合はそのまま使う
SOURCE_DIR="<local_path>"
```

### ステップ 3: プラグインを変換する

```bash
SKILL_DIR="$(dirname "$(realpath "$0")")"
SCRIPTS_DIR="${SKILL_DIR}/../../scripts"

# project スコープ（デフォルト）
python3 "${SCRIPTS_DIR}/convert-plugin.py" "${SOURCE_DIR}" --scope project

# user スコープ
python3 "${SCRIPTS_DIR}/convert-plugin.py" "${SOURCE_DIR}" --scope user

# マルチプラグインの特定プラグインのみ
python3 "${SCRIPTS_DIR}/convert-plugin.py" "${SOURCE_DIR}" --scope project --plugin <name>

# 変換内容を確認してから実行する場合
python3 "${SCRIPTS_DIR}/convert-plugin.py" "${SOURCE_DIR}" --dry-run
```

**変換後の出力先:**

| スコープ | 出力先 |
| ------- | ------ |
| `project` | `./.claude/plugins/<name>/` |
| `user` | `~/.claude/plugins/<name>/` |

### ステップ 4: マーケットプレイスに登録してインストールする

```bash
# project スコープ（デフォルト）
bash "${SCRIPTS_DIR}/setup-marketplace.sh" <plugin_name>

# user スコープ
bash "${SCRIPTS_DIR}/setup-marketplace.sh" <plugin_name> --scope user

# 複数プラグイン
bash "${SCRIPTS_DIR}/setup-marketplace.sh" plugin-a plugin-b --scope project
```

### ステップ 5: インストールを確認する

```bash
claude plugin list
```

## スコープ別の動作

| スコープ | デフォルト | プラグイン格納先 | ローカルマーケットプレイス |
| ------- | -------- | ------------ | ------------------- |
| `project` | **デフォルト** | `./.claude/plugins/<name>/` | `./.claude/local-marketplace/` |
| `user` | 明示指定時 | `~/.claude/plugins/<name>/` | `~/.claude/local-marketplace/` |

## 完全な実行例

### GitリポジトリのCursorプラグインをインストールする場合

```bash
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS_DIR="${SKILL_DIR}/../../scripts"

# クローン
TEMP_DIR=$(mktemp -d)
git clone https://github.com/example/my-cursor-plugin.git "${TEMP_DIR}/repo"

# 変換（dry-run で確認）
python3 "${SCRIPTS_DIR}/convert-plugin.py" "${TEMP_DIR}/repo" --dry-run

# 変換実行
python3 "${SCRIPTS_DIR}/convert-plugin.py" "${TEMP_DIR}/repo" --scope project

# インストール
bash "${SCRIPTS_DIR}/setup-marketplace.sh" my-cursor-plugin

# 確認
claude plugin list

# クリーンアップ
rm -rf "${TEMP_DIR}"
```

### ローカルにあるマルチプラグインリポジトリから特定のプラグインをインストールする場合

```bash
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS_DIR="${SKILL_DIR}/../../scripts"

# 変換
python3 "${SCRIPTS_DIR}/convert-plugin.py" ~/repos/my-plugins --scope user --plugin awesome-tool

# インストール
bash "${SCRIPTS_DIR}/setup-marketplace.sh" awesome-tool --scope user

# 確認
claude plugin list
```

## 変換のしくみ

詳細なマッピングは `conversion-reference.md` を参照。

- **マニフェスト**: `.cursor-plugin/plugin.json` → `.claude-plugin/plugin.json`
- **コンポーネント**: `skills/`, `agents/`, `commands/`, `.mcp.json` をコピー
- **フック**: `hooks/hooks.json` のイベント名を Claude Code 形式に変換
- **ルール**: `rules/*.mdc` の `globs:` フロントマターを `paths:` に変換して `.md` として出力

## 注意事項

- 変換前に `--dry-run` で内容を確認することを推奨する
- `hooks/` ディレクトリが存在する場合、Cursor イベント名が Claude Code 形式に自動変換される
- `.mdc` ルールファイルは `rules/*.md` として出力される
- Cursor 独自の機能で Claude Code に対応するものがない場合は、変換時に警告を出してスキップする
