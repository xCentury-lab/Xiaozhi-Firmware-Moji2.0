# Xiaozhi ファームウェア カスタム量産ビルド計画書

> **対象**: Waveshare シリーズ複数ボード
> **カスタマイズ軸**: ① 英語/日本語切替　② OTA URL 組込（classism.net）　③ ボード別カスタムロゴ　④ ボード別カスタム起動音
> **進行方針**: **STEP1（英語版）を完全に出荷可能な状態まで完成させた後、STEP2（日本語版）を開始**
> **各STEPの独立性**: STEP1だけで英語版製品を出荷可能。STEP2は日本語版を追加するための拡張
> **ビルド環境**: Windows 11 + ESP-IDF インストーラ / Ubuntu 22.04・24.04 + ESP-IDF
> **関連資産**: `Xiaozhi-Firmware-OTA/`（既存OTA URL書換ツール群）
> **作成日**: 2026-04-18
> **最終更新**: 2026-04-18（STEP1/STEP2の2段階構成へ再編成）

---

## 1. 目的と背景

### 1-1. 目的

本計画の最終目的は、**「ボード × 言語 × ブランド」の組合せで任意のファームウェアが1コマンドで量産できる状態**を作ることです。ただしリスク分散と早期市場投入のため、次の2段階で進めます。

**STEP 1（先行）: 英語版量産パイプラインの確立 → 出荷可能にする**
- ESP-IDF 環境でビルドできる状態を作り、英語UIのファームを量産可能にする
- ボード別カスタムロゴ・起動音・OTA URL をビルド時に組み込める仕組みを確立
- Waveshare 主要ボードの英語版を出荷可能な品質まで仕上げる
- **この時点で海外顧客・展示会・営業サンプルに対して出荷可能**

**STEP 2（後続）: 日本語版の追加 → 日本市場向けに展開**
- 日本語翻訳アセット（`ja-JP`）を制作
- 既存のSTEP1パイプラインに日本語オプションを追加するだけで量産可能にする
- 日本語版の QA・出荷フローを確立
- **この時点で日本国内法人・BtoC顧客に対して日本語版を出荷可能**

### 1-2. 背景

- 本家 [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) の既定言語は簡体中文で、ロゴも本家ブランド固定。
- 言語設定はコンパイル時の Kconfig で決まり、バイナリ後加工では完全差替不可（文字列長・フォント・音声データ依存）。
- ロゴ・起動音も `main/assets/` 配下の静的アセットとしてファームウェアに埋込まれるため、ビルド前にアセットを置換する必要がある。
- **英語アセット（`en-US`）は本家に既に存在している可能性が高く、日本語（`ja-JP`）は無い可能性が高い**。この非対称性が「STEP1先行・STEP2後続」にする最大の理由。
- 第三者フォーク（`iotsystem/`, `x22x22/`, `txp666/`）はドキュメント英語化レベルで、マルチブランド・マルチ言語の量産パイプラインは未整備。

### 1-3. 成果物の定義

| # | 成果物 | 形式 | 配置 | 完成時点 |
|---|---|---|---|---|
| A1 | **英語版 merged-binary**（Waveshare 1.85C、自社ロゴ・起動音） | `.bin` | `GUJIAN/v2.2.4_waveshare-esp32-s3-touch-lcd-1.85c_EN/` | STEP1 |
| A2 | **英語版 merged-binary（Waveshare全ボード）** | `.bin` | `GUJIAN/v2.2.4_{board}_EN/` | STEP1 |
| B1 | **日本語版 merged-binary**（Waveshare 1.85C） | `.bin` | `GUJIAN/v2.2.4_waveshare-esp32-s3-touch-lcd-1.85c_JA/` | STEP2 |
| B2 | **日本語版 merged-binary（Waveshare全ボード）** | `.bin` | `GUJIAN/v2.2.4_{board}_JA/` | STEP2 |
| C | **ビルド手順書**（本ファイル） | `.md` | `Xiaozhi-Device/` | 継続更新 |
| D1 | **量産ビルドスクリプト（STEP1版・英語のみ）** | `.py` / `.ps1` | `Xiaozhi-Firmware-OTA/build/` | STEP1 |
| D2 | **量産ビルドスクリプト（STEP2版・EN+JA対応）** | `.py` / `.ps1` | 同上 | STEP2 |
| E1 | **アセット管理構造（ロゴ・英語音声）** | フォルダ | `Xiaozhi-Firmware-OTA/assets/{board}/{brand}/` | STEP1 |
| E2 | **アセット管理構造（日本語翻訳・日本語音声）** | フォルダ | `Xiaozhi-Firmware-OTA/assets/{board}/{brand}/ja-JP/` | STEP2 |
| F | **ビルドマトリクス定義** | `.yaml` | `Xiaozhi-Firmware-OTA/build/matrix.yaml` | STEP1初版→STEP2拡張 |
| G | **Waveshare 全ボード対応可否表** | `.xlsx` | `xiaozhi-hardware-catalog/summary.xlsx` にカラム追加 | STEP1/STEP2各々追記 |
| H1 | **英語版出荷フロー手順書** | `.md` | `Xiaozhi-Device/shipping-workflow-en.md` | STEP1 |
| H2 | **日本語版出荷フロー手順書** | `.md` | `Xiaozhi-Device/shipping-workflow-ja.md` | STEP2 |

---

## 2. 対象ボードとバリエーション

### 2-1. 優先度A（STEP1最初に検証・パイプライン確立）

| sku | ボード名 | 役割 |
|---|---|---|
| waveshare-esp32-s3-touch-lcd-1.85c | ESP32-S3-Touch-LCD-1.85C | STEP1の最初の検証ターゲット |

### 2-2. 優先度B（STEP1後半で横展開）

`xiaozhi-hardware-catalog/waveshare/` 配下の 26 ボード全て。代表例:

- esp32-c6-touch-amoled-1.8
- esp32-p4-wifi6-touch-lcd-10.1
- その他 Waveshare Wiki 掲載モデル

### 2-3. ビルドマトリクスの設計

**STEP1完了時:**
```
バリエーション = ボード数 × 1言語(EN) × ブランド数
例: Waveshare 26ボード × EN × 1ブランド = 26 .bin
```

**STEP2完了時:**
```
バリエーション = ボード数 × 2言語(EN,JA) × ブランド数
例: Waveshare 26ボード × 2言語 × 1ブランド = 52 .bin
将来OEM拡張: 26ボード × 2言語 × 3ブランド = 156 .bin
```

### 2-4. 対象外

- M5Stack / LILYGO / ATK / その他メーカー — Waveshare 成功後に別計画で対応

---

## 3. 前提条件と必要リソース

### 3-1. ハードウェア

- Waveshare ESP32-S3-Touch-LCD-1.85C 実機 × **最低3台**（開発・QC・バックアップ）
- USB Type-C ケーブル、PC（Windows 11 または Ubuntu Desktop 22.04/24.04）
- 量産時: USB Hub・焼込治具

### 3-2. ソフトウェア（ビルド環境）

| ツール | バージョン | 用途 | Windows | Linux |
|---|---|---|---|---|
| ESP-IDF | **v5.5.2+ 必須**（推奨 v5.5.4） | ファームウェアビルド | インストーラ | `install.sh` |
| Git | 最新 | ソース管理 | Git for Windows | `apt install git` |
| Python | 3.10+ | スクリプト／アセット変換 | 3.11+ 推奨 | OS 同梱 |
| esptool.py | ESP-IDF 同梱 | 焼込・Flash読み書き | COM ポート | `/dev/ttyUSB0` |

> **環境構築の詳細手順**: Windows → [setup/windows.md](setup/windows.md) / Linux → [setup/linux.md](setup/linux.md)

### 3-3. ソフトウェア（アセット制作）

| ツール | 用途 | STEP1必須 | STEP2必須 |
|---|---|---|---|
| Figma / Illustrator | ロゴデザイン | ○ | △（既存流用） |
| LVGL Image Converter | PNG→C配列変換 | ○ | △（既存流用） |
| Audacity / ffmpeg | 起動音編集・変換 | ○ | ○（日本語TTSが必要な場合） |
| ImageMagick / cwebp | PNG↔WebP変換 | ○ | ○ |
| DeepL / 翻訳会社 | 日本語翻訳 | × | ○ |

### 3-4. 素材（著作権クリア済み）

| 素材 | STEP1必須 | STEP2必須 |
|---|---|---|
| 自社ロゴ（SVGマスター） | ○ | 流用 |
| 英語起動音 | ○ | 流用可 |
| CJKフォント（Noto Sans JP等） | × | ○ |
| 日本語UI翻訳 | × | ○ |
| 日本語音声（該当する場合） | × | ○ |

### 3-5. サーバー側

- `classism.net/xiaozhi/ota/` が稼働
- MQTT / WebSocket エンドポイントURLも決定済み
- OTAレスポンスのJSONスキーマが本家互換

---

## 4. 全体スケジュール

```
[STEP 0: 共通基盤]   (1〜2日)  ESP-IDF構築＋中国語版再現
         ↓
[STEP 1: 英語版]     (8〜10日)  英語UI + ロゴ + 起動音 + OTA + 量産 + QA + 出荷
         ↓  ★英語版リリース★
[STEP 2: 日本語版]   (6〜8日)   日本語アセット制作 + マトリクス拡張 + QA + 出荷
         ↓  ★日本語版リリース★
```

**合計目安: 15〜20営業日**（1名作業想定）

| Phase | 内容 | 工数 | ステップ |
|---|---|---|---|
| 0-A | 事前調査（Kconfig・アセットパス） | 1〜2日 | STEP0 |
| 0-B | ESP-IDF環境構築 | 0.5日 | STEP0 |
| 0-C | 中国語版ビルド再現 | 0.5日 | STEP0 |
| **1-A** | **英語化ビルド（1.85C）** | 1日 | **STEP1** |
| **1-B** | **カスタムロゴ組込（1.85C）** | 1〜2日 | **STEP1** |
| **1-C** | **カスタム起動音組込（1.85C）** | 1〜2日 | **STEP1** |
| **1-D** | **ビルドマトリクスv1（英語専用）** | 1日 | **STEP1** |
| **1-E** | **英語版QA** | 1日 | **STEP1** |
| **1-F** | **Waveshare全ボード英語版展開** | 2〜3日 | **STEP1** |
| **1-G** | **英語版出荷フロー確立** | 1日 | **STEP1 → 🚀出荷可能** |
| **2-A** | **日本語アセット制作（ja-JP新規）** | 2〜3日 | **STEP2** |
| **2-B** | **日本語ビルド（1.85C）** | 1日 | **STEP2** |
| **2-C** | **日本語UI調整（フォント・行間）** | 1日 | **STEP2** |
| **2-D** | **ビルドマトリクスv2（EN+JA対応）** | 0.5日 | **STEP2** |
| **2-E** | **日本語版QA** | 1日 | **STEP2** |
| **2-F** | **Waveshare全ボード日本語版展開** | 1〜2日 | **STEP2** |
| **2-G** | **日本語版出荷フロー統合** | 0.5日 | **STEP2 → 🚀出荷可能** |

---

# 📦 STEP 0: 共通基盤整備

> **目的**: STEP1/STEP2 共通の土台を作る
> **工数**: 1〜2日
> **完了条件**: 中国語版が自前ビルドで焼込成功

## 5. Phase 0-A: 事前調査

### 5-1. Kconfig とアセット構造の確認

```
xiaozhi-esp32/
├── main/
│   ├── Kconfig.projbuild              # LANGUAGE / OTA_URL / BOARD_TYPE 定義
│   ├── assets/
│   │   ├── zh-CN/                     # 中国語UI（既存）
│   │   ├── en-US/                     # 英語UI（★STEP1で使用、存在確認が最重要）
│   │   ├── ja-JP/                     # 日本語UI（★無ければSTEP2で新規作成）
│   │   ├── logos/                     # ロゴ画像
│   │   └── sounds/                    # 起動音・効果音
│   └── boards/{board_sku}/
│       ├── config.json
│       ├── boot_logo.c
│       └── CMakeLists.txt
└── scripts/
    ├── release.py
    └── gen_assets.py
```

**最優先確認事項:**

- [x] `main/assets/locales/en-US/` の有無 — ✅ **v2.2.4 に存在**（language.json 58行 + 音声 6種）
- [x] `main/assets/locales/ja-JP/` の有無 — ✅ **v2.2.4 に存在**（language.json 58行 + 音声 6種、他計 39 ロケール）
- [x] `LANGUAGE_EN_US` / `LANGUAGE_JA_JP` の Kconfig — ✅ `main/Kconfig.projbuild` に定義済み
- [ ] 画像仕様（解像度・カラーフォーマット・埋込方式）
- [ ] 音声仕様（サンプルレート・コーデック・再生トリガー）

> **2026-04-18 実測所見**: `main/assets/locales/` には `ar-SA bg-BG ca-ES cs-CZ da-DK de-DE el-GR en-US es-ES fa-IR fi-FI fil-PH fr-FR he-IL hi-IN hr-HR hu-HU id-ID it-IT ja-JP ko-KR ms-MY nb-NO nl-NL pl-PL pt-PT ro-RO ru-RU sk-SK sl-SI sr-RS sv-SE th-TH tr-TR uk-UA vi-VN zh-CN zh-TW` の 39 言語が同梱されている。各言語で `language.json`（UI 文字列 58行）と 6 種の OGG 音声（`0.ogg`〜`9.ogg`、`activation.ogg`、`welcome.ogg` 等）が完全に対応済み。**STEP2 の「日本語アセット制作（2〜3日）」想定は、本家翻訳を採用する前提で 0〜0.5日（用語統一レビューのみ）に短縮可能**。ただし本家翻訳の OEM 用途適性（例: `HELLO_MY_FRIEND: こんにちは、友達！` が B2B 文脈で妥当か）を営業・サポートとレビュー必須。詳細: [Review/linux-environment-setup-log.md](Review/linux-environment-setup-log.md) § 3-2。

### 5-2. 出力

- `docs/asset-spec.md` — 画像/音声の仕様書
- `docs/translation-source.md` — 翻訳対象ファイル一覧（STEP2で使用）

## 6. Phase 0-B: ESP-IDF 環境構築

### 6-1. Windows 11 の場合

1. [ESP-IDF Windows Installer](https://dl.espressif.com/dl/esp-idf/) から v5.5.x をダウンロード（v5.5.2+ 必須、推奨 v5.5.4）
2. 管理者権限でオフラインインストーラ実行
3. インストールパスは短い英数字（例: `C:\esp\v5.5\esp-idf`）
4. ターゲット `ESP32-S3` を選択
5. `ESP-IDF 5.5 PowerShell` ショートカットから起動

```powershell
idf.py --version
cd $env:IDF_PATH\examples\get-started\hello_world
idf.py set-target esp32s3
idf.py build
```

**注意事項:**
- ESP-IDF環境変数は専用ターミナル内でのみ有効
- ウイルス対策ソフトは `C:\esp\` を除外
- Windows Defender の Controlled Folder Access は無効化

### 6-2. Ubuntu 22.04 / 24.04 の場合

```bash
# 1. 必要パッケージ
sudo apt update && sudo apt install -y \
  git wget curl flex bison gperf python3 python3-pip python3-venv \
  cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0

# 2. USB シリアル権限
sudo usermod -a -G dialout $USER && newgrp dialout

# 3. Ubuntu 22.04 のみ: brltty 削除
sudo apt remove -y brltty

# 4. ESP-IDF インストール
mkdir -p ~/esp && cd ~/esp
git clone -b v5.5.4 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf && ./install.sh esp32s3
source export.sh

# 5. 動作確認
idf.py --version
cd ~/esp/esp-idf/examples/get-started/hello_world
idf.py set-target esp32s3
idf.py build
```

**注意事項:**
- `source export.sh` は毎回実行が必要（`get_idf` エイリアス登録を推奨）
- 詳細は [setup/linux.md](setup/linux.md) 参照

## 7. Phase 0-C: 中国語版ビルド再現

### Windows の場合

```powershell
cd C:\xiaozhi-work
git clone https://github.com/78/xiaozhi-esp32.git
cd xiaozhi-esp32
git checkout v2.2.4
git submodule update --init --recursive

python scripts/release.py waveshare-esp32-s3-touch-lcd-1.85c
idf.py set-target esp32s3
idf.py build

# 焼込前に必ずフルバックアップ
esptool.py -p COM7 -b 460800 read-flash 0x0 0x1000000 `
  GUJIAN/backup/waveshare-1.85c_stock_20260418.bin

idf.py -p COM7 flash monitor
```

### Linux (Ubuntu) の場合

```bash
cd ~/xiaozhi-work
git clone https://github.com/78/xiaozhi-esp32.git
cd xiaozhi-esp32
git checkout v2.2.4
git submodule update --init --recursive

source ~/esp/esp-idf/export.sh    # ESP-IDF 環境有効化
python scripts/release.py waveshare-esp32-s3-touch-lcd-1.85c
idf.py set-target esp32s3
idf.py build

# 焼込前に必ずフルバックアップ
esptool.py -p /dev/ttyUSB0 -b 460800 read_flash 0x0 0x1000000 \
  backup/waveshare-1.85c_stock_$(date +%Y%m%d).bin

idf.py -p /dev/ttyUSB0 flash monitor
# モニター終了: Ctrl+]
```

**完了条件:**
- [ ] 中国語メニューが表示される
- [ ] `api.tenclass.net` へOTA到達試行（ログで確認）
- [ ] `GUJIAN/backup/` にフルバックアップが保管されている

---

# 🚀 STEP 1: 英語版量産パイプラインの確立

> **目的**: 英語UI・自社ロゴ・自社起動音・OTA URL すべて組み込んだ英語版を量産可能にし、Waveshare全ボードで出荷可能な状態にする
> **工数**: 8〜10日
> **完了条件**: 英語版を任意のWaveshareボードで1コマンドビルド＆出荷可能
> **独立性**: このSTEPだけで英語版製品として単独出荷可能

## 8. Phase 1-A: 英語化ビルド（Waveshare 1.85C）

### 8-1. menuconfig で言語 + OTA URL 変更

```powershell
idf.py menuconfig
```

```
Xiaozhi Assistant
├── Default Language ......... English
└── OTA URL .................. https://classism.net/xiaozhi/ota/
```

### 8-2. 再ビルド＆焼込

```powershell
idf.py fullclean
idf.py build
idf.py -p COM7 flash monitor
```

### 8-3. 検証

- [ ] UIが全て英語
- [ ] 文字化けなし
- [ ] OTA接続先が `classism.net`（monitor ログで確認）
- [ ] 音声応答が正常
- [ ] 画面レイアウト崩れなし

**⚠️ `main/assets/en-US/` が存在しなかった場合**: STEP1 内で簡易翻訳アセット作成が必要（中国語文字列を英訳）。工数+1〜2日。

## 9. Phase 1-B: カスタムロゴ組込

### 9-1. ロゴ素材の準備

```
Xiaozhi-Firmware-OTA/assets/logos/
├── master/
│   └── company-logo.svg                              # ベクターマスター
├── waveshare-esp32-s3-touch-lcd-1.85c/
│   └── company/
│       ├── boot-logo-360x360.png                     # 起動画面用
│       └── boot-logo-360x360.c                       # LVGL C配列
└── ...（Waveshare他ボード分）
```

### 9-2. 画像フォーマット変換

```powershell
# LVGL Image Converter でC配列化
npm install -g @lvgl/lv_img_conv
lv_img_conv boot-logo-360x360.png `
    --color-format rgb565 `
    --output-format c_array `
    --binary-format true_color > boot-logo-360x360.c
```

### 9-3. ソース組込（方式選択）

| 方式 | 特徴 |
|---|---|
| C配列ヘッダ差替 | 最もシンプル、Flash効率良 |
| SPIFFS/LittleFS実行時ロード | 柔軟、パーティション設計必要 |
| Kconfig で `LOGO_SET` を切替 | 複数ブランド量産に最適 |

**推奨: Kconfig で `LOGO_SET` を切替**

```
Xiaozhi Assistant
└── Logo Set ................. Company / OEM_A / OEM_B / Stock
```

### 9-4. 検証

- [ ] 電源ON直後に自社ロゴ表示
- [ ] 色味正しい（RGB565劣化確認）
- [ ] 円形ディスプレイの場合、ロゴが円内に収まる
- [ ] 待機画面・設定画面のロゴ差替（該当する場合）
- [ ] Stock版（本家ロゴ）も別ビルドで生成可能

## 10. Phase 1-C: カスタム起動音組込

### 10-1. 音声素材の準備

```
Xiaozhi-Firmware-OTA/assets/sounds/
├── master/
│   ├── boot-chime.wav        # 44.1kHz/16bit マスター
│   ├── wake-ding.wav
│   ├── connect-ok.wav
│   └── error-buzz.wav
├── waveshare-esp32-s3-touch-lcd-1.85c/
│   └── company/
│       ├── boot-chime-16k.wav
│       └── boot-chime-16k.opus
└── ...
```

### 10-2. フォーマット変換＆音量正規化

```powershell
# サンプルレート統一（16kHz Mono）
ffmpeg -i master/boot-chime.wav -ar 16000 -ac 1 -sample_fmt s16 boot-chime-16k.wav

# 音量正規化（-14 LUFS）
ffmpeg -i boot-chime-16k.wav -af loudnorm=I=-14:TP=-1:LRA=11 boot-chime-16k-norm.wav

# Opus圧縮（任意）
ffmpeg -i boot-chime-16k.wav -c:a libopus -b:a 32k boot-chime-16k.opus
```

### 10-3. ソース組込（方式選択）

| 方式 | 特徴 |
|---|---|
| C配列（xxd） | 短い効果音向け、Flash効率良 |
| SPIFFS/LittleFS | 複数ファイル・長め音声向け |
| Kconfig で `SOUND_SET` を切替 | 量産向け |

**推奨: Kconfig で `SOUND_SET` を切替**

```
Xiaozhi Assistant
└── Sound Set ................ Company / OEM_A / OEM_B / Stock
```

### 10-4. 検証

- [ ] 電源ON時に起動音再生
- [ ] 音量適切・歪みなし
- [ ] 遅延なく再生開始（電源ONから2秒以内）
- [ ] ウェイクワード・接続完了・エラー音の差替（該当する場合）
- [ ] Stock版も別ビルドで生成可能

## 11. Phase 1-D: ビルドマトリクスv1（英語専用）

### 11-1. マトリクス定義ファイル（STEP1版）

`Xiaozhi-Firmware-OTA/build/matrix.yaml`:

```yaml
version: v2.2.4

defaults:
  ota_url: https://classism.net/xiaozhi/ota/
  brand: company

brands:
  company:
    logo_dir: assets/logos/{board}/company/
    sound_dir: assets/sounds/{board}/company/
    ota_url: https://classism.net/xiaozhi/ota/
  stock:
    logo_dir: null   # 本家ロゴ
    sound_dir: null  # 本家音声
    ota_url: https://api.tenclass.net/xiaozhi/ota/

# ★STEP1では English のみ★
languages:
  - English

boards:
  - sku: waveshare-esp32-s3-touch-lcd-1.85c
    target: esp32s3
    resolution: 360x360
    enabled: true
  # Phase 1-F で他ボード追加

output_pattern: "GUJIAN/v{version}_{board}_{lang}_{brand}/merged-binary.bin"
```

### 11-2. 量産ビルドスクリプト（STEP1版）

`Xiaozhi-Firmware-OTA/build/build_matrix.py`:

```python
# 疑似コード
import yaml, subprocess, shutil
from pathlib import Path

def build_one(board, lang, brand, config):
    print(f"=== {board['sku']} / {lang} / {brand['name']} ===")
    
    # 1. sdkconfig.defaults に言語・OTA URL 注入
    write_sdkconfig_defaults(board, lang, brand)
    
    # 2. ロゴ・起動音を main/ へコピー
    inject_logo(board['sku'], brand['name'])
    inject_sound(board['sku'], brand['name'])
    
    # 3. クリーンビルド
    subprocess.run(["idf.py", "fullclean"], check=True)
    subprocess.run(["idf.py", "set-target", board['target']], check=True)
    subprocess.run(["idf.py", "build"], check=True)
    
    # 4. 成果物を命名規則に従いコピー
    out_path = config['output_pattern'].format(
        version=config['version'],
        board=board['sku'],
        lang=lang.lower(),
        brand=brand['name']
    )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy("build/merged-binary.bin", out_path)
    
    # 5. manifest.json でトレーサビリティ
    write_build_manifest(out_path, board, lang, brand)
```

### 11-3. manifest.json（トレーサビリティ）

```json
{
  "board_sku": "waveshare-esp32-s3-touch-lcd-1.85c",
  "firmware_version": "v2.2.4",
  "language": "English",
  "brand": "company",
  "ota_url": "https://classism.net/xiaozhi/ota/",
  "logo_hash": "sha256:abc123...",
  "sound_hash": "sha256:def456...",
  "build_time": "2026-05-25T14:32:10+09:00",
  "builder": "xxc@ctoch.jp",
  "idf_version": "v5.5.4",
  "source_commit": "78/xiaozhi-esp32@v2.2.4",
  "binary_sha256": "sha256:789abc..."
}
```

## 12. Phase 1-E: 英語版QA

### 12-1. ビルド直後の自動検証

`Xiaozhi-Firmware-OTA/build/verify_build.py`:

- [ ] `merged-binary.bin` サイズが想定範囲（8〜10MB）
- [ ] `inspect_ota.py` で `classism.net` のみ検出、`tenclass.net` 不検出
- [ ] 文字列ダンプに英語キーワード存在（"Connecting", "Listening" 等）
- [ ] ロゴC配列のSHA256が期待値と一致
- [ ] 起動音ファイルのSHA256が期待値と一致
- [ ] `manifest.json` 全フィールド充足

### 12-2. 実機動作試験

- [ ] 初回起動（Wi-Fi未設定）→ カスタムロゴ表示→起動音再生
- [ ] Wi-Fi設定完了 → OTAサーバー（classism.net）到達
- [ ] 英語UIが正しく表示（全画面スクリーンショット取得）
- [ ] 音声対話が正常
- [ ] 連続稼働 1時間 → 再起動・メモリリーク無し
- [ ] 工場出荷リセット → 再現可能

### 12-3. 英語版 Golden Sample 機保管

1.85C の英語版1台を Golden Sample として保管。今後の英語QAは全数 Golden Sample と動作比較。

## 13. Phase 1-F: Waveshare 全ボード英語版展開

### 13-1. 横展開手順

1. `xiaozhi-hardware-catalog/summary.xlsx` から Waveshare 全SKU抽出
2. `matrix.yaml` の `boards:` に全ボード追加（`enabled: true`）
3. ボード別ロゴを自動生成（解像度差吸収）
4. `python build_matrix.py` を一括実行
5. 失敗ボードは個別トリアージ

### 13-2. ボード別ロゴ自動生成

```python
# generate_board_logos.py
from PIL import Image
BOARDS = {
    "waveshare-esp32-s3-touch-lcd-1.85c": (360, 360, "circle"),
    "waveshare-esp32-c6-touch-amoled-1.8": (368, 448, "rect"),
    # ...
}
master = Image.open("assets/logos/master/company-logo.png")
for sku, (w, h, shape) in BOARDS.items():
    resized = fit_to_canvas(master, w, h, shape)
    resized.save(f"assets/logos/{sku}/company/boot-logo-{w}x{h}.png")
```

### 13-3. 失敗時のトリアージ

| 症状 | 原因候補 | 対処 |
|---|---|---|
| `board_config.h not found` | ボード定義未整備 | 近いボード定義を流用 |
| `undefined reference to lv_xxx` | LVGL不整合 | `idf_component.yml` で版固定 |
| 画面真っ黒 | 表示ドライバ差異 | Waveshare Wiki参照 |
| ロゴが歪む | アスペクト比ミスマッチ | `generate_board_logos.py` で自動補正 |
| 起動音が鳴らない | I2S/DACピン定義不一致 | ボード `board.cc` を確認 |

### 13-4. 成功目標

- Waveshare主要ボード: 80%以上の初回ビルド成功率
- 失敗ボードは Phase 1-F 内で個別対応

## 14. Phase 1-G: 英語版出荷フロー確立 → 🚀出荷可能

### 14-1. 焼込フロー（工場向け）

```
[受注] → [SKU確定] → [英語版.bin取得] → [焼込治具で多台同時焼込]
  → [起動試験] → [Wi-Fiテスト] → [OTA疎通試験] → [梱包] → [出荷]
```

### 14-2. 焼込ツール

- `esptool.py` ベースのワンクリック焼込GUI
- 焼込後に manifest.json をシリアル番号と紐付けDB登録
- 不良品ロールバック・再焼込フロー定義

### 14-3. 配布チャネル（英語版）

- **Shopify 商品ページ（英語版）**: 海外顧客向けDLリンク提供
- **OTAサーバー（classism.net）**: 自動アップデート配信
- **展示会・営業サンプル**: 英語版サンプル機として即時出荷可能

### 14-4. STEP1 完了判定

- [x] Waveshare 1.85C の英語版が Golden Sample 準拠で量産可能
- [x] Waveshare全ボードのうち80%以上で英語版 `.bin` 生成成功
- [x] 焼込・QC・梱包・出荷の一連フローが確立
- [x] `shipping-workflow-en.md` が完成
- [x] 海外顧客に対して英語版製品を実出荷可能

**🚀 この時点で英語版は完全出荷可能。STEP2 開始判断へ。**

---

# 🗾 STEP 2: 日本語版の追加拡張

> **目的**: STEP1 で確立した量産パイプラインに日本語オプションを追加し、日本国内向け製品として出荷可能にする
> **工数**: 6〜8日
> **完了条件**: 日本語版を任意のWaveshareボードで1コマンドビルド＆出荷可能
> **前提**: STEP1 が完了していること
> **独立性**: STEP1 の英語版には影響を与えず、日本語オプションを追加するのみ

## 15. Phase 2-A: 日本語アセット制作

### 15-1. 翻訳ソース抽出

Phase 0-A の調査結果をもとに、`main/assets/zh-CN/` または `main/assets/en-US/` を翻訳ベースとする。

```powershell
# en-US が存在する場合（推奨）
Copy-Item -Recurse main/assets/en-US main/assets/ja-JP

# 無い場合は zh-CN から
Copy-Item -Recurse main/assets/zh-CN main/assets/ja-JP
```

### 15-2. 翻訳作業

| 項目 | 担当 | 手順 |
|---|---|---|
| UI文字列（.po / .json / .h） | 翻訳者 or DeepL+校正 | 機械翻訳で下訳→社内校正2名 |
| 用語統一 | 営業/サポート | `docs/glossary-ja.md` で固定 |
| ドメイン用語（自動車部品） | 社内 | 「適合車種」「型番」「整備」など |
| フォント | 開発 | Noto Sans JP / Source Han Sans JP サブセット生成 |

### 15-3. CJKフォント組込

```
main/assets/ja-JP/fonts/
└── noto-sans-jp-subset.ttf     # 必要なコードポイントのみ抽出
```

サブセット化でFlash容量を節約（フル収録版は4MB超、常用漢字サブセットで1MB以下）。

### 15-4. 翻訳品質管理

- `docs/glossary-ja.md` に用語固定
- 社内レビュー2名以上のクロスチェック
- 営業/サポート側での実機UI確認

### 15-5. 出力

`Xiaozhi-Firmware-OTA/assets/` 配下に日本語アセット構造を追加:

```
Xiaozhi-Firmware-OTA/assets/
├── logos/              # STEP1で構築済み（流用）
├── sounds/
│   └── {board}/company/
│       ├── boot-chime-16k.wav           # STEP1で構築済み
│       └── ja/                           # 日本語音声（必要な場合）
│           └── welcome-ja.wav
└── translations/                         # ★STEP2で新規
    └── ja-JP/
        ├── ui-strings.po
        └── glossary.md
```

## 16. Phase 2-B: 日本語ビルド（Waveshare 1.85C）

### 16-1. Kconfig で Japanese を選択肢に追加

本家 Kconfig.projbuild に Japanese が無い場合、ローカルでパッチ:

```
choice LANGUAGE
    prompt "Default Language"
    default LANGUAGE_ZH_CN

config LANGUAGE_ZH_CN
    bool "Chinese (Simplified)"

config LANGUAGE_EN_US
    bool "English"

config LANGUAGE_JA_JP
    bool "Japanese"     # ★追加

endchoice
```

`CMakeLists.txt` でも `ja-JP/` をビルド対象に含める。

### 16-2. menuconfig で Japanese 選択

```
Xiaozhi Assistant
└── Default Language → Japanese
```

### 16-3. ビルド＆焼込

```powershell
idf.py fullclean
idf.py build
idf.py -p COM7 flash monitor
```

### 16-4. 初回検証

- [ ] 日本語UIが表示される
- [ ] ひらがな・カタカナ・漢字すべて表示
- [ ] 文字化け・豆腐（□）ゼロ

## 17. Phase 2-C: 日本語UI調整

### 17-1. フォントサイズ・行間の調整

日本語は英語より視覚的に密度が高く、画面に収まらない問題が発生しやすい。

- [ ] メニュー項目が画面に収まる
- [ ] 長文表示での改行が自然
- [ ] フォントサイズを日本語専用に拡大/縮小

### 17-2. 翻訳違和感の修正

- [ ] 「録音中」「接続中」「音量」などの基本UIが自然
- [ ] エラーメッセージ・確認ダイアログも日本語として自然
- [ ] 半角カナへの意図せぬフォールバックなし

### 17-3. 修正反映

翻訳ファイル（`.po` / `.json`）を修正 → 再ビルド → 再検証 のループ。

## 18. Phase 2-D: ビルドマトリクスv2（EN+JA対応）

### 18-1. matrix.yaml の言語リスト拡張

```yaml
languages:
  - English
  - Japanese         # ★STEP2で追加
```

### 18-2. アセット注入ロジック拡張

`inject_assets.py` に日本語アセット対応を追加:

```python
def inject_translations(board_sku, brand, language):
    """言語別の翻訳アセットを main/assets/ へコピー"""
    if language == "Japanese":
        src = f"assets/translations/ja-JP/"
        dst = f"main/assets/ja-JP/"
        shutil.copytree(src, dst, dirs_exist_ok=True)
```

### 18-3. ビルド数の確認

```
STEP1完了時: 26ボード × 1言語 × 1ブランド = 26 .bin
STEP2完了時: 26ボード × 2言語 × 1ブランド = 52 .bin
```

### 18-4. 1.85C での動作確認

```powershell
python build_matrix.py --board waveshare-esp32-s3-touch-lcd-1.85c
# → 英語版と日本語版の2つの .bin が生成されることを確認
```

## 19. Phase 2-E: 日本語版QA

### 19-1. 自動検証

- [ ] `inspect_ota.py` で `classism.net` のみ検出
- [ ] 文字列ダンプに日本語キーワード存在（「接続中」「録音中」等）
- [ ] `manifest.json` の `language: Japanese` 確認
- [ ] CJKフォントファイルのハッシュ一致

### 19-2. 実機動作試験

- [ ] 初回起動 → カスタムロゴ → 起動音 → 日本語UI表示
- [ ] Wi-Fi設定・OTA疎通 → classism.net
- [ ] 全画面スクリーンショット取得（UI全網羅）
- [ ] 音声対話の応答が自然
- [ ] 連続稼働 1時間 安定
- [ ] 工場出荷リセット 再現可能

### 19-3. 日本語版 Golden Sample 機保管

1.85C の日本語版1台を Golden Sample として保管。

## 20. Phase 2-F: Waveshare 全ボード日本語版展開

### 20-1. 一括ビルド

```powershell
python build_matrix.py --lang Japanese
```

### 20-2. ボード固有の日本語調整

- 小画面ボード（1インチ未満）: フォントサイズを小さく、または簡潔な日本語に
- 大画面ボード（10インチ級）: フォントを大きくしてUI可読性向上

### 20-3. 失敗時対応

STEP1 と同じトリアージ表で対応。日本語特有の問題は:

| 症状 | 原因 | 対処 |
|---|---|---|
| 日本語が豆腐になる | CJKフォントサブセット不足 | 必要なコードポイント追加 |
| UI切れ（特に小画面） | 文字数超過 | 翻訳短縮または省略記号表示 |
| フォントが崩れる | ビルド時にTTFが埋込失敗 | `CMakeLists.txt` の組込確認 |

## 21. Phase 2-G: 日本語版出荷フロー統合 → 🚀出荷可能

### 21-1. 出荷フロー拡張

STEP1 の `shipping-workflow-en.md` をベースに `shipping-workflow-ja.md` を作成。主な差分:

- SKUコードに `_JA` サフィックス
- 梱包同梱物の日本語版マニュアル
- 日本国内対応（PSE / 電波法 技適）の確認

### 21-2. 配布チャネル（日本語版）

- **Shopify 商品ページ（日本語版）**: 日本国内顧客向けDLリンク
- **法人顧客向け**: 見積もり導線・法人割引ページから日本語版ファームウェア配布
- **OEM向け**: 日本語版OEMブランド版の個別ビルド

### 21-3. STEP2 完了判定

- [x] Waveshare 1.85C の日本語版が Golden Sample 準拠で量産可能
- [x] Waveshare全ボードのうち80%以上で日本語版 `.bin` 生成成功
- [x] `shipping-workflow-ja.md` が完成
- [x] 日本国内顧客に対して日本語版製品を実出荷可能

**🚀 この時点で日本語版も完全出荷可能。英語版・日本語版の両方が量産ラインに乗る。**

---

## 22. リスクと対策

| # | リスク | 影響 | 対策 | ステップ |
|---|---|---|---|---|
| 1 | 本家に `en-US` が無く STEP1 で英訳作業が発生 | STEP1遅延 | 事前調査(0-A)で確認、無ければSTEP1 内で簡易英訳 | STEP1 |
| 2 | 本家に `ja-JP` が無く翻訳工数超過 | STEP2 半年遅延 | 外部翻訳会社に早期見積もり、DeepL+校正で短縮 | STEP2 |
| 3 | ESP-IDF バージョン違いでビルド不可 | STEP0で停止 | 本家README推奨版に厳密合わせ | STEP0 |
| 4 | フォントで日本語が画面に収まらない | UI崩れ | フォントサイズ・行間を日本語専用に調整 | STEP2 |
| 5 | classism.net APIが本家非互換 | OTA動作不可 | STEP0時点でサーバーログ突合 | STEP0 |
| 6 | 焼込ミスでブリック | 検証機損失 | STEP0で必ずフルバックアップ | STEP0 |
| 7 | Waveshareボード表示ドライバ差異 | 横展開失敗 | Phase 1-F 前にWiki全ボード調査 | STEP1 |
| 8 | ライセンス（MIT）遵守漏れ | 法的リスク | 配布物にLICENSE同梱、改変点README明記 | 全体 |
| 9 | ロゴ解像度ミスマッチ | 歪み・表示欠け | `generate_board_logos.py` で自動リサイズ | STEP1 |
| 10 | 起動音の規格不一致 | 無音・歪み | Phase 0-A でボード別I2S仕様確定 | STEP0 |
| 11 | ロゴ素材の著作権 | 法的リスク | 社内制作またはOEM先から書面支給 | STEP1 |
| 12 | 音声素材の著作権 | 法的リスク | ロイヤリティフリー or 独自制作のみ | STEP1 |
| 13 | STEP2で英語版ビルドが壊れる（regression） | STEP1成果物棄損 | CIで英語版ビルドを自動再検証、STEP1成果物を凍結バージョン管理 | STEP2 |
| 14 | 量産中のアセット取違え | 誤出荷 | manifest.json + SHA256 で全数照合 | STEP1+2 |
| 15 | OEMブランド追加時の秘匿情報管理 | 情報漏洩 | Gitリポジトリ分割、OEM別privateで管理 | 全体 |
| 16 | 日本国内販売の法令遵守（PSE/技適） | 出荷不可 | STEP2-G前に法令確認、必要なら技適再取得 | STEP2 |

### 22-1. STEP2開始判断基準

STEP2 を開始する前に、以下を満たしていること:

- [x] STEP1 完了（Phase 1-G まで）
- [x] 英語版の市場反応を最低1ヶ月観測済み
- [x] 英語版のOTAアップデート実績（最低1回）
- [x] 日本市場ニーズの定量確認（見込み販売数など）

---

## 23. 第三者フォークを先行活用する場合（Plan A 並走）

STEP1 と並行して、以下フォークから英語 `.bin` を入手し、当座のサンプル機に利用可能。

| リポジトリ | 用途 |
|---|---|
| [iotsystem/xiaozhi-esp32](https://github.com/iotsystem/xiaozhi-esp32) | 英語ドキュメント＋一部英語ビルド |
| [x22x22/xiaozhi-esp32](https://github.com/x22x22/xiaozhi-esp32) | インストール手順を英語化 |
| [txp666/xiaozhi-esp32](https://github.com/txp666/xiaozhi-esp32) | Getting Started 英語版 |

**判断基準:**

- 第三者 `.bin` が動けば → 営業サンプル・展示会用に当座配布
- OTA URL は既存 `patch_bin.py` で上書き
- ただしロゴ・起動音はカスタム化不可
- **STEP1 Phase 1-B/1-C 完了時点で Plan A からは卒業**、自社パイプラインに一本化

---

## 24. マイルストーン

### STEP 0

| Milestone | 完了条件 | 想定日付 |
|---|---|---|
| M0-1 | ESP-IDF環境で中国語版を自前ビルド＆焼込成功 | 2026-05-01 |

### STEP 1（英語版）

| Milestone | 完了条件 | 想定日付 |
|---|---|---|
| M1-1 | 英語版 Waveshare 1.85C `.bin` 実機動作確認 | 2026-05-05 |
| M1-2 | カスタムロゴ入り英語版 `.bin` 実機動作確認 | 2026-05-10 |
| M1-3 | カスタム起動音入り英語版 `.bin` 実機動作確認 | 2026-05-13 |
| M1-4 | `matrix.yaml v1` で英語版バリエーション自動生成成功 | 2026-05-16 |
| M1-5 | 英語版QA基準クリア・Golden Sample確立 | 2026-05-19 |
| M1-6 | Waveshare全26ボードの英語版ビルド成功率80%以上 | 2026-05-26 |
| **M1-7** | **🚀 英語版出荷フロー確立・実出荷可能** | **2026-05-29** |

### STEP 2（日本語版）

| Milestone | 完了条件 | 想定日付 |
|---|---|---|
| M2-1 | 日本語翻訳アセット（ja-JP）完成 | 2026-06-05 |
| M2-2 | 日本語版 Waveshare 1.85C `.bin` 実機動作確認 | 2026-06-08 |
| M2-3 | 日本語UI調整完了（フォント・行間） | 2026-06-10 |
| M2-4 | `matrix.yaml v2` で EN+JA 両対応自動生成成功 | 2026-06-11 |
| M2-5 | 日本語版QA基準クリア・Golden Sample確立 | 2026-06-13 |
| M2-6 | Waveshare全26ボードの日本語版ビルド成功率80%以上 | 2026-06-18 |
| **M2-7** | **🚀 日本語版出荷フロー統合・実出荷可能** | **2026-06-19** |

---

## 25. 関連ファイル

- `CLAUDE.md` — プロジェクト全体指示書
- `xiaozhi-hardware-collection-plan.md` — ハードウェアカタログ収集計画
- `Xiaozhi-Firmware-OTA/` — 既存OTAパッチツール群（本計画で発展統合）
- `Xiaozhi-Firmware-OTA/assets/` — ボード×ブランド別アセット（STEP1で構築、STEP2で拡張）
- `Xiaozhi-Firmware-OTA/build/matrix.yaml` — ビルドマトリクス定義（v1:STEP1英語、v2:STEP2 EN+JA）
- `Xiaozhi-Firmware-OTA/build/build_matrix.py` — 量産ビルドスクリプト
- `Xiaozhi-Firmware-OTA/build/inject_assets.py` — アセット注入
- `Xiaozhi-Firmware-OTA/build/verify_build.py` — バイナリ検証
- `xiaozhi-hardware-catalog/waveshare/` — Waveshare 26ボードのスペック情報
- `shipping-workflow-en.md` — 英語版出荷フロー（STEP1で作成）
- `shipping-workflow-ja.md` — 日本語版出荷フロー（STEP2で作成）
- `docs/asset-spec.md` — 画像・音声仕様書（Phase 0-A で作成）
- `docs/translation-source.md` — 翻訳対象ファイル一覧（Phase 0-A → STEP2で利用）
- `docs/glossary-ja.md` — 日本語用語集（STEP2で作成）

---

## 26. 参考リンク

- 本家: https://github.com/78/xiaozhi-esp32
- Releases: https://github.com/78/xiaozhi-esp32/releases
- Kconfig.projbuild: https://github.com/78/xiaozhi-esp32/blob/main/main/Kconfig.projbuild
- カスタムボード: https://github.com/78/xiaozhi-esp32/blob/main/docs/custom-board.md
- ESP-IDF Windows: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/get-started/windows-setup.html
- Waveshare Xiaozhi Wiki: https://www.waveshare.com/wiki/Xiaozhi_AI_Application_Tutorial
- LVGL Image Converter: https://github.com/lvgl/lv_img_conv
- LVGL docs: https://docs.lvgl.io/
- Noto Sans JP: https://fonts.google.com/noto/specimen/Noto+Sans+JP
- 英語フォーク（iotsystem）: https://github.com/iotsystem/xiaozhi-esp32
- 英語フォーク（x22x22）: https://github.com/x22x22/xiaozhi-esp32
- 英語フォーク（txp666）: https://github.com/txp666/xiaozhi-esp32

---

## 27. 更新履歴

| 日付 | 変更者 | 変更内容 |
|---|---|---|
| 2026-04-18 | xxc | 初版作成（英語/日本語ビルド + OTA URL組込） |
| 2026-04-18 | xxc | 量産対応へ拡張: カスタムロゴ・起動音・ビルドマトリクス・QA・出荷フロー追加 |
| 2026-04-18 | xxc | **2段階構成に再編成**: STEP1（英語版先行、独立出荷可能）→ STEP2（日本語版拡張）の順次進行モデルに変更 |

---

*本計画書は進捗に応じて更新すること。各 Phase 完了時に `[x] 完了` マークと日付を追記する。*
*STEP1 完了後、STEP2 開始前に市場反応と技術的フィードバックを1ヶ月観測することを推奨。*
