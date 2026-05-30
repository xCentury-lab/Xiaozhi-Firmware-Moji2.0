# xCentury 黒猫 Emoji 表示されない問題 — 調査メモ (2026-05-30)

> **対象**: Xiaozhi-Firmware-Moji2.0 (ESP32-C5 / movecall-moji2-esp32c5)
> **症状**: User の xCentury 黒猫 21 感情 emoji が実機で表示されない / 本家デフォルト emoji のままに見える
> **ステータス**: 🟡 **真因未確定** (serial log 取得で確定可能)
> **作成日**: 2026-05-30
> **関連**: Engineer 並列 audit (本 doc の根拠)、`docs/hardware/moji2-schematic-power-tree.md`、`docs/operations/wsl-usb-device-setup.md`

---

## 0. TL;DR

| 質問 | 答え |
|---|---|
| assets.bin は正しく焼かれているか? | ✅ **正しい** (`merged-binary.bin@0x800000` = User assets.bin md5 一致確認済) |
| index.json schema は正しいか? | ✅ **正しい** (21 emoji の semantic 名 → hash file 名 mapping 完備) |
| ファーム側の読込経路は正しいか? | ✅ **正しい** (`assets.cc:214 LvglStrategy::Apply` + `lcd_display.cc:1085 SetEmotion`) |
| じゃあなぜ表示されない? | 🔴 **256×256 PNG の decode で heap 不足** が最有力仮説 (decode 後 1 枚 256 KB、毎回 decode の LV_CACHE_DEF_SIZE=0) |
| 確証する方法は? | **`idf.py monitor` で `Failed to get image info` / `Failed to decode image` 等の Assets/LVGL タグエラー**の有無を確認 (5 分以内) |
| 最有力の修正は? | **A2: xiaozhi-assets-generator で PNG を 256×256 → 64×64 にリサイズして assets.bin 再生成** (decode heap 256KB → 16KB) |

---

## 1. 症状

実機 (Moji 2.0 ESP32-C5) を v2.2.6 + User の assets.bin で起動した状態:
- 起動して LCD は表示される
- ja-JP UI / 音量バー (70% 固定の別問題は対処済) / WiFi 設定は正常
- **emoji 表示エリアに xCentury 黒猫が出ない、本家デフォルトの絵柄に見える** (or 何も表示されない可能性も)

User の期待: assets.bin に同梱した 21 個の xCentury 黒猫 (cat_master_2k v2、256×256 RGBA、各 23-37 KB の PNG) が emotion に応じて表示される。

---

## 2. 既に検証済の事実 (✅ ホワイトリスト)

並列 Engineer audit + 回路図検証で **以下は問題なし**と確定。

### 2.1 ハードウェア & Partition 焼込

- `merged-binary.bin` の `0x800000` offset から先頭 16 byte = User assets.bin 先頭 16 byte と完全一致 (`xxd -s 0x800000` で確認済)
- assets.bin md5 = `544bd69278d9f65cbfc804836347b539` (User 生成 master = 量産 binary)
- partition table の `assets` エントリ = type=spiffs, offset=0x800000, size=8MB (`partitions/v2/16m.csv`)
- 詳細: [../../firmware/v2.2.6_movecall-moji2-esp32c5/manifest.json](../../firmware/v2.2.6_movecall-moji2-esp32c5/manifest.json) の `flash_layout`

### 2.2 assets.bin の中身

- 24 エントリ (entry count = 0x18 = 24)
- 内容:
  - `font_puhui_deepseek_20_4.bin` (フォント)
  - `srmodels.bin` (WakeNet9s 軍)
  - `index.json` (semantic → file mapping)
  - `emoji_*.png` × 21 (hash 名、各 23-37 KB、256×256 RGBA、entry table で w=256 h=256)

### 2.3 index.json schema (User assets.bin 内)

ファーム `assets.cc:214 LvglStrategy::Apply()` が要求するスキーマを完全充足:

```json
{
  "version": 1,
  "text_font": "font_puhui_deepseek_20_4.bin",
  "srmodels": "srmodels.bin",
  "emoji_collection": [
    {"name": "neutral",     "file": "emoji_f8d49c97.png"},
    {"name": "happy",       "file": "emoji_0ed46eca.png"},
    {"name": "laughing",    "file": "emoji_18d117b9.png"},
    /* ... 21 entries total ... */
  ],
  "skin": { "light": {...}, "dark": {...} }
}
```

semantic 名 (`neutral` / `happy` / `sad` / `angry` / `crying` / `loving` / `embarrassed` / `surprised` / `shocked` / `thinking` / `winking` / `cool` / `relaxed` / `delicious` / `kissy` / `confident` / `sleepy` / `silly` / `confused` / `laughing` / `funny`) は **ファームが期待する 21 種類と完全一致**。

### 2.4 ファーム側の emoji 読込経路

```
起動 (Application::Init)
  └─ application.cc:328 CheckAssetsVersion()
       └─ application.cc:340 内部処理
            └─ application.cc:393 assets.Apply()
                 └─ assets.cc:214 LvglStrategy::Apply()
                      ├─ assets.cc:230 version > 1 を reject (User=1 で通過 ✓)
                      ├─ assets.cc:262-264 emoji_collection JSON parse
                      └─ EmojiCollection に 21 個登録 + LvglTheme::set_emoji_collection()

User の emotion 指定 (Application::SetEmotion)
  └─ lcd_display.cc:1074 LcdDisplay::SetEmotion("neutral")
       └─ lcd_display.cc:1085 emoji_collection->GetEmojiImage(emotion)
            └─ emoji_collection.cc 内 hash 名 → LvglRawImage (PNG decode 結果) 解決
                 └─ lv_image_set_src(emoji_image_, image->dsc())
```

### 2.5 Moji2.0 board は LCD 360×360 + LvglDisplay

- `boards/movecall-moji2-esp32c5/movecall_moji2_esp32s3.cc` → `SpiLcdDisplay` (ST77916 360×360 RGB565)
- `HAVE_LVGL` 定義済 → `Assets::LvglStrategy` 経路を強制 (`EmoteStrategy` ではない)

---

## 3. 失敗仮説 (🔴 最有力 → 🟡 副次)

### 🔴 仮説 A: 256×256 PNG decode で heap 不足 (最有力)

**根拠**:
1. **User PNG = 256×256 RGBA** → decode 後 raw = 256×256×4 = **262,144 byte = 256 KB / 枚**
2. **build default PNG = 32×32** (xiaozhi-fonts component の Twemoji32) → decode 後 raw = 32×32×4 = **4,096 byte = 4 KB / 枚** (64 倍の差)
3. **`CONFIG_LV_CACHE_DEF_SIZE=0`** で LVGL の image cache は無効 → emoji 切替の度に毎回 decode
4. **lodepng の中間 buffer** (decode 用) は heap_caps_malloc で確保、PSRAM 余裕あるはずだが断片化や同時確保失敗の可能性
5. `setup_ui_called_` race / `emoji_image_=nullptr` ガードを通過しても、**`GetEmojiImage()` 内で decode 失敗 → nullptr 返却** → font_awesome glyph (テキスト記号) にフォールバック → "ぼやけたフォントっぽい何か" として見える

**期待されるエラーログ** (`idf.py monitor` で):
```
E (xxx) Assets: Failed to get image info for emoji_f8d49c97.png
E (xxx) lvgl_image: lodepng decode failed (size=...)
E (xxx) Assets: Emoji 'neutral' image file emoji_f8d49c97.png is not valid
```

### 🟡 仮説 B: assets.bin の各 entry data の magic header 不在

`assets.cc:204` 系のエントリ data チェックで **先頭 2 byte の magic = `'ZZ'` (0x5A 0x5A)** を要求する箇所がある可能性。
- xiaozhi-assets-generator の bin 生成器が 21 個の emoji PNG 各 entry data に `ZZ` magic を前置しているか要確認
- index.json 抽出時には magic 確認済 (Engineer audit) なので、PNG entry が確認漏れ

**期待されるエラーログ**:
```
E (xxx) Assets: The asset emoji_f8d49c97.png is not valid with magic XX XX
```

### 🟡 仮説 C: `setup_ui_called_` race

`lcd_display.cc:1074` の SetEmotion で `setup_ui_called_=false` または `emoji_image_=nullptr` の場合 no-op return。
ただし起動シーケンス的に起こりにくい (User 報告は「ずっと変わらない」なので一過性 race とは違う)。

**期待されるエラーログ**:
```
W (xxx) LcdDisplay: SetEmotion('neutral') called before SetupUI() - emotion will not be displayed!
W (xxx) LcdDisplay: SetEmotion('neutral') failed: emoji_image_ is nullptr ...
```

### 🟢 仮説 D: partition_valid_ = false (mount 失敗)

`assets.cc:130 InitializePartition()` で `esp_partition_find_first("assets")` 失敗 → 後続全 no-op。
ただし md5 一致確認済なので **可能性ほぼ無し**。

**期待されるエラーログ**:
```
I (xxx) Assets: No assets partition found
E (xxx) Assets: The calculated checksum does not match
```

---

## 4. 診断手順 — serial log 1 本で切り分け

### 4.1 監視コマンド (WSL)

実機を USB-C で PC に接続し、`docs/operations/wsl-usb-device-setup.md` の手順で `/dev/ttyACM0` を attach 後:

```bash
cd ~/xiaozhi-work/xiaozhi-esp32-moji2-rebuild
source $HOME/esp/esp-idf/export.sh
idf.py -p /dev/ttyACM0 monitor
# 終了は Ctrl+]
```

### 4.2 観察対象 (起動から 30 秒の log)

| ログタグ | 期待する出力 | 出ない場合 |
|---|---|---|
| `I (xxx) Assets: Apply` 系 | partition mount 成功 | 仮説 D (partition 失敗) |
| `I (xxx) Assets: Custom emoji collection loaded count=21` | EmojiCollection 構築成功 | 仮説 B (magic 不在) or schema fail |
| `E (xxx) Assets: The asset ... is not valid with magic` | 仮説 B 確定 | 別仮説 |
| `E (xxx) Assets: Failed to get image info` | **仮説 A 確定** | 別仮説 |
| `E (xxx) lvgl_image: lodepng decode failed` | **仮説 A 確定 (decode 失敗の直接証拠)** | 別仮説 |
| `W (xxx) LcdDisplay: SetEmotion(...) called before SetupUI()` | 仮説 C | 別仮説 |
| 何もエラーが出ず emoji も変わらない | 仮説 A の silent failure 形 (decode 後の image_dsc が壊れている) | 追加調査 |

### 4.3 補助コマンド

emoji が表示されない時、AI に「今、嬉しい表情をして」と話しかけて SetEmotion 経路を強制発火:
```bash
# log で grep
idf.py -p /dev/ttyACM0 monitor 2>&1 | grep -E "Assets|LcdDisplay|emoji|lvgl_image"
```

---

## 5. 修正案

### 5.1 修正案 A2: PNG を 64×64 にリサイズ (★ 最優先、効果最大)

**手段**: [xiaozhi-assets-generator](https://github.com/xCentury-lab/xiaozhi-assets-generator) Web UI で xCentury cat_master_2k v2 の **出力サイズ指定を 256×256 → 64×64 に変更**して assets.bin 再生成。

| 項目 | 256×256 (現状) | 64×64 (修正後) |
|---|---|---|
| PNG ファイルサイズ | 23-37 KB | 推定 4-6 KB |
| Decode 後 RAW size | 256 KB | 16 KB (1/16) |
| assets.bin 全体 | 2.16 MB | 推定 0.5-0.7 MB |
| LCD 表示品質 | 360×360 画面に対し過剰 | 適切 (emoji 表示エリアは ~120-180px なので 64×64 で十分) |
| Decode heap 圧迫 | 大 | 小 |

**実施手順**:
1. xiaozhi-assets-generator Web UI を起動
2. xCentury cat_master_2k v2 emoji セットを load
3. **出力解像度を 64×64 に設定** (現状 256×256)
4. WakeNet9s モデル + フォントも含めて assets.bin 出力
5. `firmware/v2.2.6_movecall-moji2-esp32c5/assets.bin` を上書き
6. `merge_bin` 再実行 (`docs/operations/firmware-build-v2.2.6-esp32c5.md` Step 6 参照、xiaozhi.bin 再ビルドは不要)
7. 実機 assets partition (0x800000) のみ書込み (or `merged-binary.bin` 0x0 から書込み)

**副作用**: なし (LCD 表示品質は十分維持される)

### 5.2 修正案 A3: Twemoji フォールバックを追加 (★ 保険、1 行 patch)

**手段**: `lcd_display.cc:InitializeLcdThemes()` で emoji_collection が nullptr の場合 Twemoji64 をセット。

```diff
@@ main/display/lcd_display.cc:25 InitializeLcdThemes() @@
 void LcdDisplay::InitializeLcdThemes() {
     // light/dark theme 作成 ...
+    // Fallback: ensure emoji_collection is never nullptr to avoid silent failure
+    // when assets.bin Apply() fails or returns no emoji_collection.
+    if (light_theme->emoji_collection() == nullptr) {
+        light_theme->set_emoji_collection(std::make_shared<Twemoji64>());
+    }
+    if (dark_theme->emoji_collection() == nullptr) {
+        dark_theme->set_emoji_collection(std::make_shared<Twemoji64>());
+    }
 }
```

**効果**: assets.bin Apply 失敗時にも **本家 Twemoji64 (32×32 でないので少し大きい) が表示される** → 「何も出ない」状態から「本家 emoji が出る」状態にデグレード。**xCentury 黒猫表示問題自体は解決しない**が、無音 silent failure を可視化できる。

**副作用**: ROM サイズ +30-50 KB 程度 (Twemoji64 PNG bundle が xiaozhi.bin に embed される)

**注意**: 本家 Twemoji64 は `~/xiaozhi-work/xiaozhi-esp32-moji2-rebuild/main/display/lvgl_display/emoji_collection.cc:101` で定義済。

### 5.3 修正案 A2 + A3 組合せ (★ 最強)

- A2 で根本原因 (256×256 decode heap 不足) を解決
- A3 で **将来 assets.bin が失敗した場合の silent failure 防止** (二重防御)
- 量産時の出荷後 OTA で assets.bin に問題があっても本家 Twemoji が出る

---

## 6. 量産時の予防策

### 6.1 PNG サイズの量産規格

| LCD サイズ | 推奨 emoji PNG サイズ | 理由 |
|---|---|---|
| 240×240 | 32×32 〜 48×48 | 表示エリアが小さい |
| 320×240 / 360×360 (Moji 2.0) | **64×64 〜 80×80** | ⭐ 本件の推奨 |
| 480×320 / 480×480 | 96×96 〜 128×128 | 高解像度向け |

**規則**: decode 後 RAW size を **1 枚あたり 64 KB 以下**に収める (PNG 128×128 RGBA = 64 KB)。

### 6.2 assets.bin sanity check

`docs/operations/firmware-build-v2.2.6-esp32c5.md` Step 7 に追加候補:
```bash
# assets.bin の各 emoji PNG が想定サイズ以下か検証
python tools/inspect_assets.py firmware/v2.2.6_movecall-moji2-esp32c5/assets.bin --max-png-bytes 16384
```

(tools/inspect_assets.py は将来実装候補)

### 6.3 量産前の必須実機テスト

`docs/operations/flash-guide.md` 量産フローに追加すべき:
- emoji 切替テスト: AI に「嬉しい/悲しい/驚いた表情」を順番に依頼
- 全 21 emoji が想定通りに切り替わるか目視確認
- serial log で `Failed to get image info` 系の警告が出ないこと

---

## 7. 次のアクション

### 🚨 即時 (User 作業)

1. **実機を WSL に USB 接続** (`docs/operations/wsl-usb-device-setup.md`)
2. **`idf.py monitor` で 30 秒のログ取得** (起動 → 数回の emotion 変化)
3. **§4.2 のログタグを grep して仮説 A/B/C/D を特定**

### 📦 仮説 A 確定後

4. **A2 適用**: xiaozhi-assets-generator で 64×64 emoji を再生成 → assets.bin 上書き → assets partition 単独書込
5. **再 monitor**: emoji 表示確認 + heap 余裕確認 (`heap_caps_get_free_size`)
6. **A3 適用 (任意保険)**: `lcd_display.cc:InitializeLcdThemes` に Twemoji64 フォールバック → xiaozhi.bin 再ビルド + merge_bin
7. **manifest.json v4 として記録**

### 🔁 ループ防止 (再発対策)

8. `docs/operations/firmware-build-v2.2.6-esp32c5.md` Step 8 (検証) に「emoji 切替テスト + heap free 余裕確認」を追記
9. xiaozhi-assets-generator の出力デフォルトを 64×64 に変更 (project memory `xiaozhi_assets_generator` 参照)

---

## 8. 関連 doc / コードリファレンス

### 8.1 同 project 内 doc

- [../architecture/moji2-board-overview.md](../architecture/moji2-board-overview.md) — Moji 2.0 board 仕様
- [../hardware/moji2-schematic-power-tree.md](../hardware/moji2-schematic-power-tree.md) — 回路図 + BOM
- [./firmware-build-v2.2.6-esp32c5.md](./firmware-build-v2.2.6-esp32c5.md) — ビルド完全手順
- [./wsl-usb-device-setup.md](./wsl-usb-device-setup.md) — WSL USB serial 接続手順

### 8.2 ファーム source code (`~/xiaozhi-work/xiaozhi-esp32-moji2-rebuild/` 基準)

| ファイル | 行 | 内容 |
|---|---|---|
| `main/application.cc` | :328, :340, :393 | CheckAssetsVersion → Apply 経路 |
| `main/assets.cc` | :214 | `LvglStrategy::Apply()` (emoji_collection 構築) |
| `main/assets.cc` | :230 | `version > 1` reject |
| `main/assets.cc` | :262-264 | emoji_collection JSON parse |
| `main/display/lcd_display.cc` | :25 | `InitializeLcdThemes()` (フォールバック追加候補) |
| `main/display/lcd_display.cc` | :1074-1100 | `SetEmotion()` (emoji 表示の hot path) |
| `main/display/lvgl_display/emoji_collection.cc` | :53, :101 | Twemoji32 / Twemoji64 クラス (フォールバック候補) |
| `main/display/lvgl_display/lvgl_image.cc` | :12 | `LvglRawImage` (PNG decode 結果保持) |
| `main/boards/movecall-moji2-esp32c5/movecall_moji2_esp32s3.cc` | :216 | Moji2.0 board (SpiLcdDisplay 確認) |

### 8.3 外部リソース

- xiaozhi-assets-generator: https://github.com/xCentury-lab/xiaozhi-assets-generator
- 本家 xiaozhi-esp32: https://github.com/78/xiaozhi-esp32 (v2.2.6 タグ)
- LVGL Image API: https://docs.lvgl.io/master/widgets/image.html
- ESP-IDF heap API: https://docs.espressif.com/projects/esp-idf/en/latest/esp32c5/api-reference/system/heap_debug.html

---

## 9. 変更履歴

| 日付 | 変更 | 担当 |
|---|---|---|
| 2026-05-30 | 初版作成、Engineer 並列 audit 結果を集約、serial log 取得待ち | xCentury PAI |

---

*本 doc は調査中ステータス。実機 serial log 取得後に §4 観察結果と §5 修正案を実施 → §3 仮説を確定 → 真因と修正効果を §9 に追記すること。*
