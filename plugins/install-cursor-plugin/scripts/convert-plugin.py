#!/usr/bin/env python3
"""
Cursor IDE プラグインを Claude Code プラグイン形式に変換するスクリプト。

シングルプラグイン (.cursor-plugin/plugin.json) と
マルチプラグイン (.cursor-plugin/marketplace.json) の両方に対応。

使用方法:
    python convert-plugin.py <source_dir> [--scope project|user] \
        [--plugin <name>]

引数:
    source_dir          変換元のCursorプラグインディレクトリ
    --scope             インストールスコープ (project: デフォルト, user)
    --plugin            マルチプラグイン時に変換対象を絞り込む名前
    --output            出力先ディレクトリを明示指定（省略時はscope依存）
    --dry-run           実際には書き込まず変換内容を表示
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

# Cursor → Claude のフックイベントマッピング
HOOK_EVENT_MAP = {
    "preToolUse": "PreToolUse",
    "postToolUse": "PostToolUse",
    "beforeShellExecution": "PreToolUse",
    "afterShellExecution": "PostToolUse",
    "onResponse": "Stop",
    "afterAgentResponse": "Stop",
}

# beforeShellExecution は Bash ツール限定
SHELL_EVENTS = {"beforeShellExecution", "afterShellExecution"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cursor プラグインを Claude Code 形式に変換する"
    )
    parser.add_argument("source_dir", help="変換元のCursorプラグインディレクトリ")
    parser.add_argument(
        "--scope",
        choices=["project", "user"],
        default="project",
        help="インストールスコープ (デフォルト: project)",
    )
    parser.add_argument(
        "--plugin",
        default=None,
        help="マルチプラグインリポジトリで変換対象を絞り込む名前",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="出力先ディレクトリを明示指定",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際に書き込まず変換内容を表示",
    )
    return parser.parse_args()


def get_output_base(scope: str) -> Path:
    if scope == "user":
        return Path.home() / ".claude" / "plugins"
    return Path.cwd() / ".claude" / "plugins"


def read_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(
    path: Path,
    data: dict[str, Any] | list[dict[str, Any]],
    dry_run: bool = False,
) -> None:
    if dry_run:
        print(f"  [DRY-RUN] {path}")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_mdc_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    .mdc ファイルのフロントマターをパースして (frontmatter_dict, body) を返す。
    フロントマターは --- で囲まれたYAML相当のシンプルな key: value 形式を想定。
    """
    fm: dict[str, Any] = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                line = line.strip()
                if ":" in line:
                    key, _, val = line.partition(":")
                    fm[key.strip()] = val.strip()
            body = parts[2].lstrip("\n")

    return fm, body


def convert_rule(mdc_path: Path, output_dir: Path, dry_run: bool) -> None:
    """Cursor の .mdc ルールファイルを Claude の .md ルールに変換する。"""
    content = mdc_path.read_text(encoding="utf-8")
    fm, body = parse_mdc_frontmatter(content)

    # globs: をパースして paths: に変換
    globs_raw = fm.get("globs", "")
    paths: list[str] = []
    if globs_raw:
        paths = [
            g.strip() for g in re.split(r"[,\s]+", globs_raw) if g.strip()
        ]

    lines = ["---"]
    if paths:
        lines.append("paths:")
        for p in paths:
            lines.append(f"  - {p}")
    lines.append("---")
    lines.append("")
    lines.append(body.rstrip())
    lines.append("")

    out_path = output_dir / "rules" / mdc_path.with_suffix(".md").name
    if dry_run:
        print(f"  [DRY-RUN] Rule: {mdc_path.name} → {out_path}")
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  Rule: {mdc_path.name} → {out_path.relative_to(Path.cwd())}")


def convert_hooks(
    hooks_json_path: Path, output_dir: Path, dry_run: bool
) -> None:
    """Cursor の hooks/hooks.json を Claude の hooks 形式に変換する。"""
    hooks_data = read_json(hooks_json_path)
    claude_hooks: list[dict[str, Any]] = []

    entries = (
        hooks_data
        if isinstance(hooks_data, list)
        else hooks_data.get("hooks", [])
    )

    for entry in entries:
        cursor_event = entry.get("event", "")
        claude_event = HOOK_EVENT_MAP.get(cursor_event, cursor_event)
        command = entry.get("command", "")

        hook: dict[str, Any] = {
            "event": claude_event,
            "command": command,
        }

        if cursor_event in SHELL_EVENTS:
            hook["matcher"] = "Bash"

        if "condition" in entry:
            hook["condition"] = entry["condition"]

        claude_hooks.append(hook)

    out_path = output_dir / "hooks" / "hooks.json"
    write_json(out_path, claude_hooks, dry_run=dry_run)
    if not dry_run:
        print(f"  Hooks: {out_path.relative_to(Path.cwd())}")


def copy_components(source: Path, dest: Path, dry_run: bool) -> None:
    """skills/, agents/, commands/, .mcp.json などをコピーする。"""
    components = ["skills", "agents", "commands"]
    for comp in components:
        src = source / comp
        if src.exists():
            if dry_run:
                print(f"  [DRY-RUN] Copy: {src} → {dest / comp}")
            else:
                if (dest / comp).exists():
                    shutil.rmtree(dest / comp)
                shutil.copytree(src, dest / comp)
                print(f"  Copy: {comp}/")

    mcp_json = source / ".mcp.json"
    if mcp_json.exists():
        if dry_run:
            print(f"  [DRY-RUN] Copy: .mcp.json → {dest}")
        else:
            shutil.copy2(mcp_json, dest / ".mcp.json")
            print("  Copy: .mcp.json")


def build_claude_manifest(
    cursor_manifest: dict[str, Any],
    source: Path,
) -> dict[str, Any]:
    """Cursor マニフェストから Claude マニフェストを生成する。"""
    claude: dict[str, Any] = {
        "name": cursor_manifest.get("name", source.name),
        "version": cursor_manifest.get("version", "1.0.0"),
        "description": cursor_manifest.get("description", ""),
    }

    if "author" in cursor_manifest:
        claude["author"] = cursor_manifest["author"]
    if "homepage" in cursor_manifest:
        claude["homepage"] = cursor_manifest["homepage"]

    # skills / agents / commands の有無をマニフェストに反映
    for comp in ["skills", "agents", "commands"]:
        if (source / comp).exists():
            items = []
            for item_dir in sorted((source / comp).iterdir()):
                if item_dir.is_dir():
                    skill_md = item_dir / "SKILL.md"
                    if skill_md.exists():
                        items.append({
                            "name": item_dir.name,
                            "path": f"{comp}/{item_dir.name}/SKILL.md",
                        })
            if items:
                claude[comp] = items

    # hooks の有無を反映
    if (source / "hooks" / "hooks.json").exists():
        claude["hooks"] = "hooks/hooks.json"

    # MCP servers の有無を反映
    if (source / ".mcp.json").exists():
        mcp = read_json(source / ".mcp.json")
        if mcp.get("mcpServers"):
            claude["mcpServers"] = "auto"

    return claude


def convert_single_plugin(
    source: Path,
    output_dir: Path,
    dry_run: bool,
) -> None:
    """シングルプラグインを変換する。"""
    cursor_manifest_path = source / ".cursor-plugin" / "plugin.json"
    if not cursor_manifest_path.exists():
        print(f"ERROR: {cursor_manifest_path} が見つかりません", file=sys.stderr)
        sys.exit(1)

    cursor_manifest = read_json(cursor_manifest_path)
    plugin_name = cursor_manifest.get("name", source.name)
    dest = output_dir / plugin_name

    print(f"\n変換中: {plugin_name}")
    print(f"  {source} → {dest}")

    # コンポーネントのコピー
    copy_components(source, dest, dry_run)

    # フックの変換
    hooks_path = source / "hooks" / "hooks.json"
    if hooks_path.exists():
        convert_hooks(hooks_path, dest, dry_run)

    # ルールの変換
    rules_dir = source / "rules"
    if rules_dir.exists():
        for mdc_file in rules_dir.glob("*.mdc"):
            convert_rule(mdc_file, dest, dry_run)

    # マニフェストの生成
    claude_manifest = build_claude_manifest(cursor_manifest, source)
    manifest_path = dest / ".claude-plugin" / "plugin.json"
    write_json(manifest_path, claude_manifest, dry_run=dry_run)
    if not dry_run:
        print(f"  Manifest: {manifest_path.relative_to(Path.cwd())}")

    print(f"  完了: {plugin_name}")


def convert_multi_plugin(
    source: Path,
    output_dir: Path,
    target_name: str | None,
    dry_run: bool,
) -> None:
    """マルチプラグインリポジトリを変換する。"""
    marketplace_path = source / ".cursor-plugin" / "marketplace.json"
    if not marketplace_path.exists():
        print(f"ERROR: {marketplace_path} が見つかりません", file=sys.stderr)
        sys.exit(1)

    marketplace = read_json(marketplace_path)
    plugins = marketplace.get("plugins", [])

    if not plugins:
        print("ERROR: marketplace.json にプラグインが定義されていません", file=sys.stderr)
        sys.exit(1)

    for plugin_entry in plugins:
        name = plugin_entry.get("name", "")
        plugin_path = plugin_entry.get("path", "")

        if target_name and name != target_name:
            continue

        plugin_source = (
            source / plugin_path if plugin_path else source / "plugins" / name
        )
        if not plugin_source.exists():
            print(
                f"WARN: プラグインディレクトリが見つかりません: {plugin_source}",
                file=sys.stderr,
            )
            continue

        convert_single_plugin(plugin_source, output_dir, dry_run)


def main() -> None:
    args = parse_args()
    source = Path(args.source_dir).resolve()

    if not source.exists():
        print(f"ERROR: ソースディレクトリが見つかりません: {source}", file=sys.stderr)
        sys.exit(1)

    output_base = (
        Path(args.output).resolve()
        if args.output
        else get_output_base(args.scope)
    )

    print(f"スコープ: {args.scope}")
    print(f"出力先: {output_base}")

    if args.dry_run:
        print("[DRY-RUN モード]")

    # シングル or マルチを判定
    single_manifest = source / ".cursor-plugin" / "plugin.json"
    multi_manifest = source / ".cursor-plugin" / "marketplace.json"

    if multi_manifest.exists():
        print("マルチプラグインリポジトリを検出")
        convert_multi_plugin(source, output_base, args.plugin, args.dry_run)
    elif single_manifest.exists():
        print("シングルプラグインを検出")
        convert_single_plugin(source, output_base, args.dry_run)
    else:
        print(
            "ERROR: .cursor-plugin/plugin.json も"
            " .cursor-plugin/marketplace.json も見つかりません",
            file=sys.stderr,
        )
        print(f"  確認したパス: {source}", file=sys.stderr)
        sys.exit(1)

    print("\n変換が完了しました。")


if __name__ == "__main__":
    main()
