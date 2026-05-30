# Xiaozhi ファームウェア v2.2.6 + 6 軸 ビルド手順書 (ESP32-C5 / movecall-moji2)

> **対象ボード**: `movecall-moji2-esp32c5` (Movecall Moji2.0 — 小智AI衍生版)
> **チップ**: ESP32-C5 (RISC-V、Wi-Fi 6、SPIRAM 8MB QSPI、Flash 16MB)
> **作成日**: 2026-05-29
> **関連 doc**: [firmware-build-v2.2.6.md](firmware-build-v2.2.6.md) (ESP32-P4-4B 版、命令系統互換)

---

## 0. 前提

### 0-1. 環境

| 項目 | 要件 |
|---|---|
| ESP-IDF | **v5.5+ 必須** (ESP32-C5 サポートは v5.3 から、v5.5 で安定) |
| xiaozhi-esp32 | **v2.2.6** タグ |
| Python | 3.10+ |
| esptool | **≥ 4.9** (`pip install -U esptool`) |
| OS | WSL2 (Ubuntu) / Linux / macOS |

### 0-2. ESP-IDF v5.5.2 切替手順 (既に v5.5.4 等が install 済の場合)

```bash
cd $HOME/esp
git clone -b v5.5.2 --recursive https://github.com/espressif/esp-idf.git esp-idf-5.5.2
cd esp-idf-5.5.2

# 入れ子サブモジュール対策 (openthread/mbedtls 等で競合する場合)
git submodule update --init --recursive --force

# Toolchain 切替 (差分のみ DL、~5-10 分)
./install.sh esp32c5      # ★ esp32c5 を明示
source ./export.sh
```

### 0-3. xiaozhi-esp32 v2.2.6 切替

```bash
cd ~/xiaozhi-work/xiaozhi-esp32
git fetch origin && git checkout v2.2.6
git submodule update --init --recursive
```

### 0-4. movecall-moji2-esp32c5 board の概要

`main/boards/movecall-moji2-esp32c5/` 配下に board 固有定義 (Movecall 提供):

| ファイル | 役割 |
|---|---|
| `config.h` | I/O ピン定義 |
| `config.json` | sdkconfig_append + partition table 指定 |
| `movecall_moji2_esp32s3.cc` | LCD/IMU/Audio init (名前は s3 だが実 chip は c5) |
| `README.md` / `README_zh.md` | OSHWHub ハードウェア情報 + ビルド手順 |

config.json 抜粋:
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

### 0-5. Partition layout (partitions/v2/16m.csv)

```
# Name,   Type, SubType, Offset,  Size, Flags
nvs,      data, nvs,     0x9000,    0x4000,
otadata,  data, ota,     0xd000,    0x2000,
phy_init, data, phy,     0xf000,    0x1000,
ota_0,    app,  ota_0,   0x20000,   0x3f0000,
ota_1,    app,  ota_1,   ,          0x3f0000,
assets,   data, spiffs,  0x800000,  8M
```

→ **assets partition は `0x800000` 始まり、8MB**。`xiaozhi-assets-generator` が生成した `assets.bin` はここに焼く。

---

## 1. ビルド手順 (ESP32-C5 / movecall-moji2)

### Step 1: 環境変数有効化

```bash
source $HOME/esp/esp-idf-5.5.2/export.sh
cd ~/xiaozhi-work/xiaozhi-esp32
idf.py --version    # → ESP-IDF v5.5.2 確認
```

### Step 2: fullclean + set-target esp32c5 ★ **ESP32-P4 と異なる**

```bash
idf.py fullclean
idf.py set-target esp32c5
# managed_components が再 DL される (~3-5 分)
```

> **ESP32-P4 doc との差**: `set-target esp32p4` ではなく **`set-target esp32c5`**。

---

### ⚠️ Step 2.5: ja-JP 音声マスタ置換 (★ ビルド前 **必須**)

> **🛑 SKIP 厳禁**: このステップを飛ばすと、本家 ja-JP 音声 (発音誤りあり) が量産品に焼かれてしまう。
> **音声マスタは ROM の `xiaozhi.bin` に embed されるため、ビルド後は OTA で完全差替不可** (ota_0 全体の書換が必要)。
> よって **ビルド前** に必ず置換する。assets.bin (emoji + wake word) とは **別の partition** に住むため、assets.bin 差替では復旧不可。

#### 2.5-A. xCentury 整備済 master で本家 ja-JP locale を上書き

```bash
PROJ=/home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-Moji2.0
SRC_LOCALE=~/xiaozhi-work/xiaozhi-esp32/main/assets/locales/ja-JP

# 1) 本家 master を一度だけ backup (worktree 初回のみ)
[ -d "${SRC_LOCALE}.orig" ] || cp -r "$SRC_LOCALE" "${SRC_LOCALE}.orig"

# 2) xCentury 整備済 master で上書き (.ogg + language.json のみ、TTS 素材 *.wav は除外)
rsync -av --include='*.ogg' --include='language.json' --exclude='*' \
  "$PROJ/assets/sounds/locales/ja-JP/" "$SRC_LOCALE/"
```

#### 2.5-B. 置換検証 (4 段チェック)

```bash
# ① ファイル数が一致 (本家 16-17 + xCentury 整備済が同等数)
ls "$SRC_LOCALE" | grep -E '\.(ogg|json)$' | wc -l

# ② language.json が xCentury 版に差替済
head -1 "$SRC_LOCALE/language.json"

# ③ welcome.ogg の sha256 が project 側と一致
sha256sum "$SRC_LOCALE/welcome.ogg" "$PROJ/assets/sounds/locales/ja-JP/welcome.ogg"

# ④ 発音修正対象ファイル (activation/welcome/wificonfig) のサイズが本家より大きい/異なる
ls -la "$SRC_LOCALE/welcome.ogg" "${SRC_LOCALE}.orig/welcome.ogg"
```

| ✅ 期待 | ❌ 失敗時 |
|---|---|
| sha256 が一致、ファイル数同等 | 置換失敗 → `rsync` を再実行 |
| `.orig` backup が残る | 復旧用、削除禁止 |

#### 2.5-C. 置換漏れ対策 (自動 fail-safe)

ビルド中の `idf.py build` 前に **必ず** 次の guard を踏むこと:

```bash
# Guard: project master と src locale の sha256 が一致するか確認、ズレていれば fail
diff <(cd "$PROJ/assets/sounds/locales/ja-JP" && sha256sum *.ogg language.json | sort) \
     <(cd "$SRC_LOCALE"                       && sha256sum *.ogg language.json | sort) \
  || { echo "🛑 ja-JP master 置換漏れ — Step 2.5-A を再実行してください"; exit 1; }
```

> **量産時の運用ルール**:
> - **worktree 作成 → Step 2.5 → ビルド** の順を絶対に崩さない
> - worktree 削除 (`git worktree remove`) 時、本家の `.orig` backup は消えるので毎 worktree で再作成
> - `assets/sounds/locales/ja-JP/` を更新したら、過去ビルドの xiaozhi.bin は全廃棄 (assets.bin 単独差替では発音修正は反映されない)

---

### Step 3: 6 軸 sdkconfig 適用

#### 3-A. ボード固有 sdkconfig_append (★ 必須)

```bash
# Movecall Moji2.0 board を選択 (menuconfig 経由)
idf.py menuconfig
# Navigate to:
#   Xiaozhi Assistant → Board Type → "Movecall Moji2.0 小智AI衍生版"
# Save (S, Enter) → Quit (Q)
```

または sdkconfig を直接編集:
```ini
CONFIG_BOARD_TYPE_MOVECALL_MOJI2_ESP32C5=y
CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions/v2/16m.csv"
CONFIG_FREERTOS_USE_TICKLESS_IDLE=y
CONFIG_SPIRAM=y
CONFIG_SPIRAM_MODE_QUAD=y
CONFIG_SPIRAM_SPEED_80M=y
CONFIG_SPI_FLASH_FREQ_LIMIT_C5_240MHZ=y
```

#### 3-B. 残り軸 (lang / OTA のみ — wake word / emoji は assets.bin 一元管理)

```bash
cat >> sdkconfig << 'EOF'
CONFIG_LANGUAGE_JA_JP=y
CONFIG_OTA_URL="https://classism.net/xiaozhi/ota/"
EOF
```

> **★ ESP-C5 / Moji2.0 重要原則**: 以下は **すべて assets.bin に同梱**されるため、sdkconfig での個別 enable は **不要**:
>
> - **Wake word** (旧 `CONFIG_SR_WN_WN9_*`): ESP-C5 は **WakeNet9s シリーズのみ** サポート (`wn9s_alexa`, `wn9s_hiesp`, `wn9s_hikarin`, `wn9s_nekochan` 等)。フル `wn9_*` 系は不対応。
> - **Emoji コレクション** (旧 C 配列方式): xCentury 黒猫 21 感情を含むすべての emoji は assets.bin に圧縮済。`tools/emoji_to_lvgl_c.py` でのソース改変や `lcd_display.cc` patch は **不要**。
> - **フォント** (subset 等): assets.bin に同梱。
>
> sdkconfig には **言語 + OTA URL の 2 項目のみ** 追加すれば足り、wake word / emoji / フォントは **すべて Web UI ([xiaozhi-assets-generator](https://github.com/xCentury-lab/xiaozhi-assets-generator)) で構成 → assets.bin 1 ファイルで完結**する。

> **注**: WakeNet モデル本体は `assets` パーティション (`generated_assets.bin` / `assets.bin`) に住むため、`xiaozhi.bin` への影響はほぼゼロ (runtime stub ~20 KB のみ)。

### Step 4: Emoji コレクション組込 (軸 #6)

ESP32-C5 では **2 つの方式** が選択可能:

#### Step 4-(α): assets.bin パスベース (★ 推奨、最新フロー)

`xiaozhi-assets-generator` Web UI で **assets.bin を事前生成済**の場合は、Step 5 のビルドは asset 生成を行わず、Step 6 の `merge_bin` で **User の assets.bin を `0x800000` に直接配置**する。

```bash
# 生成済 assets.bin の場所
ls /home/user/project/OpenAI-Realtime-LAB/Xiaozhi-Firmware-update/firmware/v2.2.6_Moji2.0/assets.bin
```

→ assets には emoji + WakeNet (Custom MultiNet) + (オプション) フォントが組込済。**Step 4-(β) は不要**。

#### Step 4-(β): C 配列直接生成方式 (旧来、assets.bin を使わない場合)

`firmware-build-v2.2.6.md` (P4 版) の Step 4-(a)/(b) と同じ手順:
- `tools/emoji_to_lvgl_c.py` で xiaozhi-fonts に C 配列を上書き
- `lcd_display.cc` に Twemoji64 bind patch を適用

ESP32-C5 でも同じパッチが適用可能 (lcd_display は共通)。

> **推奨**: Step 4-(α) (assets.bin 方式) を使うと **emoji 更新サイクルが Web UI で完結** し、firmware rebuild 不要 ([13-rembg-tuning.md](../../../xiaozhi-assets-generator/docs/13-rembg-tuning.md) 等参照)。

### Step 5: ビルド (10-15 分)

```bash
nohup idf.py build > /tmp/idf-build.log 2>&1 &
# 進捗確認:
tail -f /tmp/idf-build.log | grep -E "Project build complete|FAILED|error:"
```

完了マーカー: `Project build complete. To flash, run:`

### Step 6: merge_bin esp32c5 ★ **ESP32-P4 と異なる**

```bash
PROJ=/home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-Moji2.0
cd build
python -m esptool --chip esp32c5 merge_bin \
  --flash_mode dio --flash_freq 80m --flash_size 16MB \
  -o "$PROJ/firmware/v2.2.6_movecall-moji2-esp32c5/merged-binary.bin" \
  0x2000 bootloader/bootloader.bin \
  0x8000 partition_table/partition-table.bin \
  0xd000 ota_data_initial.bin \
  0x20000 xiaozhi.bin \
  0x800000 "$PROJ/firmware/v2.2.6_movecall-moji2-esp32c5/assets.bin"
```

> **★ ESP32-C5 重要 — bootloader offset は `0x2000` (★ S3/C3 の `0x0` と異なる)**:
> - sdkconfig 確認: `CONFIG_BOOTLOADER_OFFSET_IN_FLASH=0x2000` (2026-05-30 実機ビルドで実測確定)
> - ESP-IDF 自動生成の `build/flash_args` を必ず信頼すること (chip 毎に正しい offset が書かれる)
> - 旧 doc の `0x0` 表記は誤り (ESP32-S3 系の値と混同していた)
>
> **ESP32-P4 doc との差**:
> - `--chip esp32p4` → **`--chip esp32c5`**
> - bootloader offset は **同じ `0x2000`** (P4 も C5 も同じ。S3/C3 のみ 0x0)
> - assets bin の source は **User 生成済 assets.bin を直接指定** (`generated_assets.bin` ではなく、xiaozhi-assets-generator Web UI 出力を使う)

### Step 7: Binary header verify (起動可能性確認)

ESP-IDF が生成する build/bootloader/bootloader.bin の magic を確認:

```bash
python3 << 'EOF'
import struct
def hdr(p, off, label):
    with open(p, "rb") as f: f.seek(off); d = f.read(16)
    if len(d) >= 16:
        magic = d[0]; seg = d[1]
        entry = struct.unpack("<I", d[4:8])[0]
        print(f"[{label}] magic=0x{magic:02x} entry=0x{entry:08x} seg={seg}")

hdr("merged-binary.bin", 0x2000, "boot")
hdr("merged-binary.bin", 0x20000, "app")
EOF
```

期待値:
- bootloader magic = `0xe9` (ESP-IDF image format)
- app magic = `0xe9` (同上)
- entry point = `0x4081_xxxx` 系 (ESP32-C5 LP memory)

### Step 8: Releases/ 配置

```bash
DATE=$(date +%Y%m%d)
DIR="v2.2.6_movecall-moji2-esp32c5_V1.0_ja-JP_alexa-hiesp_company_${DATE}_idf552"
mkdir -p "../../Xiaozhi-Firmware-update/Releases/$DIR"
cp -p bootloader/bootloader.bin partition_table/partition-table.bin \
      ota_data_initial.bin xiaozhi.bin \
      merged-binary.bin flash_args \
      "../../Xiaozhi-Firmware-update/Releases/$DIR/"
# 採用した assets.bin もコピー (再現性確保)
cp -p /home/user/project/OpenAI-Realtime-LAB/Xiaozhi-Firmware-update/firmware/v2.2.6_Moji2.0/assets.bin \
      "../../Xiaozhi-Firmware-update/Releases/$DIR/assets.bin"
cp -p merged-binary.bin "../../Xiaozhi-Firmware-update/Releases/$DIR/xiaozhi_v2.2.6_movecall-moji2-esp32c5_${DATE}_idf552.bin"
```

### Step 9: manifest.json 生成

`Releases/<dir>/manifest.json` に SHA256 / 適用 6 軸 / IDF version / assets.bin の出処を記録:

```json
{
    "firmware_name": "xiaozhi_v2.2.6_movecall-moji2-esp32c5_<DATE>_idf552",
    "board_sku": "movecall-moji2-esp32c5",
    "target_chip": "esp32c5",
    "xiaozhi_version": "v2.2.6",
    "idf_version": "v5.5.2",
    "flash_size_mb": 16,
    "language": "Japanese (ja-JP)",
    "wake_words": ["Alexa", "Hi,ESP"],
    "ota_url": "https://classism.net/xiaozhi/ota/",
    "assets_bin_source": "xiaozhi-assets-generator Web UI (cat_master_2k v2 emoji + MultiNet hikarin/nekochan)",
    "binary_sha256": "sha256:<calc>",
    "flash_layout": {
        "0x2000":   "bootloader.bin",
        "0x8000":   "partition-table.bin",
        "0xd000":   "ota_data_initial.bin",
        "0x20000":  "xiaozhi.bin",
        "0x800000": "assets.bin"
    },
    "build_date": "<YYYYMMDD>"
}
```

---

## 2. 書込手順 (Flash Download Tool, Windows)

### 設定

```
ChipType   : ESP32-C5         ← ★ C5 を選択
WorkMode   : Develop
LoadMode   : UART

ファイル選択: xiaozhi_v2.2.6_movecall-moji2-esp32c5_<DATE>_idf552.bin
@ Offset    : 0x0   ← merged-binary は必ず 0x0

SPIFlashConfig:
  SPI SPEED  : 80MHz   (★ ビルド設定一致)
  SPI MODE   : DIO     (★ ビルド設定一致)
  Flash Size : 16MB
  ☑ DoNotChgBin       (★ 必須、SHA digest 保護)
  ☐ LockSettings

COM   : COM5 (実機接続ポート)
BAUD  : 921600 (高速書込、~2 分。115200 だと ~15 分)
```

### Linux/WSL からの書込 (代替)

```bash
# Download mode 投入 (BOOT 押下 → RST 短押し → BOOT 離す)
python -m esptool --chip esp32c5 -p /dev/ttyACM0 -b 921600 \
  --before no_reset --after hard_reset \
  write_flash 0x0 merged-binary.bin
```

→ WSL の場合は usbipd-win 経由でデバイスを attach (詳細は WSL USB device setup doc 参照)。

### 期待動作

```
IDLE 等待 → START → 下载中... 100% → FINISH 完成
```

書込後、**デバイス再起動** → 起動画面表示 → ja-JP UI + WiFi 設定 + xCentury 猫 emoji 表示 + custom WakeNet 検出。

---

## 3. トラブルシュート

### 3-1. `Error: This chip is esp32c5 not esp32p4` 系エラー
- `idf.py set-target esp32c5` を忘れている。Step 2 を再実行。

### 3-2. `merge_bin` で `--chip esp32c5` を esptool が認識しない
- esptool が古い。`pip install -U esptool` で 4.9+ に更新。

### 3-3. Bootloader/app magic が `0xe9` でない
- 別チップ用にビルドされた bin が混在している。`idf.py fullclean` から再ビルド。

### 3-4. assets.bin のサイズが大きすぎる (>8MB)
- partition の 8MB 超過。`xiaozhi-assets-generator` で容量削減 (emoji 解像度低減、フォント subset 化)。

### 3-5. 起動後 WakeNet が反応しない
- assets.bin に MultiNet モデルが入っているか確認 (`hexdump -C assets.bin | grep -i alexa` 等)
- sdkconfig の `CONFIG_SR_WN_*` 設定確認

### 3-6. Emoji が二重表示・歪み
- `lcd_display.cc` の Twemoji64 bind patch が **不要** (assets.bin 経由なら skip)。Step 4-(β) を適用してたなら revert。

---

## 4. ESP32-P4 / ESP32-C5 差分まとめ

| 項目 | ESP32-P4 (4B) | **ESP32-C5 (movecall-moji2)** |
|---|---|---|
| `--chip` parameter | `esp32p4` | **`esp32c5`** |
| bootloader offset | `0x2000` | **`0x2000`** ★ (P4 と同じ。2026-05-30 実機ビルドで実測確定、`CONFIG_BOOTLOADER_OFFSET_IN_FLASH=0x2000`) |
| ESP-IDF | v5.5.2 | v5.5.2 (v5.5+ 必須) |
| Flash size | 16 MB | 16 MB (同じ) |
| SPIRAM | 16 MB OCTAL | 8 MB QUAD |
| Partition table | partitions/v2/16m.csv | partitions/v2/16m.csv (同じ) |
| assets offset | 0x800000 | 0x800000 (同じ) |
| 既存 Releases 実績 | あり | **なし** (本 doc が新規ベース) |
| Emoji 組込方式 | C 配列方式 (P4 doc) | **assets.bin 方式 (推奨)** |
| 期待 IDLE 電流 | ~70 mA | ~20 mA (C5 低消費) |

---

## 5. 関連ドキュメント

- [firmware-build-v2.2.6.md](firmware-build-v2.2.6.md) — ESP32-P4-4B 版 (本 doc のベース)
- [flash-guide.md](flash-guide.md) — 量産ライン書込手順
- [binary-size-constraints.md](binary-size-constraints.md) — partition size 制約
- [wake-word-selection.md](wake-word-selection.md) — 2 段ウェイクアーキテクチャ
- [../customization-spec-v2.2.6.md](../customization-spec-v2.2.6.md) — 6 軸仕様
- [../architecture/xiaozhi-esp32-overview.md](../architecture/xiaozhi-esp32-overview.md) — システム全体像
- **Movecall Moji2.0 公式 hw**: https://oshwhub.com/movecall/moji2
- **xiaozhi-esp32 board README**: `~/xiaozhi-work/xiaozhi-esp32/main/boards/movecall-moji2-esp32c5/README.md`

## 6. assets.bin の生成元 (参考)

User が配置済の `assets.bin` は別プロジェクト `xiaozhi-assets-generator` で生成された:

- **生成ツール**: [`xiaozhi-assets-generator` Web UI](http://localhost:3000/tools/assets-generator/)
- **生成元 emoji**: `emojis-custom/master/xcentury_cat/cat_master_2k/` (2048×2048 RGBA, 21 emotion)
- **Web 配信版**: `web/public/static/emojis/xcentury_cat_white/` (256×256 RGBA, 21 emotion)
- **assets.bin 構造**: Custom MultiNet (hikarin / nekochan) + 21 emotion emoji + Font subset

詳細: `xiaozhi-assets-generator/docs/11-emoji-pack-generation.md` ほか。

---

## 改訂履歴

| 日付 | バージョン | 内容 | 作成者 |
|---|---|---|---|
| 2026-05-29 | 1.0 | ESP32-C5 (movecall-moji2) 専用ビルド手順初版。ESP32-P4 doc から派生、assets.bin パスベースの新フロー組込 | PAI / xxc@ctoch.jp |
