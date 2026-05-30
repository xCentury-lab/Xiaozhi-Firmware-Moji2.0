---
name: xiaozhi-build
description: Xiaozhi ファーム (78/xiaozhi-esp32 v2.2.4) を 4 軸カスタマイズ要件 (ja-JP / Alexa+Hi,ESP / classism.net OTA / ja-JP 音声マスタ反映) で自動ビルドし、firmware/ 配下に配置 + manifest.json 生成する。ボード SKU を引数で受け取る。オプションで書込まで実行。
argument-hint: "<board-sku> [--port /dev/ttyACM0] [--hw-rev V1.0] [--date YYYYMMDD] [--no-build]"
allowed-tools: Bash(python3 *), Bash(source *), Bash(ls *), Bash(cat *), Bash(grep *), Read, Edit
---

# xiaozhi-build: Xiaozhi ファーム 4 軸カスタマイズ自動ビルド

## このスキルが担うこと

以下の **4 軸カスタマイズ要件**を、指定されたボード SKU の Xiaozhi ファームに一括適用します。要件詳細は [`docs/customization-spec.md`](/home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-VoCat/docs/customization-spec.md) 参照。

| # | 軸 | 適用内容 |
|---|---|---|
| 1 | UI 言語 | `CONFIG_LANGUAGE_JA_JP=y` |
| 2 | ウェイクワード | `CONFIG_SR_WN_WN9_ALEXA=y` + `CONFIG_SR_WN_WN9_HIESP=y` |
| 3 | OTA URL | `CONFIG_OTA_URL="https://classism.net/xiaozhi/ota/"` |
| 4 | **ja-JP 音声マスタ** (発音修正) | `assets/sounds/locales/ja-JP/*.ogg` を本家 source に注入 (ja-JP 限定) |

> **2026-05-24 軸定義変更**: 旧「ブートロゴ ("和合")」軸と「ブランド定義」軸を削除。ロゴパッチング処理 (lcd_display.cc 改変) は本 skill から除外済。Brand 情報は manifest.json への記録のみ。

## 使い方

### ユーザーからの典型的な指示

> 「waveshare-1.85c のカスタム版ファーム作って」
> 「yunliao-s3 用に作り直して」
> 「小智云聊-S3 のファームを作って、書込みもして」

### Claude の実行手順

1. **ボード SKU を確定**:
   - ユーザー指示の表記を `main/boards/<sku>/` のディレクトリ名に正規化
   - 例: 「waveshare-1.85c」→ `waveshare-esp32-s3-touch-lcd-1.85c`
   - 例: 「小智云聊-S3」「yunliao」→ `yunliao-s3`
   - 曖昧な場合は `ls /home/xxc/xiaozhi-work/xiaozhi-esp32/main/boards/` を実行して提示

2. **書込みの有無を確認**:
   - 「書込んで」「flash して」等の指示があれば `--port /dev/ttyACM0` を付ける（先に `ls /dev/ttyACM* /dev/ttyUSB*` でポート存在確認）
   - 指示なしなら書込みは行わず、ビルド + manifest 生成まで

3. **スクリプト実行** (長時間処理なのでバックグラウンド推奨):
   ```bash
   python3 /home/xxc/project/Xiaozhi-Firmware-VoCat/.claude/skills/xiaozhi-build/scripts/xiaozhi_build.py <board-sku> [--port <port>]
   ```

4. **完了報告**:
   - 生成ファームのパス、SHA256、サイズ、使用フォント、配置ディレクトリを要約して返す
   - 書込み実行時は「Hard resetting via RTS pin」確認まで

## スクリプトの内部動作（参考）

1. `main/CMakeLists.txt` から `<board-sku>` に対応する `CONFIG_BOARD_TYPE_*` シンボルを逆引き
2. `main/boards/<sku>/config.json` の `sdkconfig_append` を読んでボード固有 sdkconfig を取得（例: yunliao-s3 の `CONFIG_USE_DEVICE_AEC=y`）
3. sdkconfig を編集（ボード切替 + 4 軸カスタマイズ）
4. **ja-JP 音声マスタを本家 source に注入** (ja-JP build 時のみ): `cp -p assets/sounds/locales/ja-JP/*.ogg main/assets/locales/ja-JP/`
5. ボードが変わった場合のみ `idf.py fullclean`
6. `esptool merge_bin` で `merged-binary.bin` を生成
7. `firmware/v2.2.4_<board>_V1.0_ja-JP_alexa-hiesp_company/` に全成果物を配置
9. `manifest.json` 自動生成（SHA256, サイズ, 使用フォント, ボード extras を記録）
10. `--port` 指定時は `esptool write_flash` でフラッシュ

## 前提環境

| 項目 | パス |
|---|---|
| 本家ソース | `/home/xxc/xiaozhi-work/xiaozhi-esp32` (環境変数 `XIAOZHI_SRC` でも可) |
| ESP-IDF | `/home/xxc/esp/esp-idf` (v5.5.4) |
| プロジェクト | `/home/xxc/project/Xiaozhi-Firmware-VoCat` |
| 出力先 | `$PROJECT/firmware/v2.2.4_<board>_V1.0_ja-JP_alexa-hiesp_company/` |

## 注意事項

- **ビルド時間**: 初回 / ボード切替時は `fullclean` が走るため 7〜10 分。同一ボード再ビルドは 1〜3 分
- **sdkconfig は直接編集**: matrix.yaml 経由の量産ビルドパイプラインとは独立。量産時は [`build/build_matrix.py`](/home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-VoCat/build/build_matrix.py) 側に統合予定
- **既存 firmware ディレクトリ**: 同名ディレクトリが存在する場合は**上書き**します（旧 jarvis-hiesp 版等は別ディレクトリなので影響なし）
- **書込先 `/dev/ttyACM0`**: `write_flash` 直後に USB 再列挙でポート名が変わる場合あり。ポートが消えた場合は数秒待って再確認

## 関連ドキュメント

- [customization-spec.md](/home/xxc/project/Xiaozhi-Firmware-VoCat/docs/customization-spec.md) — 4 軸要件の正式定義
- [wake-word-selection.md](/home/xxc/project/Xiaozhi-Firmware-VoCat/docs/operations/wake-word-selection.md) — ウェイクワード選定根拠
- [matrix.yaml](/home/xxc/project/Xiaozhi-Firmware-VoCat/build/matrix.yaml) — 量産ビルドマトリクス（将来統合先）
