# Xiaozhi ファームウェア カスタマイズ要件定義書

> **対象ファーム**: `v2.2.6_esp-vocat_V1.0_ja-JP_Wakeword_OTA_YYYYMMDD.bin` (ESP-VoCat 商品化対象)
> **ベース**: [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) `v2.2.6`
> **対象ハード**: ESP-VoCat V1.0 (ESP32-S3, 360×360 円形ディスプレイ, 16MB Flash)
> **ブランド**: company (xCentury) — manifest 内記録のみ、UI 非表示
> **最終更新**: 2026-05-24
> **ドキュメント目次**: [README.md](README.md)

---

## 🎯 カスタマイズ概要

本家 Xiaozhi ファームを日本国内 OEM 向けにカスタマイズし、量産体制で再現可能な形でビルド・出荷する。カスタマイズは以下の **4 軸**で定義する。

| # | 軸 | 本家デフォルト | 本要件定義 | 言語限定? |
|---|---|---|---|---|
| 1 | UI 言語 | 中国語 (zh-CN) | **日本語 (ja-JP)** | — |
| 2 | ウェイクワード | 你好小智 | **Alexa + 你好喵伴** (ESP-VoCat) | — |
| 3 | OTA サーバー URL | `api.tenclass.net/xiaozhi/ota/` | **`classism.net/xiaozhi/ota/`** | — |
| 4 | **ja-JP 音声マスタ** (発音修正) | 本家 ja-JP 音声 (発音誤りあり) | **自家整備 `assets/sounds/locales/ja-JP/`** | **ja-JP 限定** |

> **2026-05-24 軸定義変更**:
> - 旧「ブート時ブランドロゴ」軸 ❌ 削除 (ESP-VoCat は emote::EmoteDisplay 主体でロゴ非表示のため不要)
> - 旧「ボード別カスタム起動音」軸 → **「ja-JP 音声マスタ (発音修正)」に再定義**。ボード非依存、ja-JP の本家音声発音誤りの修正のみが目的。英語版は本家音声をそのまま使用。
> - 旧「ブランド定義」軸は manifest 記録のみで残し、独立軸からは除外。

---

## 1️⃣ UI 言語: Japanese (ja-JP)

### 要件
- デバイス UI（ステータスメッセージ・ダイアログ・通知）は**全て日本語表示**
- 文字コード: UTF-8、LVGL 描画フォントは CJK 対応
- 翻訳ソースは本家 `main/assets/locales/ja-JP/` を流用（OEM 翻訳レビューは別途）

### 設定ファイル
| 項目 | ファイル / キー |
|---|---|
| sdkconfig | `CONFIG_LANGUAGE_JA_JP=y`（他の `CONFIG_LANGUAGE_*` は `is not set`） |
| 本家ソース | [`main/assets/locales/ja-JP/`](https://github.com/78/xiaozhi-esp32/tree/v2.2.4/main/assets/locales/ja-JP) |
| 本家フォント | `font_puhui_basic_16_4`（Waveshare 1.85c デフォルト、 `main/CMakeLists.txt:339`） |

### 検証基準
- シリアル起動ログに `CONFIG_LANGUAGE_JA_JP=y` が反映
- 画面に「接続中」「録音中」「録音完了」等の日本語が正しく描画される
- OTA チェック時の `Please Wait` が日本語化される

---

## 2️⃣ ウェイクワード: Alexa + Hi, ESP

### 要件
- 同時有効化ウェイクワード: **`Alexa` と `Hi, ESP` の 2 つ**
- モデルは Espressif 公式 ESP-SR v2.x プリビルド TTS モデル
- 日本語話者が発音しやすい組合せを採用（[wake-word-selection.md](operations/wake-word-selection.md) 参照）

### 選定根拠
| 観点 | 採択理由 |
|---|---|
| 日本語話者適性 | 「アレクサ」「ハイ・イー・エス・ピー」ともに 2〜4 音節で明瞭 |
| 認知度 | `Alexa` は Amazon スマートスピーカーで日本市場でも定着 |
| 実機検証 | `Hi, ESP` は 2026-04-18 日本語ネイティブ話者で検出成功確認済 |
| 却下案 | `Jarvis` は日本語発音では検出閾値 (0.627) 未達で却下 |

### 設定ファイル
| 項目 | ファイル / キー |
|---|---|
| sdkconfig | `CONFIG_SR_WN_WN9_ALEXA=y`, `CONFIG_SR_WN_WN9_HIESP=y`（`CONFIG_SR_WN_WN9_JARVIS_TTS` は `is not set`） |
| モデル配置 | `$IDF_PATH/managed_components/espressif__esp-sr/model/wakenet_model/wn9_alexa,wn9_hiesp`（ESP-IDF 経由で自動取得） |
| ロード先 | AFE (Audio Front-End) プライマリ＋セカンダリスロットに静的リンク |

### 検証基準
- シリアル起動ログに以下が出力されること
  ```
  I (xxxx) AfeWakeWord: Model 0: wn9_hiesp
  I (xxxx) AfeWakeWord: Model 1: wn9_alexa
  I (xxxx) AFE: AFE Pipeline: ... -> |WakeNet(wn9_hiesp,wn9_alexa)| -> ...
  ```
- 実機で「Alexa」「ハイ・イー・エス・ピー」を発話し、どちらでも会話モードに遷移すること
- 最大 2 個制限に抵触しないこと（3 個以上同時有効化不可は [wake-word-selection.md § 技術的制約](operations/wake-word-selection.md#-技術的制約最大-2-個)）

---

## 3️⃣ OTA サーバー URL: classism.net

### 要件
- OTA チェックURL を本家 `api.tenclass.net` から自社運用の `classism.net` に**コンパイル時組込**
- バイナリへの事後パッチ適用（`tools/patch_bin.py` 等）ではなく、sdkconfig での事前指定を必須とする（量産ラインでの人為ミス防止）

### 設定ファイル
| 項目 | ファイル / キー |
|---|---|
| sdkconfig | `CONFIG_OTA_URL="https://classism.net/xiaozhi/ota/"` |
| matrix.yaml | `brands.company.ota_url: https://classism.net/xiaozhi/ota/` |
| 本家 Kconfig | `main/Kconfig.projbuild` → `OTA_URL` エントリ |

### 検証基準
- 新ファームの `xiaozhi.bin` 内に文字列 `https://classism.net/xiaozhi/ota/` が存在
- 旧 URL `api.tenclass.net` が**一切含まれない**（QA チェック: [matrix.yaml § forbidden_strings](../build/matrix.yaml)）
- 初回起動時、デバイスから `classism.net` に HTTP(S) リクエストが発生する

---

## ~~4️⃣ ブート時ブランドロゴ: 「和合」~~ (廃止 2026-05-24)

> **⚠️ 本セクションは 2026-05-24 廃止**: ESP-VoCat は `emote::EmoteDisplay` 主体でブートロゴ非表示。lcd_display.cc のロゴパッチはランタイムに反映されないため、軸自体を削除。以下は履歴記録として保持。



### 要件
- デバイス電源投入〜初回会話開始前に画面中央に**「和合」の文字**を表示
- 色はテーマの `text_color()`（ライト: 黒 / ダーク: 白）に従う
- フォントは CJK 対応、サイズは 30px（puhui 30_4）
- 会話メッセージ到着または Emotion 表示開始時にロゴは自動で非表示

### 設計方針
本家は `FONT_AWESOME_MICROCHIP_AI` (Unicode 私用領域 `\xee\x87\xac`) の Font Awesome アイコンを `font_awesome_30_4` で描画。これを、

- **CJK 対応フォント** `font_puhui_30_4`（「和」U+548C, 「合」U+5408 を含む）
- **文字列リテラル** `"和合"`

に置き換える。

### 影響範囲
- `emoji_label_` オブジェクトは起動時ロゴ表示 + Font Awesome ベース Emote fallback の 2 用途で共用されている
- Emote fallback 経路 (`SetEmotion()` 内 `font_awesome_get_utf8()` が非 null の場合) では `large_icon_font` にフォントを戻す必要あり
- Waveshare 1.85c では `DEFAULT_EMOJI_COLLECTION=twemoji_64` が設定済のため通常 Emote は画像経由となり fallback 経路は通常発火しないが、安全のため復帰処理を追加

### 設定ファイル
| 項目 | ファイル / 行 |
|---|---|
| ロゴ表示コード (メイン SetupUI) | [`main/display/lcd_display.cc`](https://github.com/78/xiaozhi-esp32/blob/v2.2.4/main/display/lcd_display.cc) L495-497 |
| ロゴ表示コード (emote_box 版 SetupUI) | 同上 L841-843 |
| フォント宣言追加 | 同上 L24 `LV_FONT_DECLARE(font_puhui_30_4);` |
| Emote fallback 復帰処理 | 同上 `SetEmotion()` 関数内 `font_awesome_get_utf8` 分岐 |
| フォント実体 | [`managed_components/78__xiaozhi-fonts/src/font_puhui_30_4.c`](https://github.com/78-home/xiaozhi-fonts) |

### 差替え手順（本家ソース直接改変）
```cpp
// main/display/lcd_display.cc
// 1. トップに追加
LV_FONT_DECLARE(font_puhui_30_4);

// 2. SetupUI 2箇所で:
lv_obj_set_style_text_font(emoji_label_, &font_puhui_30_4, 0);
lv_label_set_text(emoji_label_, "和合");

// 3. SetEmotion() の font_awesome fallback 分岐で:
auto lvgl_theme = static_cast<LvglTheme*>(current_theme_);
lv_obj_set_style_text_font(emoji_label_, lvgl_theme->large_icon_font()->font(), 0);
lv_label_set_text(emoji_label_, utf8);
```

### 検証基準
- 起動直後〜Wi-Fi 接続開始前に画面中央に「和合」が表示される
- 初回会話開始時にロゴが消える
- Emote (happy/sad/angry 等) 表示時に文字化けしない（twemoji 画像が正常に描画される）

### 将来拡張: 画像ロゴ化
テキスト「和合」ではなく PNG ロゴに差替える場合は [asset-spec.md](asset-spec.md) 参照（Phase 1-B〜1-C 実装予定）。本要件定義では**テキスト方式を MVP として採用**し、ブランド確定後に画像化する。

---

## 5️⃣ ブランド定義: company (xCentury)

### 要件
- manifest.json / matrix.yaml 上での**ブランド識別メタデータ**として定義
- 現時点ではデバイス UI への `xCentury` 文字表示は**行わない**（ロゴ「和合」で代替）
- 将来、ロゴ画像差替え・カスタム起動音対応時のアセット格納先名として機能

### 設定ファイル
| 項目 | ファイル / キー |
|---|---|
| マトリクス定義 | [`build/matrix.yaml`](../build/matrix.yaml) `brands.company` |
| manifest.json | `"brand": "company (xCentury)"` |
| ロゴ格納先（将来） | [`assets/logos/{board}/company/`](../assets/logos/waveshare-esp32-s3-touch-lcd-1.85c/company/) |
| 起動音格納先（将来） | [`assets/sounds/{board}/company/`](../assets/sounds/waveshare-esp32-s3-touch-lcd-1.85c/company/) |

### 現状と今後
| 項目 | 現状 | 今後 |
|---|---|---|
| OTA URL | ✅ `classism.net` 反映済 | — |
| ブート文字ロゴ | ✅ 「和合」 | PNG ロゴ化（Phase 1-B） |
| 起動音 | ⚠️ 本家デフォルト | OEM カスタム音源差替え（Phase 1-C） |
| sdkconfig フラグ | `CONFIG_FLASH_DEFAULT_ASSETS=y` | `CONFIG_FLASH_CUSTOM_ASSETS=y` へ移行予定 |

---

## 📦 成果物 (Build Artifacts)

### 出力構造
```
firmware/v2.2.4_waveshare-1.85c_V1.0_ja-JP_alexa-hiesp_company/
├── xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_alexa-hiesp_company_YYYYMMDD.bin  # 配布用（merged）
├── merged-binary.bin                       # 上と同一
├── bootloader.bin                          # 0x0
├── partition-table.bin                     # 0x8000
├── ota_data_initial.bin                    # 0xd000
├── xiaozhi.bin                             # 0x20000（アプリ本体）
├── generated_assets.bin                    # 0x800000（SPIFFS アセット）
├── flash_args                              # esptool 引数
└── manifest.json                           # ビルドメタデータ
```

### manifest.json 必須フィールド
```json
{
  "firmware_name": "...",
  "board_sku": "waveshare-esp32-s3-touch-lcd-1.85c",
  "hardware_revision": "V1.0",
  "xiaozhi_version": "v2.2.4",
  "language": "Japanese (ja-JP)",
  "wake_words": ["Alexa", "Hi,ESP"],
  "wake_word_models": ["wn9_alexa", "wn9_hiesp"],
  "brand": "company (xCentury)",
  "ota_url": "https://classism.net/xiaozhi/ota/",
  "build_date": "YYYYMMDD",
  "binary_sha256": "sha256:...",
  "binary_size_bytes": N,
  "sdkconfig_key_values": { ... },
  "brand_logo_style": "text:和合 (font_puhui_30_4)",
  "builder": "xxc@ctoch.jp",
  "source_commit": "78/xiaozhi-esp32@v2.2.4"
}
```

---

## 🔧 ビルド環境

| 項目 | 要件 |
|---|---|
| ESP-IDF | v5.5.2 以上（推奨 **v5.5.4**） |
| ターゲット | `esp32s3` |
| パーティション | `partitions/v2/16m.csv`（dual-OTA + assets SPIFFS 8MB） |
| Flash サイズ | 16MB |
| Flash モード | QIO, 80MHz |
| ビルダ環境変数 | `XIAOZHI_SRC=<本家ソースのパス>` |

---

## ✅ 受入試験 (Acceptance Criteria)

### 静的検証（`build/verify_build.py` で自動化）
- [ ] `xiaozhi.bin` 内に文字列 `https://classism.net/xiaozhi/ota/` が存在
- [ ] `xiaozhi.bin` 内に文字列 `api.tenclass.net` が**存在しない**
- [ ] `manifest.json` の `wake_words` が `["Alexa", "Hi,ESP"]` に一致
- [ ] `manifest.json` の `language` が `Japanese (ja-JP)` に一致
- [ ] `binary_size_bytes` が 8〜10MB の範囲内
- [ ] `binary_sha256` が記録されており実バイナリと一致

### 動的検証（実機 Waveshare 1.85c で確認）
- [ ] 電源投入直後〜Wi-Fi 接続前に画面中央に「**和合**」が表示される
- [ ] Wi-Fi プロビジョニング画面が日本語で表示される
- [ ] 起動ログに `Set WakeNet Model: wn9_hiesp` と `Set Second WakeNet Model: wn9_alexa` が出力される
- [ ] 「**Alexa**」発話でウェイクワード検出、会話モード移行
- [ ] 「**ハイ・イー・エス・ピー**」発話でウェイクワード検出、会話モード移行
- [ ] 会話開始後、ロゴ「和合」が自動で非表示になる
- [ ] OTA チェック通信先が `classism.net` であることをネットワークキャプチャで確認
- [ ] 会話応答時に twemoji_64 絵文字が正常に描画される（文字化けしない）

---

## 🔗 関連ドキュメント

- [build-plan.md](build-plan.md) — 全体計画（STEP1/STEP2）
- [operations/wake-word-selection.md](operations/wake-word-selection.md) — ウェイクワード選定ガイド
- [operations/flash-guide.md](operations/flash-guide.md) — 書込手順
- [asset-spec.md](asset-spec.md) — 画像・音声仕様（Phase 1-B/C）
- [translation-source.md](translation-source.md) — 翻訳対象ファイル一覧
- [../build/matrix.yaml](../build/matrix.yaml) — ビルドマトリクス定義
- [../build/build_matrix.py](../build/build_matrix.py) — 量産ビルドスクリプト

---

## 改訂履歴

| 日付 | バージョン | 内容 | 作成者 |
|---|---|---|---|
| 2026-04-18 | 1.0 | 初版。ja-JP + Alexa/Hi,ESP + classism.net + 「和合」ロゴ + company(xCentury) の 5 軸を正式定義 | xxc@ctoch.jp |
