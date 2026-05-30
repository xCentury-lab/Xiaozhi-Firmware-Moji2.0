# Movecall Moji 2.0 (ESP32-C5) ボード概要

> **対象**: `movecall-moji2-esp32c5` (Movecall Moji 2.0 — 小智 AI 衍生版)
> **チップ**: ESP32-C5 (RISC-V、Wi-Fi 6)
> **作成日**: 2026-05-29
> **公式 hw**: https://oshwhub.com/movecall/moji2

---

## 1. ハードウェア概要

| 項目 | 値 |
|---|---|
| Target chip | **ESP32-C5** (RISC-V 32bit、デュアル Wi-Fi (2.4G + 5G)、Bluetooth 5.0 LE) |
| Flash | 16 MB |
| SPIRAM | 8 MB QSPI (Quad SPI) |
| Display | (Moji 2.0 LCD) |
| Audio Codec | (Moji 2.0 codec) |
| Speaker | mono |
| 起動 wake | Alexa / Hi,ESP / Custom MultiNet (hikarin / nekochan) |

詳細は [Movecall OSHWHub 公式 hw page](https://oshwhub.com/movecall/moji2) 参照。

---

## 2. ESP32-C5 の特徴

| 項目 | 値 |
|---|---|
| Architecture | RISC-V 32bit single core |
| Clock | 最大 240 MHz |
| Wi-Fi | デュアル (2.4 GHz + 5 GHz、Wi-Fi 6 対応) |
| Bluetooth | BLE 5.0 |
| ESP-IDF サポート開始 | v5.3 (preview) → v5.5 で stable |
| Bootloader offset | **0x2000** (ESP32-P4 と同じ、ESP32-S3/C3 の 0x0 と異なる。`CONFIG_BOOTLOADER_OFFSET_IN_FLASH=0x2000`、2026-05-30 実機ビルド実測確定) |
| TEE / Secure Boot | サポート (本プロジェクトでは無効) |

---

## 3. Partition Layout (16MB)

`partitions/v2/16m.csv` (xiaozhi-esp32 内):

```
# Name,   Type, SubType, Offset,  Size, Flags
nvs,      data, nvs,     0x9000,    0x4000,
otadata,  data, ota,     0xd000,    0x2000,
phy_init, data, phy,     0xf000,    0x1000,
ota_0,    app,  ota_0,   0x20000,   0x3f0000,
ota_1,    app,  ota_1,   ,          0x3f0000,
assets,   data, spiffs,  0x800000,  8M
```

| Partition | Offset | Size | 内容 |
|---|---|---|---|
| nvs | 0x9000 | 16 KB | NVS (永続設定) |
| otadata | 0xd000 | 8 KB | OTA メタ |
| phy_init | 0xf000 | 4 KB | RF キャリブレーション |
| ota_0 (xiaozhi.bin) | 0x20000 | 3.94 MB | アプリ本体 (initial slot) |
| ota_1 | 自動 | 3.94 MB | OTA 更新受け先 |
| **assets** | **0x800000** | **8 MB** | ⭐ **xiaozhi-assets-generator 生成の assets.bin を焼く位置** |

---

## 4. xiaozhi-esp32 board file 解析

### config.json

```json
{
    "target": "esp32c5",
    "builds": [{
        "name": "movecall-moji2-esp32c5",
        "sdkconfig_append": [
            "CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y",
            "CONFIG_PARTITION_TABLE_CUSTOM_FILENAME=\"partitions/v2/16m.csv\"",
            "CONFIG_FREERTOS_USE_TICKLESS_IDLE=y",
            "CONFIG_SPIRAM=y",
            "CONFIG_SPIRAM_MODE_QUAD=y",
            "CONFIG_SPIRAM_SPEED_80M=y",
            "CONFIG_SPI_FLASH_FREQ_LIMIT_C5_240MHZ=y"
        ]
    }]
}
```

### File 構成 (本家 source 内)

```
main/boards/movecall-moji2-esp32c5/
├── config.h                       # I/O ピン定義
├── config.json                    # sdkconfig_append + partition
├── movecall_moji2_esp32s3.cc      # board 実装 (名前は s3 だが実 C5)
├── README.md                      # 英語版ビルド手順
└── README_zh.md                   # 中文版ビルド手順
```

---

## 5. Wake Word (WakeNet9s シリーズ、assets.bin 一元管理)

### 5.1 ESP-C5 の Wake Word 制約

ESP32-C5 (RISC-V、低リソース) は **WakeNet9s (small/lite) シリーズのみ** サポート:

| WakeNet 系統 | 対象チップ | モデル名形式 | C5 対応 |
|---|---|---|---|
| **WakeNet9 (フル)** | ESP32-S3 / P4 (Xtensa) | `wn9_*` (例: wn9_alexa) | ❌ 非対応 |
| **WakeNet9s (small)** | **ESP32-C3 / C5 / C6** | `wn9s_*` (例: wn9s_alexa) | ✅ **公式版** |
| MultiNet | (別系統、command 認識) | mn_* | 対象外 (Moji2 は wake word 主体) |

ESP32-C5 で WakeNet9 (`wn9_*`) を指定するとビルドは通っても **runtime で memory 不足エラー**が出るため、必ず `wn9s_*` を選ぶ。

### 5.2 assets.bin への同梱

Moji2.0 では **wake word モデルを assets.bin に同梱**することで以下を実現:

- sdkconfig での `CONFIG_SR_WN_*` 個別 enable が **不要**
- Web UI (xiaozhi-assets-generator) でモデル選択可能 → firmware rebuild なしで wake word 入替
- 複数の wake word を同時搭載可能 (容量内なら 4-6 個程度)

### 5.3 標準搭載 wake words

| Wake word | model 名 | 用途 |
|---|---|---|
| Alexa | `wn9s_alexa` | 国際標準 |
| Hi, ESP | `wn9s_hiesp` | xiaozhi 標準 |
| ひかりん | `wn9s_hikarin` | xCentury カスタム (日本語) |
| ねこちゃん | `wn9s_nekochan` | xCentury カスタム (日本語) |

> **Safety net**: assets.bin が破損 / 焼き込み失敗時、ファーム単独では wake word なし状態になる (起動はする)。assets.bin の整合性検証は build 後に必須 ([../operations/firmware-build-v2.2.6-esp32c5.md](../operations/firmware-build-v2.2.6-esp32c5.md) Step 7 参照)。

---

## 6. ESP-VoCat (姉妹プロジェクト) との違い

| 項目 | ESP-VoCat | **Moji 2.0** |
|---|---|---|
| Chip | ESP32-S3 (Xtensa) | **ESP32-C5 (RISC-V)** |
| Wi-Fi | 2.4 GHz only | **2.4 G + 5 G (Wi-Fi 6)** |
| SPIRAM | 16 MB OCTAL | 8 MB QUAD |
| Asset 形式 | `expression_assets.bin` (3MB、emote 表情 + wakenet 同梱) | **`assets.bin`** (emoji + MultiNet + フォント、xiaozhi-assets-generator 生成) |
| Display | emote::EmoteDisplay 主体 | LCD 表示主体 |
| Emoji 反映 | C 配列方式 (旧来) | **assets.bin パスベース** (新フロー) |
| ESP-IDF | v5.5.2 | **v5.5+** (v5.5.2 推奨) |

---

## 7. 関連ドキュメント

- [../operations/firmware-build-v2.2.6-esp32c5.md](../operations/firmware-build-v2.2.6-esp32c5.md) — ⭐ ビルド完全手順
- [../operations/audio-assets.md](../operations/audio-assets.md) — 音声アセット所在
- [../operations/wake-word-selection.md](../operations/wake-word-selection.md) — 2 段ウェイクアーキテクチャ
- [../../README.md](../../README.md) — プロジェクトトップ
- **xiaozhi-esp32 board doc**: `~/xiaozhi-work/xiaozhi-esp32/main/boards/movecall-moji2-esp32c5/README.md`

### Movecall 公式一次情報

| カテゴリ | URL | 内容 |
|---|---|---|
| **オープンハードウェア (开源链接 / oshwhub)** | https://oshwhub.com/movecall/moji2 | 回路図・PCB 設計・BOM (open source hardware) |
| **3D モデル / 筐体ファイル (3D文件链接)** | https://makerworld.com.cn/zh/@MoveCall | 筐体・ボタン等の 3D プリント用 STL / 3MF (Bambu Lab MakerWorld 配布) |
