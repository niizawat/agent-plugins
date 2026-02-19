#!/usr/bin/env bash
# 変換済みプラグインをローカルマーケットプレイスに登録してインストールするスクリプト。
#
# 使用方法:
#   setup-marketplace.sh <plugin_name> [plugin_name2 ...] [--scope project|user]
#
# 例:
#   setup-marketplace.sh my-plugin                    # project スコープ（デフォルト）
#   setup-marketplace.sh my-plugin --scope user       # user スコープ
#   setup-marketplace.sh plugin-a plugin-b            # 複数プラグイン

set -euo pipefail

MARKETPLACE_NAME="local-plugins"
SCOPE="project"
PLUGIN_NAMES=()

# 引数パース
while [[ $# -gt 0 ]]; do
    case "$1" in
        --scope)
            SCOPE="${2:?--scope には project または user を指定してください}"
            shift 2
            ;;
        -*)
            echo "ERROR: 不明なオプション: $1" >&2
            exit 1
            ;;
        *)
            PLUGIN_NAMES+=("$1")
            shift
            ;;
    esac
done

if [[ ${#PLUGIN_NAMES[@]} -eq 0 ]]; then
    echo "ERROR: プラグイン名を1つ以上指定してください" >&2
    echo "使用方法: $0 <plugin_name> [--scope project|user]" >&2
    exit 1
fi

if [[ "$SCOPE" != "project" && "$SCOPE" != "user" ]]; then
    echo "ERROR: --scope には project または user を指定してください" >&2
    exit 1
fi

# スコープに応じたディレクトリを決定
if [[ "$SCOPE" == "user" ]]; then
    PLUGIN_DIR="${HOME}/.claude/plugins"
    MARKETPLACE_DIR="${HOME}/.claude/local-marketplace"
else
    PLUGIN_DIR="$(pwd)/.claude/plugins"
    MARKETPLACE_DIR="$(pwd)/.claude/local-marketplace"
fi

echo "スコープ: ${SCOPE}"
echo "プラグインディレクトリ: ${PLUGIN_DIR}"
echo "マーケットプレイスディレクトリ: ${MARKETPLACE_DIR}"

# マーケットプレイスディレクトリの準備
mkdir -p "${MARKETPLACE_DIR}/.claude-plugin"
mkdir -p "${MARKETPLACE_DIR}/plugins"

# marketplace.json を生成/更新
MANIFEST="${MARKETPLACE_DIR}/.claude-plugin/marketplace.json"

generate_manifest() {
    local plugins_json="[]"

    # 既存のプラグインエントリを保持しつつ新しいエントリを追加
    if [[ -f "${MANIFEST}" ]]; then
        plugins_json=$(python3 - <<EOF
import json, sys

with open("${MANIFEST}") as f:
    data = json.load(f)

existing = {p["name"]: p for p in data.get("plugins", [])}

new_names = ${PLUGIN_NAMES[@]+"${PLUGIN_NAMES[@]}"}
for name in new_names.split():
    if name:
        existing[name] = {
            "name": name,
            "source": f"./plugins/{name}",
            "version": "1.0.0"
        }

plugins = list(existing.values())
print(json.dumps(plugins, ensure_ascii=False, indent=2))
EOF
)
    else
        local items=""
        for name in "${PLUGIN_NAMES[@]}"; do
            items+=$(printf '    {"name": "%s", "source": "./plugins/%s", "version": "1.0.0"}' "${name}" "${name}")
            items+=","$'\n'
        done
        items="${items%,$'\n'}"
        plugins_json=$(printf '[\n%s\n  ]' "${items}")
    fi

    cat > "${MANIFEST}" <<JSON
{
  "name": "${MARKETPLACE_NAME}",
  "plugins": ${plugins_json}
}
JSON
}

generate_manifest
echo "マーケットプレイスマニフェストを更新しました: ${MANIFEST}"

# シンボリックリンクの作成
for PLUGIN_NAME in "${PLUGIN_NAMES[@]}"; do
    PLUGIN_SRC="${PLUGIN_DIR}/${PLUGIN_NAME}"
    PLUGIN_LINK="${MARKETPLACE_DIR}/plugins/${PLUGIN_NAME}"

    if [[ ! -d "${PLUGIN_SRC}" ]]; then
        echo "ERROR: プラグインディレクトリが見つかりません: ${PLUGIN_SRC}" >&2
        echo "  先に convert-plugin.py を実行してください" >&2
        exit 1
    fi

    if [[ -L "${PLUGIN_LINK}" ]]; then
        rm "${PLUGIN_LINK}"
    elif [[ -d "${PLUGIN_LINK}" ]]; then
        echo "WARN: ${PLUGIN_LINK} はシンボリックリンクではないディレクトリです。スキップします。" >&2
        continue
    fi

    ln -s "${PLUGIN_SRC}" "${PLUGIN_LINK}"
    echo "シンボリックリンク作成: ${PLUGIN_LINK} → ${PLUGIN_SRC}"
done

# claude CLI でマーケットプレイスを登録/更新
echo ""
echo "Claude CLI でマーケットプレイスを登録中..."

if claude plugin marketplace list 2>/dev/null | grep -q "${MARKETPLACE_NAME}"; then
    claude plugin marketplace update "${MARKETPLACE_NAME}"
    echo "マーケットプレイスを更新しました: ${MARKETPLACE_NAME}"
else
    claude plugin marketplace add "${MARKETPLACE_DIR}"
    echo "マーケットプレイスを追加しました: ${MARKETPLACE_DIR}"
fi

# プラグインをインストール
echo ""
for PLUGIN_NAME in "${PLUGIN_NAMES[@]}"; do
    echo "インストール中: ${PLUGIN_NAME}@${MARKETPLACE_NAME}"
    claude plugin install "${PLUGIN_NAME}@${MARKETPLACE_NAME}" --scope "${SCOPE}"
    echo "インストール完了: ${PLUGIN_NAME}"
done

echo ""
echo "すべての操作が完了しました。"
echo "インストール済みプラグインを確認するには: claude plugin list"
