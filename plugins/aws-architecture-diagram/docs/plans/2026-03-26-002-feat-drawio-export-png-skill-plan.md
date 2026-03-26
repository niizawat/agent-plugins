---
title: "feat: Add drawio-export skill for PNG conversion and visual review"
type: feat
status: active
date: 2026-03-26
---

# feat: Add drawio-export skill for PNG conversion and visual review

## Overview

`drawio` CLI（`/opt/homebrew/bin/drawio`）を使って `.drawio` ファイルを PNG に変換するスキルを追加する。
`diagram-reviewer` エージェントがこのスキルを呼び出して PNG を生成し、画像として視覚的に
アイコンの重なり・ラベル重なり・レイアウト問題を確認できるようにする。

## Problem Statement / Motivation

現在の `diagram-reviewer` は DrawIO XML をテキスト解析で検証している。
テキスト解析では「同一座標」は検出できるが、実際のレンダリング後の重なりや
視覚的な読みにくさは判断できない。

`drawio -x -f png` で PNG を生成すれば、Claude のマルチモーダル能力（画像認識）を
活用して「見た目の重なり」「ラベルの読みにくさ」「全体バランス」を評価できる。

## Proposed Solution

### 新スキル: `drawio-export`

```
skills/
└── drawio-export/
    ├── SKILL.md
    └── scripts/
        └── export-to-png.sh
```

**`export-to-png.sh`** — drawio CLI を呼び出す薄いラッパー:

```bash
#!/usr/bin/env bash
set -euo pipefail
INPUT="${1:?Usage: export-to-png.sh <input.drawio> [output.png]}"
OUTPUT="${2:-${INPUT%.drawio}.png}"
drawio -x -f png -s 2 -b 20 -o "$OUTPUT" "$INPUT"
echo "Exported: $OUTPUT"
```

### diagram-reviewer.md の更新

レビューフローに「PNG変換→画像確認」ステップを追加:

1. XML テキスト解析（R01〜R12）
2. `Bash` ツールで `export-to-png.sh` を実行して PNG を生成
3. `Read` ツールで PNG を読み込み（Claude は画像を認識できる）
4. 視覚的に以下を確認:
   - アイコンが重なっていないか
   - エッジラベルがアイコンラベルと重なっていないか
   - 全体のレイアウトバランス
5. 視覚的発見を WARNING として追記

## Acceptance Criteria

- [ ] `skills/drawio-export/SKILL.md` が作成されている
- [ ] `skills/drawio-export/scripts/export-to-png.sh` が実行可能
- [ ] `drawio` コマンドが存在しない場合のエラーハンドリングがある
- [ ] `diagram-reviewer` のフローが「PNG変換→画像確認」を含む
- [ ] `diagram-reviewer` のツールリストに `Bash` が追加されている
- [ ] テスト: `test/sample-cdk-stack.ts` から生成した `.drawio` でレビューが視覚的に動作する

## Technical Notes

- drawio CLI パス: `/opt/homebrew/bin/drawio` (macOS Homebrew)
- エクスポートコマンド: `drawio -x -f png -s 2 -b 20 -o output.png input.drawio`
  - `-s 2`: 2倍スケール（解像度向上）
  - `-b 20`: 20px ボーダー（見切れ防止）
- PNG はレビュー後に削除可能（一時ファイル扱い）
- Claude Code の `Read` ツールは PNG/JPG を画像として認識できる

## Dependencies & Risks

**依存**: drawio CLI（`/opt/homebrew/bin/drawio`）— macOS 専用の可能性あり。Linux では別パスの場合がある。

**リスク**: drawio CLI がインストールされていない環境では PNG 変換をスキップし、テキスト解析のみで合否判定する。

## Sources & References

- [agents/diagram-reviewer.md](../agents/diagram-reviewer.md)
- drawio CLI help: `drawio --help`
