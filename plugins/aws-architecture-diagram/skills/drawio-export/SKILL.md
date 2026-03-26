---
name: DrawIO Export to PNG
description: This skill should be used when converting a .drawio file to PNG format, when asked to "export drawio to png", "drawioをpngに変換", "構成図をpngで出力", or when the diagram-reviewer agent needs to visually inspect a generated diagram for overlapping icons, label collisions, or layout issues.
version: 0.1.0
---

# DrawIO Export to PNG

Convert a `.drawio` file to a PNG image using the `drawio` CLI, enabling visual inspection of generated architecture diagrams.

## When to Use

Use this skill when:

- The `diagram-reviewer` agent needs to visually confirm icon overlap, label readability, or layout balance
- A user asks to export a `.drawio` file as an image
- Visual quality assurance of a generated diagram is required

## Export Script

Use `scripts/export-to-png.sh` to perform the conversion:

```bash
bash skills/drawio-export/scripts/export-to-png.sh <input.drawio> [output.png]
```

- If `output.png` is omitted, the PNG is written alongside the input file (same name, `.png` extension).
- The script exits with code `2` and prints `SKIP_PNG_REVIEW=true` if the `drawio` CLI is not installed.

## CLI Reference

The underlying command:

```bash
drawio --export --format png --scale 2 --border 20 --output output.png input.drawio
```

| Flag | Value | Purpose |
|------|-------|---------|
| `--export` | — | Enable export mode |
| `--format` | `png` | Output format |
| `--scale` | `2` | 2× resolution for readability |
| `--border` | `20` | 20px padding to prevent clipping |
| `--output` | path | Output file path |

## Visual Review Checklist

After generating the PNG, read it with the `Read` tool and check:

1. **Icon overlap** — Are any AWS service icons visually overlapping each other?
2. **Label readability** — Are icon labels fully visible and not cut off?
3. **Edge label overlap** — Do connection line labels overlap with icon labels?
4. **Container fit** — Are all icons fully inside their VPC / subnet containers?
5. **Overall balance** — Is the diagram evenly spaced and easy to read?

Report each visual issue as a `VISUAL-WARNING` in the review report, distinct from the XML-based rule checks (R01–R12).

## Installation

```bash
brew install drawio   # macOS
```

On Linux, download from the official draw.io GitHub releases page.

## Error Handling

If the `drawio` CLI is not found:

- The script exits with code `2` and outputs `SKIP_PNG_REVIEW=true`
- The `diagram-reviewer` should skip the visual review step and note in the report: "Visual review skipped (drawio CLI not available)"
- The XML-based rule checks (R01–R12) still run and determine pass/fail
