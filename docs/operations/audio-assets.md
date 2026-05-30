# 音声アセット リファレンス

> **対象**: Xiaozhi ファームウェアに埋め込まれる音声（起動音・通知音・案内音声）
> **目的**: 音声ファイルの所在・用途・埋込方式・カスタマイズ手順の一元整理
> **作成日**: 2026-04-18
> **ドキュメント目次**: [../README.md](../README.md)
> **関連**: [../asset-spec.md](../asset-spec.md)（仕様計画書）/ [../../assets/sounds/README.md](../../assets/sounds/README.md)（制作仕様）

---

## 📌 結論サマリ

- 音声ファイルは **2 箇所** に存在し、**2 カテゴリ**（言語依存/共通）に分かれる
- 実機書込時に 1 ビルドあたり **22 ファイル** が app バイナリに埋め込まれる
- 組込方式: `CMake EMBED_FILES` によるバイナリシンボル化（SPIFFS/LittleFS ではない）
- 言語切替は `CONFIG_LANGUAGE_XX_YY` Kconfig で制御
- 現在の実機ビルドに含まれるのはすべて **本家オリジナル音声**（xCentury ブランド未適用）

---

## 1. 音声ファイルの所在

### 1-1. 本家 `xiaozhi-esp32` 側（ビルド時に埋込）

本家ソース: `~/xiaozhi-work/xiaozhi-esp32/main/assets/`

```
main/assets/
├── common/                 ← 言語非依存（全ロケール共通）
│   ├── success.ogg
│   ├── exclamation.ogg
│   ├── popup.ogg
│   ├── low_battery.ogg
│   └── vibration.ogg
└── locales/                ← 言語依存
    ├── ar-SA/ ...           （39 ロケール）
    ├── en-US/
    │   ├── 0.ogg ~ 9.ogg
    │   ├── activation.ogg
    │   ├── err_pin.ogg
    │   ├── err_reg.ogg
    │   ├── upgrade.ogg
    │   ├── welcome.ogg
    │   ├── wificonfig.ogg
    │   └── language.json    （UI 文字列、音声ではない）
    ├── ja-JP/ ...           （同じ 17 ファイル構成）
    ├── zh-CN/ ...
    └── ...
```

同梱言語: `ar-SA bg-BG ca-ES cs-CZ da-DK de-DE el-GR en-US es-ES fa-IR fi-FI fil-PH fr-FR he-IL hi-IN hr-HR hu-HU id-ID it-IT ja-JP ko-KR ms-MY nb-NO nl-NL pl-PL pt-PT ro-RO ru-RU sk-SK sl-SI sr-RS sv-SE th-TH tr-TR uk-UA vi-VN zh-CN zh-TW`

### 1-2. 本プロジェクト `Xiaozhi-Firmware-update/assets/sounds/`（マスタ・カスタム音声）

```
assets/sounds/
├── README.md                                    ← 仕様書 + 3 層構造定義
├── locales/                                     ← ★ 言語別マスタ (2026-05-24 整備)
│   └── ja-JP/                                   ← 日本語マスタ 20 ファイル
│       ├── README.md
│       ├── 0.ogg 〜 9.ogg, activation.ogg, ...   ← 正規 .ogg (ビルド対象)
│       ├── language.json                        ← UI 文字列
│       ├── *.ogg.bak                            ← 過去版参考
│       └── soniox-tts-*.wav                     ← TTS 元 WAV
├── master/                                      ← raw WAV master (44.1kHz/16bit)
│   └── .gitkeep
└── waveshare-esp32-s3-touch-lcd-1.85c/
    └── company/                                 ← ボード×ブランド別カスタム (Phase 1-C)
        └── .gitkeep
```

**現状: `locales/ja-JP/` 整備済 (自己完結)。`master/` と `{board}/{brand}/` は Phase 1-C で制作予定。**

---

## 2. 音声ファイル別の用途と再生タイミング

### 2-1. 共通音声（`main/assets/common/*.ogg`）

| ファイル | 再生タイミング | コード参照 |
|---|---|---|
| `success.ogg` | アクティベーション成功等 | `Lang::Sounds::OGG_SUCCESS` |
| `exclamation.ogg` | モデム初期化失敗・通信失敗・アセット DL エラー等 | `Lang::Sounds::OGG_EXCLAMATION` |
| `popup.ogg` | ポップアップ通知 | （未使用確認要）|
| `low_battery.ogg` | バッテリー低下警告 | （battery manager）|
| `vibration.ogg` | サーバ/MQTT からのステータス更新通知 | `Lang::Sounds::OGG_VIBRATION` |

### 2-2. 言語依存音声（`main/assets/locales/{lang}/*.ogg`）

| ファイル | 再生タイミング | コード参照 |
|---|---|---|
| `welcome.ogg` | 初期状態で再生される起動音挨拶 | `Lang::Sounds::OGG_WELCOME` |
| `wificonfig.ogg` | Wi-Fi 設定モード入った時の案内音声 | `Lang::Sounds::OGG_WIFICONFIG` |
| `activation.ogg` | アクティベーション画面遷移時 | `Lang::Sounds::OGG_ACTIVATION` |
| `upgrade.ogg` | OTA アップグレード中の案内 | `Lang::Sounds::OGG_UPGRADE` |
| `err_pin.ogg` | SIM カード未挿入エラー | `Lang::Sounds::OGG_ERR_PIN` |
| `err_reg.ogg` | ネットワーク登録失敗 | `Lang::Sounds::OGG_ERR_REG` |
| `0.ogg` 〜 `9.ogg` | 数字読み上げ（アクティベーションコード・数値読上）| `Lang::Sounds::OGG_0` 〜 `OGG_9` |

### 2-3. `main/application.cc` での使用例

```cpp
// エラー通知
Alert(Lang::Strings::ERROR, Lang::Strings::PIN_ERROR,
      "triangle_exclamation", Lang::Sounds::OGG_ERR_PIN);

Alert(Lang::Strings::ERROR, Lang::Strings::REG_ERROR,
      "triangle_exclamation", Lang::Sounds::OGG_ERR_REG);

Alert(Lang::Strings::ERROR, Lang::Strings::MODEM_INIT_ERROR,
      "triangle_exclamation", Lang::Sounds::OGG_EXCLAMATION);

// 成功通知
audio_service_.PlaySound(Lang::Sounds::OGG_SUCCESS);

// OTA アップグレード中
Alert(Lang::Strings::LOADING_ASSETS, message,
      "cloud_arrow_down", Lang::Sounds::OGG_UPGRADE);

// サーバ status 通知
Alert(status, message, emotion, Lang::Sounds::OGG_VIBRATION);

// 数字読み上げ（activation code など）
digit_sound{'0', Lang::Sounds::OGG_0},
digit_sound{'1', Lang::Sounds::OGG_1},
// ... '9', Lang::Sounds::OGG_9
```

---

## 3. 埋込方式（ビルドシステム）

### 3-1. `main/CMakeLists.txt` の組立ロジック

```cmake
# 1. 選択言語ディレクトリを決定（CONFIG_LANGUAGE_XX_YY から）
if(CONFIG_LANGUAGE_EN_US)
    set(LANG_DIR "en-US")
elseif(CONFIG_LANGUAGE_JA_JP)
    set(LANG_DIR "ja-JP")
elseif(CONFIG_LANGUAGE_ZH_CN)
    set(LANG_DIR "zh-CN")
# ... 他 36 言語
endif()

# 2. 言語ディレクトリから .ogg を全収集
file(GLOB LANG_SOUNDS
     ${CMAKE_CURRENT_SOURCE_DIR}/assets/locales/${LANG_DIR}/*.ogg)

# 3. 共通音声を収集
file(GLOB COMMON_SOUNDS
     ${CMAKE_CURRENT_SOURCE_DIR}/assets/common/*.ogg)

# 4. app バイナリにバイナリデータとして埋込
idf_component_register(
    ...
    EMBED_FILES ${LANG_SOUNDS} ${COMMON_SOUNDS}
)
```

### 3-2. シンボル自動生成

ビルドツールが `main/assets/lang_config.h` を自動生成:

```cpp
namespace Lang::Sounds {
    // リンカシンボル
    extern const char ogg_welcome_start[] asm("_binary_welcome_ogg_start");
    extern const char ogg_welcome_end[]   asm("_binary_welcome_ogg_end");

    // std::string_view でアクセス可能にする
    static const std::string_view OGG_WELCOME {
        static_cast<const char*>(ogg_welcome_start),
        static_cast<size_t>(ogg_welcome_end - ogg_welcome_start)
    };
    // ... 他のシンボル
}
```

### 3-3. ストレージ方式の選択比較

| 方式 | 採用状況 | 特徴 |
|---|---|---|
| **バイナリ埋込（`EMBED_FILES`）**| ✅ **現行** | app.bin に含まれる、RAM/Flash 直アクセス、OTA 単一更新 |
| SPIFFS / LittleFS | ✗ 不採用 | 別パーティション、柔軟だが初回焼込複雑 |
| C 配列（`xxd` 出力）| ✗ 不採用 | ソース管理大、コンパイル時間増 |

**結論**: 現状は `EMBED_FILES` 方式（Opus/OGG 圧縮済で容量は十分小さい）。

---

## 4. 言語切替の Kconfig 設定

### 4-1. Kconfig シンボル

`main/Kconfig.projbuild` 抜粋:

```kconfig
choice LANGUAGE
    prompt "Default Language"
    default LANGUAGE_ZH_CN
    config LANGUAGE_ZH_CN bool "Chinese"
    config LANGUAGE_ZH_TW bool "Chinese Traditional"
    config LANGUAGE_EN_US bool "English"
    config LANGUAGE_JA_JP bool "Japanese"
    config LANGUAGE_KO_KR bool "Korean"
    # ... 他 30+ 言語
endchoice
```

### 4-2. sdkconfig での指定例

```bash
# 英語版
CONFIG_LANGUAGE_EN_US=y
# → en-US ディレクトリの .ogg + common/ が埋込

# 日本語版
CONFIG_LANGUAGE_JA_JP=y
# → ja-JP ディレクトリの .ogg + common/ が埋込
```

### 4-3. `idf.py menuconfig` 経由の切替

```bash
cd $XIAOZHI_SRC && get_idf
idf.py menuconfig
# → Xiaozhi Assistant → Default Language → English/Japanese/...
```

---

## 5. 現在の実機ビルドに含まれる音声

2026-04-18 時点の日本語版ファームウェア
（`xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_20260418.bin`）に含まれる音声:

### 共通音声（5 ファイル、すべての言語で共通）

| ファイル | サイズ（概算）| 用途 |
|---|---|---|
| `common/success.ogg` | 数 KB | 成功音 |
| `common/exclamation.ogg` | 数 KB | エラー音 |
| `common/popup.ogg` | 数 KB | ポップアップ通知 |
| `common/low_battery.ogg` | 数 KB | バッテリー警告 |
| `common/vibration.ogg` | 数 KB | 振動/通知トーン |

### 日本語音声（17 ファイル、`locales/ja-JP/`）

| ファイル | 用途 | 音声の想定内容 |
|---|---|---|
| `welcome.ogg` | 起動時挨拶 | 「こんにちは」等 |
| `wificonfig.ogg` | Wi-Fi 設定モード | 「Wi-Fi 設定モードです」等 |
| `activation.ogg` | アクティベーション | 「デバイスをアクティベートしてください」等 |
| `upgrade.ogg` | アップグレード中 | 「アップグレード中です」等 |
| `err_pin.ogg` | SIM エラー | 「SIM カードを確認してください」等 |
| `err_reg.ogg` | ネットワークエラー | 「ネットワークに接続できません」等 |
| `0.ogg` 〜 `9.ogg` | 数字読み上げ | 「ゼロ」「イチ」…「キュウ」 |

**合計 22 ファイル**（すべて本家オリジナル、xCentury ブランドカスタマイズ未適用）。

---

## 6. カスタム音声への差替手順

### 6-1. 方式 A: 本家 `locales/{lang}/` に直接配置（最もシンプル）

自社制作の「xCentury 起動挨拶」を日本語版 `welcome.ogg` に差替える例:

```bash
# Step 1: 自社制作音声を仕様通りに変換
#   要件: 16 kHz Mono、Opus/OGG、-14 LUFS
ffmpeg -i master/my-company-welcome.wav \
       -ar 16000 -ac 1 \
       -af "loudnorm=I=-14:TP=-1:LRA=11" \
       -c:a libopus -b:a 32k \
       ~/xiaozhi-work/xiaozhi-esp32/main/assets/locales/ja-JP/welcome.ogg

# Step 2: リビルド
cd ~/xiaozhi-work/xiaozhi-esp32 && get_idf
idf.py build

# Step 3: 実機書込
python -m esptool --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    write_flash 0x0 build/merged-binary.bin
```

**欠点**: 本家リポジトリを直接改変するため、本家の更新時にコンフリクトしやすい。

### 6-2. 方式 B: 本プロジェクトからの自動注入（Phase 1-C で完成予定）

[build-plan.md § Phase 1-C](../build-plan.md) の計画:

```bash
# Phase 1-C 完成時の想定ワークフロー
python build/build_matrix.py \
    --board waveshare-esp32-s3-touch-lcd-1.85c \
    --lang Japanese \
    --brand company
```

内部動作:
1. `build/inject_assets.py` が `assets/sounds/waveshare-.../company/` 配下の音声を `main/assets/locales/ja-JP/` に上書きコピー
2. `idf.py build` 実行
3. ビルド後、本家の元ファイルを復元（clean workspace）

**実装状況**: `inject_assets.py` はスケルトンのみ（[Review/action-items.md § B-4](../Review/action-items.md) 参照）

---

## 7. フォーマット要件（[assets/sounds/README.md](../../assets/sounds/README.md) より）

| 項目 | 要件 | 理由 |
|---|---|---|
| サンプルレート | **16 kHz** | 音声認識と統一（AFE の入力レートと整合）|
| ビット深度 | 16 bit PCM | 標準 |
| チャンネル | **Mono** | スピーカー 1 基のため |
| コーデック | **Opus（OGG コンテナ）** | 本家と統一、圧縮率良好 |
| 音量 | **-14 LUFS** | デバイス間の音量統一 |
| 長さ | 起動音 2 秒以内 / 効果音 1 秒以内 | ユーザー体感の即時性 |

### 変換コマンド例

```bash
# サンプルレート統一 → Mono 化 → 音量正規化 → Opus 圧縮
ffmpeg -i master/source.wav \
       -ar 16000 -ac 1 \
       -af "loudnorm=I=-14:TP=-1:LRA=11" \
       -c:a libopus -b:a 32k \
       output.ogg
```

---

## 8. 著作権管理

[assets/sounds/README.md](../../assets/sounds/README.md) の方針:

- マスター音声は **ロイヤリティフリー素材または自社独自制作のみ** 使用
- 購入ライセンス素材の場合、ライセンス書面を `docs/licenses/` に保管
- 日本語音声を人間声優で制作する場合、**権利譲渡契約書を明示**

マスター WAV は `.gitignore` で除外、社内ファイルサーバ管理:
- `\\fileserver\xiaozhi-assets\sounds\master\`

---

## 9. 実機で音声再生を確認する方法

### 9-1. シリアルログでの再生ログ確認

```bash
get_idf
cd $XIAOZHI_SRC
idf.py -p /dev/ttyACM0 monitor
# Ctrl+] で終了
```

再生時に以下のようなログが流れる:

```
I (xxxx) AudioService: PlaySound started: welcome.ogg (duration: 1500 ms)
I (xxxx) AudioService: PlaySound done
```

### 9-2. 実機の挙動パターン

| 状況 | 期待される音声 |
|---|---|
| 電源 ON → Wi-Fi 設定モード入ると | `wificonfig.ogg` |
| Wi-Fi 接続完了 → アクティベーション画面 | `activation.ogg` → 数字読み上げ（`0.ogg` 〜 `9.ogg`）|
| MQTT 接続 → ステータス通知 | `vibration.ogg` |
| OTA 新バージョン検出 | `upgrade.ogg` |
| エラー発生 | `err_pin.ogg` / `err_reg.ogg` / `exclamation.ogg` |

---

## 10. よくある質問

### Q1. 本家 ja-JP の音声は誰が録音したもの？
A. Espressif 公式 or コミュニティ提供。詳細は本家 [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) の issue/commit 履歴参照。商用利用する場合、本家ライセンス（MIT）範囲内では問題ないが、**OEM ブランド配布時は営業/法務確認推奨**。

### Q2. 音声を変えずに UI だけ変えたい
A. `main/assets/locales/{lang}/language.json` を編集するだけで UI 文字列は変わる（音声ファイルは触らない）。ただし `idf.py build` で再ビルド・再書込必要。

### Q3. 日本語音声を差し替えずに英語版の音声を使いたい
A. `CONFIG_LANGUAGE_EN_US=y` でビルドすれば OK。UI も英語になる。UI だけ日本語で音声だけ英語、は標準構成では不可（同一 Kconfig スイッチで両方決まる）。

### Q4. 音声ファイルが埋め込まれた実機サイズへの影響は？
A. 22 ファイル合計で約 300〜600 KB（Opus 圧縮で非常に小さい）。現在の `xiaozhi.bin` は約 2.8 MB、merged-binary は 9.9 MB。音声比率は全体の 3〜6%。

### Q5. カスタム音声追加で OTA が増えるか？
A. はい。音声は `xiaozhi.bin`（app パーティション）に埋込まれるので、OTA 配信量に直接加算される。差し替えるだけなら増えないが、追加する場合は Flash 容量制限（app パーティション 4 MB）に注意。

---

## 📚 関連ドキュメント

- [../asset-spec.md](../asset-spec.md) — アセット仕様計画書（Phase 0-A の枠組み）
- [../../assets/sounds/README.md](../../assets/sounds/README.md) — カスタム音声制作仕様書
- [../build-plan.md](../build-plan.md) § Phase 1-C — カスタム起動音組込計画
- [../operations/wake-word-selection.md](wake-word-selection.md) — ウェイクワード関連（音声処理の入力側）
- [../Review/action-items.md](../Review/action-items.md) § B-4 — `inject_assets.py` 実装待ち

## 🔗 外部参照

- OGG/Opus 仕様: https://opus-codec.org/
- ffmpeg loudnorm フィルタ: https://ffmpeg.org/ffmpeg-filters.html#loudnorm
- ESP-IDF EMBED_FILES: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/build-system.html#embedding-binary-data

---

## 改訂履歴

| 日付 | バージョン | 内容 | 作成者 |
|---|---|---|---|
| 2026-04-18 | 1.0 | 初版。Phase 0-C 段階での実機ビルド時の音声調査結果をまとめた | xxc@ctoch.jp |
