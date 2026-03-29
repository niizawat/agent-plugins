---
title: "refactor: Split diagram-reviewer into drawio-reviewer and image-reviewer"
type: refactor
status: completed
date: 2026-03-27
origin: docs/brainstorms/2026-03-27-reviewer-split-requirements.md
---

# diagram-reviewer を XML レビューと画像レビューに分離

## Enhancement Summary

**深化日時**: 2026-03-27
**強化セクション数**: 7
**使用した研究エージェント**: architecture-strategist, agent-native-reviewer, code-simplicity-reviewer, performance-oracle, pattern-recognition-specialist, best-practices-researcher (×2)

### 主要な発見と改善点

1. **VISUAL-LABEL-READABILITY を削除**: VISUAL-ICON-OVERLAP と完全に同一処理（R04グリッド配置）のため、独立カテゴリとして維持するのは YAGNI 違反。
2. **diagram-fixer の VISUAL-ERROR スキップ指示を明示的に削除**する必要がある（Step 3 と Step 6 の矛盾を解消するチェックリスト項目が抜けていた）。
3. **統合レポートの構造化**: 単純な文字列結合ではなく `<!-- source: -->` コメント付きのセクション分離形式を採用し、diagram-fixer が XML/視覚の違反を区別できるようにする。
4. **drawio CLI 不在時の明示的フラグ管理**: `visual_check_executed` フラグで偽陽性 PASS を防ぐ。
5. **R10 と VISUAL-EDGE-LABEL-OVERLAP の重複排除ルール**: 同一エッジIDが両方から報告された場合は R10 を優先する。
6. **修正適用順序の正規化**: R11-EMPTY-CONTAINER は R07 の直後に適用する（R07 で空コンテナが生まれるケースを処理するため）。
7. **diagram-reviewer の委譲ラッパー化**: 「非推奨の description のみ」ではなく、新エージェントへの委譲ラッパーとして実装することで既存ユーザーが新機能を享受できる。

---

## Overview

現在の `diagram-reviewer` エージェントは XML ルールチェック（R01〜R12）と PNG 視覚検査（VISUAL-ERROR/WARNING）を 1 つのエージェントが担っている。この責任を 2 つの専任エージェントに分離し、QA ループの精度と処理速度を改善する。

```
【現在】
diagram-qa → diagram-reviewer（XML + PNG）→ diagram-fixer

【変更後】
diagram-qa → diagram-drawio-reviewer（XML のみ）  ─┐
           → diagram-image-reviewer（PNG のみ）  ─┤→ diagram-fixer（統合レポート）
```

## Problem Statement / Motivation

- **責任の混在**: XML 構造検証と視覚的品質検査は本質的に別のスキルを必要とする
- **直列実行の非効率**: 現行は PNG エクスポート・視覚検査が XML チェックの後に直列実行される
- **改善困難**: 一方の精度を改善しようとすると他方のロジックへの影響を考慮しなければならない
- **並列化で高速化**: 2 エージェントを並列実行することで各イテレーションの待ち時間を削減できる（約22%短縮）

## Proposed Solution

### 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `agents/diagram-drawio-reviewer.md` | **新規作成** — XML ルールチェック専任 |
| `agents/diagram-image-reviewer.md` | **新規作成** — PNG 視覚検査専任 |
| `agents/diagram-qa.md` | **更新** — 2 レビュアーの並列実行 + 統合レポート生成 |
| `agents/diagram-fixer.md` | **更新** — 統合レポート入力の明記 + VISUAL-ERROR 修正ロジック追加 |
| `agents/diagram-reviewer.md` | **委譲ラッパー化** — 新エージェントへの委譲ラッパーとして実装 |

---

## Technical Approach

### グリッド定数（全エージェント共通参照）

以下の定数は diagram-drawio-reviewer（チェック基準）と diagram-fixer（修正値）で一致させる必要がある。変更時は両ファイルを同時に更新すること。

```
GRID_PAD_X        = 60    # コンテナ内の左パディング
GRID_PAD_Y        = 60    # コンテナ内の上パディング
GRID_STEP_X       = 200   # 水平グリッドステップ
GRID_STEP_Y       = 180   # 垂直グリッドステップ
CONTAINER_MIN_W   = 180   # コンテナ最小幅（1列時）
CONTAINER_MIN_H   = 220   # コンテナ最小高（1行時）
ICON_EFF_W        = 120   # アイコン実効幅（重なり判定）
ICON_EFF_H        = 100   # アイコン実効高（重なり判定）
EDGE_OFFSET_PX    = 120   # R10 オフセット量
```

### 修正アクション正規化テーブル

検出方法（ルール名）と修正アクションを分離して管理する:

| 修正アクション | 対応するルール |
| --- | --- |
| FIX-ADD-LAYERS | R02 |
| FIX-DEDUP-IDS | R03 |
| FIX-ICON-LABEL-STYLE | R05 |
| **FIX-GRID-REARRANGE** | R04, VISUAL-ICON-OVERLAP, VISUAL-LABEL-READABILITY（すべて同一処理） |
| FIX-CONTAINER-RESIZE | VISUAL-CONTAINER-OVERFLOW（R04後もコンテナが小さい場合） |
| FIX-LAYER-ASSIGN | R07 |
| FIX-CHILD-RELOCATE | R11-EMPTY-CONTAINER（R07の副作用処理を含む） |
| FIX-EDGE-STYLE | R09 |
| **FIX-EDGE-OFFSET** | R10, VISUAL-EDGE-LABEL-OVERLAP（同一処理、R10を優先） |

---

### Phase 1: diagram-drawio-reviewer.md を新規作成

現行 `diagram-reviewer.md` の XML ルールチェック部分を抽出して独立させる。

**含めるルール（変更なし）**:
- R01: XML Structure (CRITICAL)
- R02: All 6 Layers Defined (CRITICAL) — `parent="0"` + no `vertex` attribute
- R03: Unique Cell IDs (CRITICAL)
- R04: Icon Spacing (ERROR) — 200px horizontal, 180px vertical
- R05: Icon Label Position (ERROR) — `verticalLabelPosition=bottom;verticalAlign=top`
- R07: Layer Assignment (ERROR)
- R08: AWS Shape Names (WARNING)
- R09: Edge Style (ERROR) — `edgeStyle=orthogonalEdgeStyle;jumpStyle=arc`
- R10: Edge Label Proximity (ERROR) — 絶対座標計算を含む
- R12: External Resources in Left Column (INFO)

**除外するもの**:
- PNG エクスポート処理（Step 4 の `export-to-png.sh` 呼び出し）
- 視覚検査ロジック（アイコン重なり、ラベル可読性 etc.）
- R11（PNG ベースのチェック → diagram-image-reviewer へ移動）
- VISUAL-ERROR/VISUAL-WARNING の報告

**出力レポート形式**（現行から VISUAL-ERROR 行を除いたもの）:

```markdown
## DrawIO 構成図レビューレポート（XML ルール）

📄 **ファイル**: [path]
🕐 **レビュー日時**: [date]

### サマリー
| 重大度 | 件数 | 判定 |
|--------|------|------|
| CRITICAL | N | ❌ / ✅ |
| ERROR    | N | ❌ / ✅ |
| WARNING  | N | ⚠️ / ✅ |
| INFO     | N | ℹ️ |

**総合判定**: ✅ 合格 / ❌ 不合格（CRITICAL または ERROR が 1 件以上）

### 違反詳細
[各違反を重大度の高い順に列挙]

### 合格ルール
[違反がなかったルールを列挙]
```

**PASS/FAIL 判定**: CRITICAL = 0 かつ ERROR = 0

**tools**: `["Read", "Glob", "Bash"]`（PNG 不要のため Bash は最小限）

### Research Insights — Phase 1

**機械可読性の向上（agent-native-reviewer より）**: diagram-fixer が自動処理できるよう、違反詳細に JSON コードブロックを補足する形式を推奨する。

```markdown
#### ERROR: Icon Spacing (R04)

- **対象**: ecs-1, rds-1
- **問題**: 水平距離 80px（必要: 200px）
- **修正案**: ecs-1 の x を 200 → 400 に変更

```json
{
  "rule": "R04",
  "severity": "ERROR",
  "recommended_fix": "FIX-GRID-REARRANGE",
  "parent_id": "subnet-priv-1a"
}
```
```

`recommended_fix` フィールドを追加することで、diagram-fixer が修正アクションを曖昧なく特定できる。

---

### Phase 2: diagram-image-reviewer.md を新規作成

現行 `diagram-reviewer.md` の PNG 視覚検査部分を抽出して独立させる。

**処理フロー**:

1. `.drawio` ファイルパスを受け取る
2. **XML を Read ツールで読み込む** — 全 mxCell の id・parent・x・y・width・height を抽出し、絶対座標マップを構築する（視覚上の位置と cell ID を対応づけるため）
   - 座標マップ構築: `abs_x(cell) = cell.x_rel + abs_x(parent)` を再帰的に計算
   - 間隔違反の疑いがあるアイコン（隣接距離 < 150px）を重点検査リストとして抽出
   - **注意**: この XML 読み込みは drawio-reviewer と並列実行されるため時間的オーバーヘッドはない（全体の 5〜10%）
3. `bash skills/drawio-export/scripts/export-to-png.sh <input.drawio>` を実行
   - exit code `2`（drawio CLI なし）の場合: `visual_check_executed = false` として「Visual review skipped (drawio CLI not available)」を報告して終了
   - 正常終了の場合: `visual_check_executed = true`
4. PNG を Read ツールで読み込み、**座標マップを参照しながら**視覚的に検査する。プロンプト設計原則: 重なり候補（隣接距離 < 150px）のアイコンだけをプロンプトに埋め込む（全セルを渡すと精度が低下）。各検査項目で絶対座標マップと照合して cell ID を特定し、「cell ID + 絶対座標 + 相対座標 + 推奨新座標」の4点セットで報告させる。検査項目:
   - **アイコン重なり (VISUAL-ICON-OVERLAP)** — 重なっているアイコンの cell ID・現在絶対座標・親コンテナIDを報告
   - **ラベル可読性 (VISUAL-LABEL-READABILITY)** — ラベルが切れているアイコンの cell ID を報告（修正アクションは FIX-GRID-REARRANGE、VISUAL-ICON-OVERLAP と同一）
   - **エッジラベルとアイコンの重なり (VISUAL-EDGE-LABEL-OVERLAP)** — 対象エッジ ID・重なりアイコン ID・現在の midpoint 座標を報告（R10 と同一エッジIDの場合、fixer は R10 を優先）
   - **コンテナサイズ不足 (VISUAL-CONTAINER-OVERFLOW)** — はみ出しているアイコンの cell ID・コンテナ ID・推奨コンテナサイズを報告
   - **R11 空コンテナ (R11-EMPTY-CONTAINER)** — 視覚的に空のコンテナ ID を報告（必ず XML の parent 関係も確認: コンテナを parent とする cell が存在するか、その cell の相対座標も報告）
   - **全体バランス** — 全体的な配置の問題を VISUAL-WARNING として報告（修正不可）
5. 修正可能な問題は **cell ID・絶対座標・相対座標（XML値）・推奨修正を含む構造化形式** で `VISUAL-ERROR` として報告
6. 修正不可（全体バランス）は `VISUAL-WARNING` として報告

**出力レポート形式**:

```markdown
## DrawIO 構成図レビューレポート（視覚検査）

📄 **ファイル**: [path]
🖼️ **PNG**: [path].png
🕐 **レビュー日時**: [date]
🔍 **視覚検査状態**: completed / skipped (drawio CLI not available)

### サマリー
| 重大度 | 件数 | 判定 |
|--------|------|------|
| VISUAL-ERROR   | N | ❌ / ✅ |
| VISUAL-WARNING | N | ⚠️ / ✅ |

**総合判定**: ✅ 合格 / ❌ 不合格（VISUAL-ERROR が 1 件以上）

### 視覚的問題の詳細

#### VISUAL-ERROR: アイコン重なり (VISUAL-ICON-OVERLAP)

- **対象**: [cell-id-A] と [cell-id-B]
- **問題**: 2つのアイコンが垂直方向に80px間隔（必要: 180px）で重なっている
- **座標種別**: 絶対座標（XMLのx/yに親コンテナのオフセットを加算済み）
- **cell-id-A 絶対座標**: (710, 440)、**相対座標（XML値）**: x=80, y=80（親: subnet-pub-1a）
- **cell-id-B 絶対座標**: (710, 520)、**相対座標（XML値）**: x=80, y=160（親: subnet-pub-1a）
- **親コンテナ XML geometry**: x=630, y=360, width=300, height=200
- **修正案**: 親コンテナ (subnet-pub-1a) に FIX-GRID-REARRANGE を適用
- **recommended_fix**: FIX-GRID-REARRANGE
- **fix_parent_id**: subnet-pub-1a

### 合格した視覚チェック
[問題がなかった項目を列挙]

[drawio CLI が利用不可の場合]
ℹ️ Visual review skipped (drawio CLI not available)
```

**PASS/FAIL 判定**: VISUAL-ERROR = 0

**tools**: `["Read", "Glob", "Bash"]`

### Research Insights — Phase 2

**座標種別の必須明示（agent-native-reviewer より）**: VISUAL-ERROR の出力に「絶対座標か相対座標か」を明示しないと diagram-fixer が座標変換を誤る。常に絶対座標と相対座標（XML値）の両方を報告すること。

**R11 の検出と修正の整合性（architecture-strategist より）**: R11-EMPTY-CONTAINER は「視覚的に空に見えるコンテナ」を検出するが、diagram-fixer は「parent 関係にあるアイコンの座標調整」しか行えない。image-reviewer は必ず XML の parent 関係（このコンテナを parent とする cell が存在するか）も確認し、レポートに含めること。parent 関係がない場合は FIX-CHILD-RELOCATE の対象外として VISUAL-WARNING で報告する。

**優先絞り込みによるプロンプト品質向上（PNG 検査研究より）**: 座標マップ全件をプロンプトに渡すのではなく、XML 計算で「隣接距離 < 150px」を事前スクリーニングし、重なり候補のみを絞り込んでプロンプトに渡すことで LLM の注意が分散しない。

---

### Phase 3: diagram-qa.md を更新

`Step 1: レビュー実行` を 2 エージェントの並列呼び出しに変更する。

**並列実行の指示（重要）**: diagram-qa のシステムプロンプトに「同一ターンで 2 つの Agent ツール呼び出しを発行することで真の並列実行を達成する」と明示的に記述する。明示しないと逐次実行になる場合がある。

**変更前（Step 1）**:
```
Agent: diagram-reviewer
Prompt: "[drawio_path] をレビューして"
```

**変更後（Step 1）**:
```
[並列実行] 以下の 2 エージェントを同一ターンで Agent ツールを呼び出す:

Agent A: diagram-drawio-reviewer
Prompt: "[drawio_path] をレビューして。出力は構造化レポート形式で返すこと。"

Agent B: diagram-image-reviewer
Prompt: "[drawio_path] をレビューして。出力は構造化レポート形式で返すこと。"

両エージェントの完了を待ち、結果を drawio_report / image_report として保存する。
image_report の先頭行「視覚検査状態: completed / skipped」を確認し、
visual_check_executed フラグを設定する。
```

**統合レポート生成ロジック**（両結果取得後）:

```python
# 件数集計
critical_count     = drawio_report から CRITICAL 件数を抽出
error_count        = drawio_report から ERROR 件数を抽出
visual_error_count = image_report から VISUAL-ERROR 件数を抽出（CLI スキップ時は 0 ではなく None）
warning_count      = drawio_report + image_report の WARNING 件数合計
info_count         = drawio_report の INFO 件数

# CLI スキップ時の扱い
if visual_check_executed == False:
    violation_count = critical_count + error_count  # VISUAL-ERROR を含めない
else:
    violation_count = critical_count + error_count + visual_error_count

# 統合レポートを構造化形式で作成（fixer へ渡す）
unified_report = f"""
## 統合レビューレポート

<!-- source: diagram-drawio-reviewer -->
### XML ルールチェック結果
{drawio_report}

---

<!-- source: diagram-image-reviewer -->
<!-- status: {completed|skipped} -->
### 視覚検査結果
{image_report}

---

### 統合サマリー（diagram-fixer 参照用）
| 重大度 | 件数 |
|--------|------|
| CRITICAL     | {critical_count} |
| ERROR        | {error_count} |
| VISUAL-ERROR | {visual_error_count if visual_check_executed else "skipped"} |
| WARNING      | {warning_count} |
| INFO         | {info_count} |

violation_count: {violation_count}
visual_check_executed: {visual_check_executed}
"""
```

**PASS 判定の変更**:

```
【変更前】violation_count = critical_count + error_count
【変更後】violation_count = critical_count + error_count + visual_error_count
         （ただし visual_check_executed = False の場合は VISUAL-ERROR を含めない）
```

**Final Report の更新**:

```markdown
### 最終レビュー結果
| 重大度 | 件数 | 判定 |
|--------|------|------|
| CRITICAL     | N | ❌ / ✅ |
| ERROR        | N | ❌ / ✅ |
| VISUAL-ERROR | N | ❌ / ✅ |
| WARNING      | N | ⚠️ / ✅ |
| INFO         | N | ℹ️ |

[visual_check_executed = False の場合]
⚠️ **視覚検査未実施**: drawio CLI が利用不可。PNG を手動確認することを推奨します。
```

**収束チェックの強化（停滞・発散・振動の検出）**:

```
【変更前の収束チェック（単純）】
if prev_violation_count is not None and violation_count >= prev_violation_count:
  → FAIL: 修正効果なし

【変更後の収束チェック（多層防御）】
violation_history = [前回, 今回]  # イテレーション毎に追記

# 停滞検出: 直近 2 回で違反数が変化しない
if len(violation_history) >= 2 and violation_history[-1] == violation_history[-2]:
  → FAIL: 修正効果なし（停滞）

# 発散検出: 違反数が増加している
if len(violation_history) >= 2 and violation_history[-1] > violation_history[-2]:
  → FAIL: 修正後に新規問題が発生（発散）
```

### Research Insights — Phase 3

**並列呼び出しの明示的指示（並列エージェント研究より）**: Claude は明示的な指示がないと逐次実行を選ぶ場合がある。システムプロンプトに「独立したタスクが 2 件以上ある場合、同一ターンで複数の Agent ツール呼び出しを発行せよ。1 つずつ順番に発行してはならない」と明記する。

**violation_count の機械可読な単一行（agent-native-reviewer より）**: `violation_count: N` という固定フォーマットの1行を統合レポート末尾に含めることで、収束チェックの数値抽出が確実になる。

**R10 と VISUAL-EDGE-LABEL-OVERLAP の重複排除（architecture-strategist より）**: 同一エッジ ID が両レビュアーから報告される場合がある。diagram-fixer の Step 3 に「同一エッジ ID が R10 と VISUAL-EDGE-LABEL-OVERLAP の両方に存在する場合は R10 のみを処理し VISUAL-EDGE-LABEL-OVERLAP をスキップする」というルールを追加する（R10 の方が定量的座標計算に基づくため信頼性が高い）。

---

### Phase 4: diagram-fixer.md を更新（VISUAL-ERROR 修正ロジック追加）

統合レポートの入力明記に加え、修正可能な VISUAL-ERROR への対応ロジックを追加する。

**Input セクションの更新**:

- レビューレポートは `diagram-drawio-reviewer` と `diagram-image-reviewer` の統合レポートである旨を明記
- 統合レポートには XML ルールチェック結果セクションと視覚検査結果セクションが含まれる
- image-reviewer の `<!-- source: diagram-image-reviewer -->` セクションから修正対象を抽出する

**既存の VISUAL-ERROR スキップ指示を削除する（重要）**:

- 現行 Step 3 の「**Skip WARNING, INFO, and VISUAL-ERROR violations**」という記述を変更する
- 現行 Step 6 の「`WARNING/INFO/VISUAL-ERROR は自動修正の対象外`」というスキップ説明文を更新する
- 変更後の方針: 「`VISUAL-WARNING（全体バランス）と INFO は自動修正の対象外。VISUAL-ERROR のうち `recommended_fix` フィールドが既知の修正アクションにマップできるものは自動修正する。`」

**修正アクションの適用順序（R04/R07 の副作用を考慮した正規化順序）**:

```
Order 1: FIX-ADD-LAYERS         (R02 — 構造の前提)
Order 2: FIX-DEDUP-IDS          (R03 — ID の一意性)
Order 3: FIX-ICON-LABEL-STYLE   (R05 — スタイル修正、独立)
Order 4: FIX-GRID-REARRANGE     (R04 + VISUAL-ICON-OVERLAP — 座標修正)
Order 5: FIX-CONTAINER-RESIZE   (R04 後も小さい場合 + VISUAL-CONTAINER-OVERFLOW)
Order 6: FIX-LAYER-ASSIGN       (R07 — 絶対座標変換は R04 後に行う)
Order 7: FIX-CHILD-RELOCATE     (R11-EMPTY-CONTAINER — R07 の副作用で空コンテナが生まれた場合も含む)
Order 8: FIX-EDGE-STYLE         (R09)
Order 9: FIX-EDGE-OFFSET        (R10 + VISUAL-EDGE-LABEL-OVERLAP — エッジラベル)
```

**R07 後に R11 を適用する理由**: R07 でアイコンをレイヤーに移動すると、コンテナ（VPC/Subnet）の parent 配下からアイコンが消えて視覚的に空コンテナになるケースがある。この副作用を R07 の直後に処理するのが自然である。

**追加する修正アクション（Fix Process に追記）**:

#### VISUAL-ICON-OVERLAP — アイコン重なり修正

R04 グリッド配置と同じロジックを適用。image-reviewer が報告した `fix_parent_id` の parent 内のアイコン全体を再配置する。

```text
対象: VISUAL-ERROR で recommended_fix = FIX-GRID-REARRANGE の違反
処理: R04 Fix と同じグリッド座標計算を適用（fix_parent_id を parent として使用）
注意: VISUAL-LABEL-READABILITY も同一処理のため個別セクション不要（R04 と統合）
```

#### VISUAL-EDGE-LABEL-OVERLAP — エッジラベル重なり修正

R10 オフセット調整と同じロジックを適用。R10 と同一エッジ ID が報告されている場合は R10 の処理のみ行いこのアクションをスキップする。

```text
対象: VISUAL-ERROR で recommended_fix = FIX-EDGE-OFFSET の違反
      かつ同一 edge_id が R10 にも存在しない場合のみ
処理: R10 Fix と同じ mxPoint as="offset" の追加・調整
```

#### VISUAL-CONTAINER-OVERFLOW — コンテナサイズ不足修正

image-reviewer が報告したコンテナ拡張を XML に反映する。

```text
対象: VISUAL-ERROR で recommended_fix = FIX-CONTAINER-RESIZE の違反
処理: コンテナの mxGeometry width/height を拡張
      新サイズ = max(現サイズ, アイコン相対座標 + アイコンサイズ + padding 80px)
      ※ 相対座標（XML値）を使用すること（絶対座標ではない）
```

#### R11-EMPTY-CONTAINER — 空コンテナ修正（座標調整）

image-reviewer が空コンテナを検出した場合、コンテナの `parent` として登録されているアイコンのうち、コンテナ bounds の外側に配置されているものをコンテナ内に移動する。

```text
対象: VISUAL-ERROR で recommended_fix = FIX-CHILD-RELOCATE の違反

前提チェック:
- image-reviewer が「このコンテナを parent とする cell が存在する」と報告している場合のみ処理
- parent 関係がない場合（別レイヤーのアイコンが視覚的に重なっているだけ）はスキップ

処理:
1. container の mxGeometry（x, y, width, height）を取得
2. container を parent とする全アイコン cell を列挙
3. 各アイコンの相対座標 (cell.x, cell.y) を検査:
   - bounds 外（cell.x < 0, cell.y < 0, または cell.x + icon_width > container.width など）
     → グリッド配置: new_x = 60 + col_index * 200, new_y = 60 + row_index * 180
4. 配置後にコンテナサイズが不足していれば FIX-CONTAINER-RESIZE と同様に拡張

制約: parent 関係にないアイコン（別レイヤー）は対象外（R07 で対処）
```

**スキップセクションの更新**:

- スキップ対象: `WARNING / INFO / VISUAL-WARNING（全体バランス）`
- 修正サマリーのスキップ説明文を「`VISUAL-WARNING（全体バランス）と INFO は自動修正の対象外。目視確認を推奨。`」に更新

### Research Insights — Phase 4

**R04 グリッド配置のカスケード問題（performance-oracle より）**: R04 コンテナ拡張は隣接コンテナの存在を考慮しない。拡張後に隣接コンテナと重なる場合があるが、これは R04 のスコープ外（異なる parent 間の比較は行わない）。発生した場合は次イテレーションの視覚検査で VISUAL-CONTAINER-OVERFLOW として検出される。

**R07 後の新規視覚問題（performance-oracle より）**: R07 でアイコンをレイヤーに移動すると、絶対座標で他の layer-3/4/5 アイコンと重なる新規 VISUAL-ICON-OVERLAP が発生しうる。これは次イテレーションの視覚検査で検出・修正されるため設計上は問題ないが、イテレーション回数を消費する。

**収束失敗パターンへの対応（並列エージェント研究より）**: VISUAL-ERROR が残存するループは以下の2つのパターンが多い:
1. **振動**: R04 修正 → 別の重なりが発生 → R04 修正 → 最初の重なりが再発
2. **停滞**: image-reviewer が毎回同じ VISUAL-ERROR を報告するが fixer が修正済みと誤認

どちらも収束チェック（直近 2 回で violation_count 変化なし）で早期終了する。

---

### Phase 5: diagram-reviewer.md を委譲ラッパーとして更新

「非推奨の description のみ更新する」ではなく、**新エージェントへの委譲ラッパー**として実装する。これにより既存ユーザーが新エージェントに明示的に切り替えることなく、VISUAL-ERROR の修正機能を享受できる。

**実装方針**:

```markdown
# Diagram Reviewer（後方互換ラッパー）

⚠️ **このエージェントは後方互換ラッパーです**。

内部的に `diagram-drawio-reviewer`（XML ルール）と `diagram-image-reviewer`（視覚検査）
を順番に呼び出し、統合レポートを生成します。新規実装では `diagram-qa` を使用してください。

## 処理フロー

1. `diagram-drawio-reviewer` を呼び出して XML ルールチェックを実行
2. `diagram-image-reviewer` を呼び出して視覚検査を実行
3. 両レポートを統合して単一レポートとして返す
```

**実装順序の制約（重要）**: Phase 5 は Phase 3 と Phase 4 の**両方の受け入れ基準が PASS した後**に実施すること。Phase 3/4 完了前に Phase 5 を実施すると、diagram-qa が委譲先エージェントを呼び出す状態になり動作不全になる。

### Research Insights — Phase 5

**委譲ラッパーの価値（agent-native-reviewer より）**: 「非推奨の description のみ」では既存ユーザーへの価値がない。委譲ラッパーとして実装することで:
- 既存ユーザーは切り替え不要
- VISUAL-ERROR の新機能を自動的に享受
- diagram-qa への移行を促すメッセージも含められる

---

## Implementation Checklist

- [x] `agents/diagram-drawio-reviewer.md` を新規作成
  - [x] XML ルール R01〜R12（R11 除く）を含む
  - [x] PNG 処理ロジックを含まない
  - [x] 違反詳細に `recommended_fix` フィールドを含む構造化形式
  - [x] グリッド定数を本計画の「グリッド定数テーブル」と一致させる
- [x] `agents/diagram-image-reviewer.md` を新規作成
  - [x] 検査前に XML を Read して cell ID・座標マップを構築する
  - [x] PNG エクスポート → 視覚検査フローを含む
  - [x] `visual_check_executed` フラグを出力に含める（CLI スキップ時の区別）
  - [x] R11 の報告時に XML の parent 関係（コンテナを parent とする cell の有無）も確認・報告する
  - [x] VISUAL-ERROR の出力に「絶対座標」「相対座標（XML値）」「親コンテナ geometry」を含める
  - [x] `recommended_fix` フィールドと `fix_parent_id` を含む構造化形式
  - [x] 修正可能な VISUAL-ERROR は FIX-GRID-REARRANGE / FIX-EDGE-OFFSET / FIX-CONTAINER-RESIZE / FIX-CHILD-RELOCATE のいずれかで報告
  - [x] 修正不可（全体バランス）は VISUAL-WARNING で報告
  - [x] **VISUAL-LABEL-READABILITY は独立カテゴリとして追加しない**（FIX-GRID-REARRANGE で統合）
- [x] `agents/diagram-qa.md` を更新
  - [x] Step 1 を「同一ターンで Agent ツールを 2 つ呼び出す」並列実行に変更
  - [x] `visual_check_executed` フラグの処理を追加
  - [x] 統合レポートを `<!-- source: -->` セクション分離形式で生成するよう変更
  - [x] 統合レポート末尾に `violation_count: N` の機械可読行を追加
  - [x] `violation_count` の計算を `critical + error + visual_error` に更新（CLI スキップ時は `critical + error` のみ）
  - [x] 収束チェックに停滞・発散の検出パターンを追加
  - [x] Final Report に VISUAL-ERROR 行を追加
  - [x] Final Report に `visual_check_executed = False` 時の警告メッセージを追加
- [x] `agents/diagram-fixer.md` を更新
  - [x] Input セクションに統合レポートの構造（XML/視覚セクション）を明記
  - [x] **Step 3 の「Skip VISUAL-ERROR」指示を削除する**（重要: 既存記述との矛盾解消）
  - [x] Step 3 に R10 と VISUAL-EDGE-LABEL-OVERLAP の重複排除ルールを追加
  - [x] VISUAL-ICON-OVERLAP 修正ロジックを追加（R04 と統合、VISUAL-LABEL-READABILITY は不要）
  - [x] VISUAL-EDGE-LABEL-OVERLAP 修正ロジックを追加（R10 重複時はスキップ）
  - [x] VISUAL-CONTAINER-OVERFLOW 修正ロジックを追加（相対座標ベースで計算）
  - [x] R11-EMPTY-CONTAINER（コンテナ内座標調整）修正ロジックを追加
  - [x] 修正適用順序を正規化順序（Order 1〜9）に更新
  - [x] **Step 6 スキップ説明文を「VISUAL-WARNING（全体バランス）と INFO が対象外」に更新**（重要）
  - [x] グリッド定数を本計画の「グリッド定数テーブル」と一致させる
- [x] `agents/diagram-reviewer.md` を委譲ラッパーとして更新
  - [x] description を後方互換ラッパーである旨に更新
  - [x] 処理フローを「drawio-reviewer → image-reviewer → 統合」として実装
  - [x] **Phase 3 と Phase 4 の両方が完了してから実施する**

## Acceptance Criteria

- [ ] `diagram-drawio-reviewer` が XML ルールのみを検査し、正しいレポートを返す
- [ ] `diagram-image-reviewer` が PNG 視覚検査のみを実行し、VISUAL-ERROR/WARNING を座標種別付きで報告する
- [ ] `diagram-qa` が両レビュアーを並列で（同一ターンで）呼び出し、統合レポートを `diagram-fixer` に渡す
- [ ] `diagram-fixer` が統合レポートから XML 違反と修正可能な VISUAL-ERROR（アイコン重なり・エッジラベル重なり・コンテナはみ出し・R11 空コンテナの座標調整）を修正する
- [ ] R10 と VISUAL-EDGE-LABEL-OVERLAP が同一エッジを報告した場合、R10 のみが処理される
- [ ] drawio CLI 不在時に `visual_check_executed = false` として違反カウントに含めず、最終レポートに警告を出す
- [ ] QA ループの PASS 条件（CRITICAL=0 AND ERROR=0 AND VISUAL-ERROR=0）が維持される
- [ ] 最大 3 回ループ・収束チェック（停滞・発散検出）など既存の QA ループ動作が変わらない
- [ ] `diagram-reviewer` が委譲ラッパーとして動作し、旧インターフェースとの互換性を維持する

## Dependencies & Risks

- **並列呼び出しの記述**: `diagram-qa` のシステムプロンプトに「同一ターンで 2 つの Agent ツール呼び出しを発行する」と明示的に指示する必要がある。
- **R07 修正の連鎖**: R07 でアイコンをレイヤーに移動すると新規 VISUAL-ICON-OVERLAP が発生しうる。次イテレーションで検出されるため最大 3 回のループで収束するはず。
- **R04 コンテナ拡張の隣接干渉**: コンテナ拡張が隣接コンテナとの重なりを生む場合がある。R04 のスコープ外（異なる parent 間比較は行わない）のため次イテレーションの視覚検査で対処される。
- **実装順序の遵守**: Phase 5（委譲ラッパー化）は Phase 3 と 4 の両方が完了してから行う。

## Outstanding Questions (Deferred to Planning)

> これらは実装中に判断・解決する技術的事項:

- `[Affects Phase 3]` `diagram-qa` での並列 Agent 呼び出しの具体的記述方法
- `[Affects Phase 3]` `visual_check_executed = False` 時に PASS 判定を「XML-PASS (視覚未確認)」と表記するか、単純な PASS とするか
- `[Affects Phase 3]` VISUAL-ERROR のみ残存時に早期終了するか（最大反復回数まで待つか）

## Sources & References

### Origin

- **Origin document:** [docs/brainstorms/2026-03-27-reviewer-split-requirements.md](../brainstorms/2026-03-27-reviewer-split-requirements.md)
  - Key decisions carried forward: 並列実行、統合レポートは diagram-qa が生成、diagram-reviewer は委譲ラッパーとして維持

### Internal References

- 現行 diagram-reviewer: [agents/diagram-reviewer.md](../../agents/diagram-reviewer.md)
- 新設 diagram-drawio-reviewer: [agents/diagram-drawio-reviewer.md](../../agents/diagram-drawio-reviewer.md)（Phase 1 完了済み）
- 現行 diagram-qa: [agents/diagram-qa.md](../../agents/diagram-qa.md)
- 現行 diagram-fixer: [agents/diagram-fixer.md](../../agents/diagram-fixer.md)
- PNG エクスポートスクリプト: [skills/drawio-export/scripts/export-to-png.sh](../../skills/drawio-export/scripts/export-to-png.sh)
- 旧 QA ループ要件: [docs/brainstorms/2026-03-26-diagram-qa-loop-requirements.md](../brainstorms/2026-03-26-diagram-qa-loop-requirements.md)
