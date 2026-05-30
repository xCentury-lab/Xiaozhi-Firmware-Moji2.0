---
name: xiaozhi-ota-rewrite
description: 既存の Xiaozhi ファーム binary (merged-binary.bin / フルフラッシュダンプ) に埋め込まれた OTA サーバ URL を in-place で書き換える。再ビルド不要。デフォルトで `api.tenclass.net` → `classism.net` に置換。任意でデバイス読み出し → 書換 → 書戻しのフルパイプラインも実行。
argument-hint: "<bin-file> [--url <new-url>] [--port /dev/ttyACM0] [--write-back] [--read-from-device]"
allowed-tools: Bash(python3 *), Bash(source *), Bash(esptool.py *), Bash(ls *), Bash(strings *), Bash(grep *), Bash(md5sum *), Bash(cp *), Read, Edit
---

# xiaozhi-ota-rewrite: OTA URL の in-place 書き換え

## このスキルが担うこと

すでに存在する Xiaozhi ファーム `.bin` 内の OTA サーバ URL を、ソース再ビルドなしに書き換えます。

| 項目 | 内容 |
|---|---|
| 対象ファイル | `merged-binary.bin` / `flash_full_*.bin` などの bundled image |
| デフォルト置換 | `https://api.tenclass.net/xiaozhi/ota/` (37B) → `https://classism.net/xiaozhi/ota/` (33B + NUL×4) |
| 同サイズ維持 | 末尾を NUL でパディングしファイルサイズ・以降オフセットを完全保持 |
| バックアップ | `<file>.orig` を自動作成（既存なら上書きしない）|

## 使い方

### ユーザーからの典型的な指示

> 「`merged-binary.bin` の OTA を書き換えて」
> 「実機からダンプして OTA 変えて書き戻して」
> 「`flash_full_16MB.bin` の OTA を `https://my.server.com/ota/` にして」

### Claude の実行手順

#### Mode A: ファイル単体パッチ（最頻出）

ファイルパスだけ指定された場合:

```bash
python3 /home/xxc/project/Xiaozhi-Firmware-VoCat/.claude/skills/xiaozhi-ota-rewrite/scripts/patch_ota_url.py <bin-file>
```

URL 指定がある場合:

```bash
python3 .../patch_ota_url.py <bin-file> --url https://classism.net/xiaozhi/ota/
```

スクリプトは:
1. `<file>.orig` バックアップ作成（既存はスキップ）
2. 既知の OTA URL を 1 箇所だけ検索（複数見つかった場合はエラー終了で安全停止）
3. 新 URL + NUL パディングで in-place 書き換え
4. オフセット / md5 / サイズ不変を report

#### Mode B: 実機ダンプ → パッチ

「実機から読んで OTA 書き換え」の指示の場合、先にダンプ:

```bash
# 1) ダウンロードモード投入を依頼（実機側）:
#    BOOT を押しながら RST を一度押し、BOOT を離す
# 2) ダンプ:
source /home/xxc/esp/esp-idf/export.sh
esptool.py --chip esp32s3 -p /dev/ttyACM0 -b 921600 \
  --before no_reset --after no_reset \
  read_flash 0 <flash-size> <output-bin>
# 3) パッチ:
python3 .../patch_ota_url.py <output-bin>
```

`<flash-size>` は事前に `flash_id` で確認するか、SKU 既知値を使う（watch=32MB=`0x2000000`、AI-Buddy robot=16MB=`0x1000000`）。

#### Mode C: 書き戻しまで（`--write-back` 相当の指示）

Mode A or B のあと:

```bash
esptool.py --chip esp32s3 -p /dev/ttyACM0 -b 921600 \
  --before no_reset --after hard_reset \
  write_flash 0x0 <patched-bin>
```

書き戻し後は実機で正常起動するか確認すること。

## 重要: ハッシュ整合性

ESP-IDF の app image には末尾に SHA-256 ハッシュが付与される。app パーティション内の文字列を書き換えるとこのハッシュが不整合になり、bootloader 側でハッシュ検証が有効な場合は **起動しない**。

| 状態 | 影響 |
|---|---|
| Secure Boot 無効 + `CONFIG_SECURE_BOOT_ALLOW_SHORT_APP_PARTITION` 等が default | 多くの場合警告のみで起動する（実績あり） |
| Secure Boot 有効 / 厳格な hash check | **起動失敗** — 必ず `.orig` から復元できる状態で実施 |

事前に既存 OEM ビルド (`firmware/v2.2.4_*_company/`) で再ビルド版が利用可能か確認し、可能ならそちら推奨。in-place パッチは「再ビルドが間に合わない」「ソースが手元にない既存個体の救済」が主用途。

## 再ビルドとの使い分け

| 状況 | 推奨手段 |
|---|---|
| 新規 SKU の OEM 量産 | [`xiaozhi-build`](../xiaozhi-build/SKILL.md) スキル（ソースから 5 軸カスタマイズ）|
| 既存ファームの URL だけ変えたい | **本スキル** |
| 出荷前個体の URL 差し替え | 本スキル（事前に `.orig` 確保） |
| ハッシュ厳格な構成 | 必ず再ビルド |

## 前提環境

| 項目 | パス |
|---|---|
| ESP-IDF | `/home/xxc/esp/esp-idf` (esptool.py 経由) |
| プロジェクト | `/home/xxc/project/Xiaozhi-Firmware-VoCat` |
| スクリプト | `.claude/skills/xiaozhi-ota-rewrite/scripts/patch_ota_url.py` |

## 注意事項

- **NUL パディング**: C 文字列なので末尾 NUL で正しく終端され、新 URL のみが有効。残バイトは無害
- **長さ制約**: 新 URL は元 URL 以下の長さでなければならない（`https://api.tenclass.net/xiaozhi/ota/` = 37B が上限）
- **ダウンロードモード**: 連続して esptool を呼ぶ場合は `--before no_reset --after no_reset` で download mode を維持。詳細は [`firmware/README.md`](/home/xxc/project/Xiaozhi-Firmware-VoCat/firmware/README.md) の「ダウンロードモード（ROM bootloader）への手動投入」セクション参照
- **検出される URL は 1 箇所のみ**: app パーティション内の単一インスタンス。複数個所検出された場合スクリプトはエラー終了する（誤書換防止）
- **実績**: v2.2.4 / v2.2.6 系 firmware（waveshare-1.85c, waveshare-2.06, AI-Buddy robot 等）で in-place パッチ成功確認済み

## 関連ドキュメント

- [`firmware/README.md`](/home/xxc/project/Xiaozhi-Firmware-VoCat/firmware/README.md) — ファーム配置とダウンロードモード手順
- [`xiaozhi-build` スキル](../xiaozhi-build/SKILL.md) — ソースからの再ビルド方式
- [`docs/customization-spec.md`](/home/xxc/project/Xiaozhi-Firmware-VoCat/docs/customization-spec.md) — 5 軸カスタマイズ要件正式定義
