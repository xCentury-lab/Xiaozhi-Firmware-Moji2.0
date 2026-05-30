# Xiaozhi-Firmware-Moji2.0

> **Xiaozhi ESP32 ファームウェアのカスタム量産ビルドパイプライン (Movecall Moji 2.0 商品化)**
> 言語切替・OTA URL 組込・ja-JP 音声マスタ補正・ウェイクワード・**カスタム emoji (xCentury 黒猫 21 感情)** を再現可能な形で量産するためのプロジェクト

---

## 🎯 プロジェクトの目的

本家 [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) のファームウェアを以下の **5 軸** + **emoji** で量産可能にカスタマイズします。

| # | 軸 | 内容 | 実装手段 |
|---|---|---|---|
| 1 | **UI 言語** | ja-JP | コンパイル時 Kconfig + ja-JP 音声マスタ反映 |
| 2 | **OTA サーバ URL** | `classism.net` | ビルド時組込 (バイナリ後加工不要) |
| 3 | **ja-JP 音声マスタ** (発音修正) ⚠️ | 本家 ja-JP 音声には発音誤りがあるため、`assets/sounds/locales/ja-JP/` で自家整備 | **★ ビルド前 必須**: 本家 source の `main/assets/locales/ja-JP/` に **rsync で上書き → xiaozhi.bin に embed** (ビルド後 OTA 部分差替不可、Step 2.5 で sha256 guard 必須) |
| 4 | **ウェイクワード** | **assets.bin 内蔵 WakeNet9s シリーズモデル** (ひかりん / ねこちゃん / Alexa 等、全て `wn9s_*` 形式) | **assets.bin 一元管理** (sdkconfig での個別 enable 不要) |
| 5 | **emoji コレクション** ★ | xCentury 黒猫 21 感情 (cat_master_2k v2) | **assets.bin 一元管理** (xiaozhi-assets-generator Web UI 生成、C 配列方式不要) |

> **2026-05-29 ★ assets.bin 一元化原則 (ESP-C5 / Moji2.0)**:
>
> ESP-C5 / Moji2.0 では **emoji + wake word + フォント の 3 種類はすべて assets.bin に組込まれる**。これにより:
>
> - sdkconfig での `CONFIG_SR_WN_*` 個別 enable は **不要** (ESP-C5 専用の WakeNet9s シリーズが assets.bin 同梱)
> - emoji の C 配列方式 (`tools/emoji_to_lvgl_c.py`) や `lcd_display.cc` patch も **不要**
> - フォントも assets.bin 同梱 (subset 済)
>
> firmware 側は **assets.bin への依存度が高い** → 量産時は assets.bin の SHA256 を必ず manifest.json に記録、出荷後の差替も assets partition (0x800000) の書込のみで完結。
>
> 詳細: [docs/operations/firmware-build-v2.2.6-esp32c5.md](docs/operations/firmware-build-v2.2.6-esp32c5.md) Step 4-(α)、[docs/architecture/moji2-board-overview.md](docs/architecture/moji2-board-overview.md) §5。

---

## 📍 現在の状態 (2026-05-29)

| 項目 | 値 |
|---|---|
| 商品化対象 | **movecall-moji2-esp32c5** 1 SKU (Movecall Moji 2.0 小智 AI 衍生版) |
| Firmware version | v2.2.6 (本家 78/xiaozhi-esp32 v2.2.6 タグ) |
| Target chip | **ESP32-C5** (RISC-V、Wi-Fi 6) |
| 言語 | ja-JP |
| Wake words | **assets.bin 内蔵 WakeNet9s モデル** (Alexa / Hi,ESP / ひかりん / ねこちゃん等、全て `wn9s_*` 形式) |
| OTA URL | `https://classism.net/xiaozhi/ota/` |
| Brand | company (xCentury) |
| Emoji pack | xCentury 黒猫 cat_master_2k v2 (21 感情、透明背景) |
| 進行中の課題 | 初回ビルド未実施 (assets.bin は配置済) |

---

## 🎛 対応ボード

| SKU | チップ | Flash | SPIRAM | 状態 |
|---|---|---|---|---|
| **`movecall-moji2-esp32c5`** ⭐ 商品化対象 | **ESP32-C5** | 16 MB | 8 MB QSPI | assets.bin 配置済、ビルド待機 |

### 連携先

| 種別 | 場所 |
|---|---|
| 本家 firmware | [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) v2.2.6 タグ |
| OTA サーバ | `https://classism.net/xiaozhi/ota/` (AWS EC2) |
| **assets.bin 生成** | [xiaozhi-assets-generator](https://github.com/xCentury-lab/xiaozhi-assets-generator) Web UI |
| ESP-IDF | v5.5+ 必須 (ESP32-C5 サポート) |
| Movecall Moji 2.0 公式 hw (open source / 开源链接) | https://oshwhub.com/movecall/moji2 |
| Movecall Moji 2.0 3D モデルファイル (3D文件链接) | https://makerworld.com.cn/zh/@MoveCall |

### 📚 Movecall 公式リンク集

商品化・修理・カスタム筐体製作の際に参照する一次情報源:

| カテゴリ | URL | 内容 |
|---|---|---|
| **オープンハードウェア (开源链接 / oshwhub)** | https://oshwhub.com/movecall/moji2 | 回路図・PCB 設計・BOM (オープンソースハードウェア) |
| **3D モデル / 筐体ファイル (3D文件链接)** | https://makerworld.com.cn/zh/@MoveCall | 筐体・ボタン等の 3D プリント用 STL / 3MF (Bambu Lab MakerWorld 配布) |

> 上記は **Movecall 本家** が公開している一次情報。商品化時の OEM 筐体設計や、修理用予備パーツの 3D プリントに利用可能。

---

## 📁 リポジトリ構造

```
Xiaozhi-Firmware-Moji2.0/
├── README.md                                ★ 本ファイル
├── LICENSE                                  MIT
├── requirements.txt                         Python 依存
├── push.sh / push.ps1                       GitHub push スクリプト
│
├── scripts/                                 環境構築 (Ubuntu / Windows)
│
├── docs/                                    ★ 全ドキュメント
│   ├── README.md                            ← マスタインデックス
│   ├── PROJECT_OVERVIEW.md                  ← 商品化概要 (本 doc から派生)
│   ├── build-plan.md                        ← メイン計画書
│   ├── customization-spec.md                ← 5 軸 + emoji 仕様
│   ├── asset-spec.md                        ← 音声 / emoji 仕様
│   ├── operations/
│   │   ├── firmware-build-v2.2.6-esp32c5.md ⭐ ★ Moji2.0 ビルド完全手順
│   │   ├── audio-assets.md                  音声アセット所在マップ
│   │   ├── flash-guide.md                   量産ライン書込手順
│   │   ├── ota-url-inplace-rewrite.md       OTA URL 書換手順
│   │   ├── volume-configuration.md          音量設定
│   │   ├── wake-word-selection.md           ウェイクワード選定
│   │   └── wsl-usb-device-setup.md          WSL USB セットアップ
│   ├── setup/                               OS 別環境構築 (linux/windows)
│   ├── plans/                               Phase 別実行プラン
│   ├── server/                              サーバ仕様
│   └── Review/                              Phase 0 事前調査
│
├── build/                                   量産ビルドパイプライン (matrix.yaml + scripts)
├── tools/                                   OTA URL 後加工パッチツール
├── assets/                                  ボード × ブランド × 言語別アセット
│   └── sounds/locales/ja-JP/                ← 日本語音声マスタ (継承)
├── firmware/                                ビルド成果物 (.gitignored)
│   └── v2.2.6_movecall-moji2-esp32c5/       ⭐ 商品化ターゲット (assets.bin 配置先)
├── patches/                                 本家へ当てるパッチ
└── .claude/skills/                          ビルド・OTA 書換 skill
    ├── xiaozhi-build/                       (※ ESP32-C5 対応に拡張予定)
    └── xiaozhi-ota-rewrite/                 OTA URL in-place 書換
```

---

## 🚀 標準ビルドフロー (Moji2.0)

```bash
# 1. 本家 source 準備 (worktree pattern 推奨)
cd ~/xiaozhi-work/xiaozhi-esp32
git worktree add ../xiaozhi-esp32-moji2-rebuild v2.2.6
cd ../xiaozhi-esp32-moji2-rebuild
git submodule update --init --recursive

# 2. ESP-IDF v5.5+ 環境有効化
source $HOME/esp/esp-idf-5.5.2/export.sh

# 3. ターゲット切替 (★ S3 → C5 にチップ変更、wake word 系統も WakeNet9 → WakeNet9s に切替)
idf.py fullclean
idf.py set-target esp32c5

# 3.5. ★ ja-JP 音声マスタ置換 (★ ビルド前 必須 — skip すると発音誤りのまま量産)
#      本家 ja-JP 音声 (発音誤りあり) を xCentury 整備済 master で上書き。
#      音声マスタは xiaozhi.bin に embed されるため、ビルド後 OTA で部分差替できない。
PROJ=/home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-Moji2.0
SRC_LOCALE=~/xiaozhi-work/xiaozhi-esp32/main/assets/locales/ja-JP
[ -d "${SRC_LOCALE}.orig" ] || cp -r "$SRC_LOCALE" "${SRC_LOCALE}.orig"   # 本家 backup (1 回のみ)
rsync -av --include='*.ogg' --include='language.json' --exclude='*' \
  "$PROJ/assets/sounds/locales/ja-JP/" "$SRC_LOCALE/"
diff <(cd "$PROJ/assets/sounds/locales/ja-JP" && sha256sum *.ogg language.json | sort) \
     <(cd "$SRC_LOCALE"                       && sha256sum *.ogg language.json | sort) \
  || { echo "🛑 ja-JP master 置換漏れ"; exit 1; }

# 4. Board 選択 (menuconfig)
idf.py menuconfig
#   → Xiaozhi Assistant → Board Type → "Movecall Moji2.0 小智AI衍生版"

# 5. ビルド (10-15 分)
idf.py build

# 6. merge_bin + User の assets.bin を 0x800000 に組込み (★ Moji2.0 固有フロー)
PROJ=/home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-Moji2.0
cd build
python -m esptool --chip esp32c5 merge_bin \
  --flash_mode dio --flash_freq 80m --flash_size 16MB \
  -o merged-binary.bin \
  0x2000 bootloader/bootloader.bin \
  0x8000 partition_table/partition-table.bin \
  0xd000 ota_data_initial.bin \
  0x20000 xiaozhi.bin \
  0x800000 "$PROJ/firmware/v2.2.6_movecall-moji2-esp32c5/assets.bin"

# 7. 成果物配置
cp merged-binary.bin "$PROJ/firmware/v2.2.6_movecall-moji2-esp32c5/"
```

詳細: [docs/operations/firmware-build-v2.2.6-esp32c5.md](docs/operations/firmware-build-v2.2.6-esp32c5.md)

---

## 🔄 ESP-VoCat (姉妹プロジェクト) との違い

| 項目 | [Xiaozhi-Firmware-VoCat](../Xiaozhi-Firmware-VoCat/) | **Xiaozhi-Firmware-Moji2.0** |
|---|---|---|
| ボード | ESP-VoCat (旧 EchoEar) | **movecall-moji2-esp32c5** |
| チップ | ESP32-S3 | **ESP32-C5** (RISC-V) |
| bootloader offset | 0x0 (S3) | **0x2000** (C5、★ S3 と異なる、2026-05-30 実機ビルド確定) |
| ESP-IDF | v5.5.2 | v5.5.2+ (v5.5+ 必須) |
| Asset 形式 | `expression_assets.bin` (3MB、emote 表情 + wakenet) | **assets.bin** (xiaozhi-assets-generator 生成、emoji + **WakeNet9s 群** + フォント) |
| Emoji 組込 | emote 経由 (Display 主体) | **assets.bin パスベース** (★ 新フロー) |
| Wake word 系統 | **WakeNet9** (フル、`wn9_*`、sdkconfig で個別 enable) | **WakeNet9s** (small、`wn9s_*`、assets.bin 同梱で一元管理) |
| 起動音マスタ | ja-JP 自家整備 | ja-JP 自家整備 (継承) |

---

## ⚖️ ライセンス・メンテナ

- **License**: MIT (本家 78/xiaozhi-esp32 も MIT)
- **メンテナ**: xxc (xxc@ctoch.jp) / xCentury PAI
- **配布時**: 本家 LICENSE 同梱と改変点 README 明記必須
- **公開範囲**: Private (OEM ブランド情報・秘匿サーバ設定を含むため)

---

*最終更新: 2026-05-29 | 詳細仕様は [docs/build-plan.md](docs/build-plan.md) と [docs/operations/firmware-build-v2.2.6-esp32c5.md](docs/operations/firmware-build-v2.2.6-esp32c5.md) 参照。*
