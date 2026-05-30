# OTA URL の in-place 書き換え

> **対象**: 既存ファーム binary（`merged-binary.bin` / `flash_full_*.bin`）の OTA サーバ URL を再ビルドなしで変更したい場合
> **対象読者**: ファームエンジニア・サポート・OEM オペレータ
> **作成日**: 2026-05-24

---

## 概要

Xiaozhi ファームには `https://api.tenclass.net/xiaozhi/ota/` のような **OTA サーバ URL が文字列として埋め込まれています**。OEM 配布版で自社 OTA サーバ（`https://classism.net/xiaozhi/ota/`）に切り替える際、本来はソース再ビルドが必要ですが、**長さが同等以下の URL であれば in-place バイナリパッチで対応可能**です。

### 適用シナリオ

| シナリオ | 推奨手段 |
|---|---|
| 新規 SKU の OEM 量産（ソースあり） | [`xiaozhi-build`](../../.claude/skills/xiaozhi-build/SKILL.md) スキル（ソースから再ビルド） |
| **既存ファームの URL だけ変えたい** | **本手順（in-place パッチ）** |
| 出荷前個体の URL 差し替え | 本手順（事前に `.orig` バックアップ確保） |
| Secure Boot 厳格な構成 | 必ず再ビルド（in-place 不可）|

---

## 原理

### URL の格納方式

esp-idf の app パーティション内に **NULL 終端 C 文字列** として埋め込まれている。位置は `strings` + `grep` で簡単に特定できる:

```bash
strings merged-binary.bin | grep -E "https?://.*ota"
# https://api.tenclass.net/xiaozhi/ota/

grep -aob "https://api.tenclass.net/xiaozhi/ota/" merged-binary.bin
# 170003:https://api.tenclass.net/xiaozhi/ota/   ← オフセット 0x29813
```

### in-place パッチの仕組み

| 項目 | 値（例） |
|---|---|
| 元 URL | `https://api.tenclass.net/xiaozhi/ota/` (37 バイト) |
| 新 URL | `https://classism.net/xiaozhi/ota/` (33 バイト) |
| パディング | NUL バイト × 4 個（37 - 33 = 4） |
| ファイルサイズ | 不変（37 バイト枠を完全に再利用） |
| 以降のオフセット | 不変（パディングで埋めるため） |

C 文字列は NUL で終端するため、33 バイト目以降の NUL は無視され、新 URL のみが有効になる。

---

## 実行手順

### スキル経由（推奨）

[`xiaozhi-ota-rewrite`](../../.claude/skills/xiaozhi-ota-rewrite/SKILL.md) スキルにスクリプト化されている:

```bash
python3 /home/xxc/project/Xiaozhi-Firmware-VoCat/.claude/skills/xiaozhi-ota-rewrite/scripts/patch_ota_url.py \
  /path/to/merged-binary.bin

# URL を別のものにする場合:
python3 .../patch_ota_url.py /path/to/merged-binary.bin \
  --url "https://my.example.com/ota/"
```

スクリプトの安全装置:

1. `<file>.orig` を自動バックアップ（既存なら上書きしない）
2. 既知 URL（`https://api.tenclass.net/xiaozhi/ota/`）を 1 箇所だけ検索 — 複数検出時はエラー終了
3. 新 URL の長さが元 URL を超える場合はエラー終了
4. パッチ後にファイルサイズ・既知 URL 不在・新 URL 存在を再検証

### 手動実行（参考）

```python
old = b"https://api.tenclass.net/xiaozhi/ota/"
new = b"https://classism.net/xiaozhi/ota/"
patch = new + b"\x00" * (len(old) - len(new))
with open(path, "r+b") as f:
    data = f.read()
    assert data.count(old) == 1, "expected exactly 1 occurrence"
    f.seek(data.index(old))
    f.write(patch)
```

---

## ⚠️ 重要: SHA-256 ハッシュ整合性

### リスク

ESP-IDF の app image には末尾に SHA-256 ハッシュが付与される。**app パーティション内の文字列を書き換えるとこのハッシュが不整合**になり、bootloader 側でハッシュ検証が有効な場合は **起動しない**:

| デバイス構成 | 影響 |
|---|---|
| Secure Boot 無効 + 緩い hash check | 多くの場合警告のみで起動する（実績あり）|
| Secure Boot 有効 / 厳格な hash check | **起動失敗** — 復元できる状態で実施 |

### 実績

| ファーム | パッチ後の起動 | 備考 |
|---|---|---|
| v2.2.4 waveshare-1.85c | ✓ | `_company` ビルドと併用 |
| v2.2.6 waveshare-2.06 | ✓ | 単体パッチで正常起動 |
| v2.2.6 esp-vocat | ✓ | 単体パッチで正常起動 |
| v2.2.6 AI-Buddy robot | ✓ | 単体パッチで正常起動 |

→ 現在の Xiaozhi 構成では、**Secure Boot OFF のためハッシュ検証は警告レベル**。実用上は問題なし。

### 安全に運用するための原則

1. **必ず `.orig` バックアップを取る**（スクリプトが自動で作成）
2. パッチ後は **必ず実機で起動確認** してから本番に流す
3. 起動しなかった場合は `.orig` を書き戻して復旧
4. ソース有り＆量産時は再ビルドが本筋（[`xiaozhi-build`](../../.claude/skills/xiaozhi-build/SKILL.md) スキル）

---

## 検証

書き換え前後で `strings` で URL を確認:

```bash
strings merged-binary.bin | grep "xiaozhi/ota"
# 前: https://api.tenclass.net/xiaozhi/ota/
# 後: https://classism.net/xiaozhi/ota/
```

ファイルサイズが不変であることを確認:

```bash
ls -la merged-binary.bin merged-binary.bin.orig
# 両方とも同じバイト数
```

書き戻した実機で OTA リクエストが新 URL に向くか確認（実機ログまたは tcpdump で）。

---

## 関連ドキュメント

- [`xiaozhi-ota-rewrite` SKILL.md](../../.claude/skills/xiaozhi-ota-rewrite/SKILL.md) — スキル本体
- [`xiaozhi-build` SKILL.md](../../.claude/skills/xiaozhi-build/SKILL.md) — ソース再ビルド版
- [`docs/customization-spec.md`](../customization-spec.md) — 5 軸カスタマイズ要件
