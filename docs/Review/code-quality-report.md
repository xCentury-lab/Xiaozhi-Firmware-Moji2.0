# コード品質レポート

> **レビュー日**: 2026-04-18
> **対象**: `build/` および `tools/` 配下の全 Python スクリプト

---

## 1. ファイル別品質スコア

| ファイル | 行数 | 品質 | 主要指摘 |
|---|---|---|---|
| `build/build_matrix.py` | 243 | B | スケルトン。設計良好。型ヒント使用 |
| `build/inject_assets.py` | 132 | B | スケルトン。構造明確 |
| `build/verify_build.py` | 168 | A | ほぼ実装完了。堅実なロジック |
| `tools/inspect_ota.py` | 173 | A+ | 完成度最高。判定ロジック秀逸 |
| `tools/patch_bin.py` | 45 | C | 動作するが簡素すぎる |
| `tools/patch_bin_2.py` | 45 | D | バグあり（検証ロジック不整合） |
| `tools/patch_release_zip.py` | 57 | B+ | 機能的。URL直接DL機能付き |
| `tools/check.py` | 14 | D | パスのハードコーディング |
| `tools/check_bin.py` | 11 | D | パスのハードコーディング |

---

## 2. バグ報告

### BUG-001: patch_bin_2.py の検証ロジック不整合

**重要度**: 中
**ファイル**: `tools/patch_bin_2.py:36-41`

```python
# 問題箇所
OLD_URL = b'https://xiaozhi.jp/xiaozhi/ota/'     # xiaozhi.jp を置換
# ...
if b'classism.net' in patched and b'tenclass.net' not in patched:
    #                              ^^^^^^^^^^^^^^^^
    # xiaozhi.jp を置換したのに tenclass.net の不在をチェックしている
```

**期待動作**: `xiaozhi.jp` が残存していないことを検証すべき

**修正案**:
```python
if b'classism.net' in patched and OLD_URL not in patched:
    print("OK: 新URL確認")
    print("OK: 旧URL消去確認")
```

---

## 3. コード重複

### DUP-001: patch_bin.py と patch_bin_2.py

両ファイルは `OLD_URL` の値のみ異なり、他のロジックは完全に同一。

| 行 | patch_bin.py | patch_bin_2.py |
|---|---|---|
| 3 | `b'https://api.tenclass.net/xiaozhi/ota/'` | `b'https://xiaozhi.jp/xiaozhi/ota/'` |
| 残り全行 | 同一 | 同一 |

**推奨**: 1ファイルに統合し、`--preset` または `--old-url` 引数で切替

### DUP-002: sha256_of_file()

`build_matrix.py:67-72` と `verify_build.py:47-52` で同一関数が重複定義。

**推奨**: `build/utils.py` に共通関数として切出し

---

## 4. ハードコーディング

### HARD-001: check.py

```python
zip_path = "v2.2.4_waveshare-esp32-s3-touch-lcd-1.85c_patched.zip"
```

パスが固定されており、他のバージョン/ボードでは使えない。

### HARD-002: check_bin.py

```python
bin_path = "v2.0.3_esp32-s3-touch-lcd-1.85c\\merged-binary_patched.bin"
```

Windows パス形式でハードコーディング。バージョンも古い（v2.0.3）。

### HARD-003: push.ps1

```powershell
git config user.name "xxc"
git config user.email "xxc@ctoch.jp"
```

ユーザー情報がスクリプトにハードコーディング。チームで共有する場合は環境変数化推奨。

---

## 5. 良い実装パターン

### GOOD-001: inspect_ota.py の判定ロジック

4パターンの網羅的判定が秀逸:
1. URL もキーワードも無し → Partial dump
2. 旧URLのみ → 未パッチ
3. 新URLのみ → パッチ済み
4. 両方存在 → パッチ途中

### GOOD-002: verify_build.py の段階的検証

6段階の検証が論理的に構成:
```
サイズ → OTA URL → 禁止文字列 → 言語キーワード → manifest → SHA256
```

### GOOD-003: build_matrix.py のCLI設計

```python
parser.add_argument("--board", help="単一ボードのみビルド")
parser.add_argument("--lang", help="単一言語のみビルド")
parser.add_argument("--all", action="store_true")
parser.add_argument("--only-failed", action="store_true")
```

開発時（単一ビルド）と量産時（全組合せ）の両方に対応する設計。

### GOOD-004: matrix.yaml のQA統合

```yaml
qa:
  forbidden_strings:
    - "tenclass.net"
  required_ota_url: "classism.net"
```

ビルド定義とQA基準を同一ファイルで管理する設計は、乖離防止に効果的。

---

## 6. 依存関係

### 6-1. Python パッケージ

| パッケージ | 使用箇所 | 必須度 |
|---|---|---|
| `pyyaml` | build_matrix.py, verify_build.py | 必須 |
| `Pillow` | 将来の generate_board_logos.py | STEP1-F |

### 6-2. 外部ツール

| ツール | 使用箇所 | 必須度 |
|---|---|---|
| ESP-IDF (idf.py) | build_matrix.py | 必須 |
| ffmpeg | 音声変換 | STEP1-C |
| @lvgl/lv_img_conv | ロゴC配列変換 | STEP1-B |
| ImageMagick | 画像変換 | STEP1-B |

### 6-3. 未作成ファイル

- `requirements.txt` — Python 依存関係
- `scripts/generate_board_logos.py` — ロゴ自動生成（build-plan で言及）
- `docs/glossary-ja.md` — 日本語用語集（STEP2用）

---

## 7. Python バージョン互換性

コードベースは Python 3.11+ を対象としている:
- `list[str]` 型ヒント（build_matrix.py:55, verify_build.py:55）は Python 3.9+ で動作
- f-string 使用は Python 3.6+ で動作
- `Path` 使用は Python 3.4+ で動作

**実質的な最低要件: Python 3.9+**（型ヒント構文による）

---

*本レポートは静的コードレビューに基づく。実行テストは未実施。*
