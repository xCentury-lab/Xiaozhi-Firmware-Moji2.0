# ウェイクワード選定ガイド

> **対象**: Waveshare ESP32-S3 系ボードへの Xiaozhi ファームウェアビルド
> **目的**: ウェイクワードの選定基準・組合せ推奨・実機検証結果の共有
> **最終更新**: 2026-04-18
> **ドキュメント目次**: [../README.md](../README.md)

---

## 🎯 推奨ウェイクワード組合せ（OEM 用途別）

Xiaozhi は **最大 2 個**のウェイクワードを同時有効化できます（[技術的制約の詳細](#-技術的制約最大-2-個)）。以下は用途別の推奨組合せです。

### 🇯🇵 日本語版 OEM 向け（B2C/B2B）

**✅ 推奨: `Hi, ESP` + `Alexa`**

| 理由 | 詳細 |
|---|---|
| **日本語話者の発音適性** | 両方とも日本人が英語っぽく発音しやすい。「ハイ・イー・エス・ピー」「アレクサ」は音節数が少なく、明瞭 |
| **一般認知度** | `Alexa` は日本でも Amazon スマートスピーカーで定着 |
| **実機検証済** | `Hi, ESP` は 2026-04-18 に日本語話者による動作確認済 |
| **冗長性** | 1 つが反応しない環境でも他方で代替可能 |

### 🌍 英語圏 OEM 向け（展示会・海外）

**✅ 推奨: `Jarvis` + `Hi, ESP`**

| 理由 | 詳細 |
|---|---|
| **ブランディング** | `Jarvis` は Iron Man の印象で技術デモに好適 |
| **ネイティブ対応** | 英語ネイティブ話者なら両方とも高精度 |
| **現行実装**（2026-04-18 時点の量産候補ファーム）| `v2.2.4_waveshare-1.85c_V1.0_en-US_jarvis-hiesp_*` で実装 |

### 🏢 ブランド差別化優先

**✅ 推奨: カスタムウェイクワード + `Hi, ESP`**（バックアップ）

- Espressif にカスタムモデル発注（「Hey xCentury」など）
- 費用: 数万〜数十万円/語、納期 1〜2 週間
- `Hi, ESP` をバックアップに残すことで、カスタムモデル未完成の端末でも最低限動作

### 👨‍💻 開発・デバッグ用途

**推奨: `Hi, ESP` + `你好小智`**（wn9_nihaoxiaozhi_tts）

- `你好小智` は本家モデルで検出精度が最も安定
- 中国語読みに抵抗がない開発者向け

---

## 🔬 実機検証結果（2026-04-18）

### 検証環境
- **ボード**: Waveshare ESP32-S3-Touch-LCD-1.85C（V1.0）
- **ファームウェア**: `xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_20260418.bin`
- **有効化ウェイクワード**: `wn9_jarvis_tts` + `wn9_hiesp`
- **話者**: 日本語ネイティブ
- **環境**: オフィス室内、マイク至近距離

### 結果

| ウェイクワード | 検出成否 | 備考 |
|---|---|---|
| **Hi, ESP**（ハイ・イー・エス・ピー） | ✅ 成功 | 1 回で検出 |
| **Jarvis**（ジャービス） | ❌ 失敗 | 複数回試行しても検出せず |

### 🕵️ Jarvis 失敗の原因分析

`wn9_jarvis_tts` は Espressif 公式の TTS（Text-to-Speech）合成音声で学習されたモデル。学習データはネイティブ英語（主に米語）の TTS 音声が中心。

日本語話者の発音上の差異:

| 要素 | ネイティブ英語 | 日本語話者（典型） |
|---|---|---|
| **音節数** | 2 音節 `Jar-vis` | 3 音節 `ジャー・ビ・ス` |
| **子音 /dʒ/** | 破擦音（舌先を硬口蓋に付け、一気に離す） | 軽い「ジ」音 |
| **母音 /ɑː/** | 開いた後舌母音 | 日本語の「ア」 |
| **語尾 /ɪs/** | 短母音 + 無声歯擦音 | 「ビス」と母音挿入 |
| **R 音** | retroflex /r/ | なし |

結果として、日本語話者の「ジャービス」は AFE Pipeline の閾値（wakenet9l 設定値: 0.627/0.632）を下回り、検出失敗。

### 💡 回避策

1. **発音トレーニング**: "Jarvis" を英語ネイティブ風（「ヂャーヴs」）で発音 — 一部成功するが量産 OEM 向けには現実的でない
2. **別ウェイクワードへ切替**: 本ドキュメントの[推奨組合せ](#-推奨ウェイクワード組合せoem-用途別)参照（**本命**）
3. **カスタムモデル発注**: Espressif に日本語話者サンプルベースの再学習を依頼

---

## 🛠 技術的制約（最大 2 個）

Xiaozhi ファームウェア（`main/audio/wake_words/afe_wake_word.cc`）は ESP-SR の AFE（Audio Front-End）を使用。AFE の設定構造体は以下のスロットのみ定義:

```c
// managed_components/espressif__esp-sr/include/esp32s3/esp_afe_config.h
char *wakenet_model_name;    // プライマリウェイクワード
char *wakenet_model_name_2;  // セカンダリウェイクワード
```

Kconfig で 3 個以上選択しても、自動で先頭 2 個のみ採用されます。3 個以上にはコード改修（`afe_add_wakenet_model` API 呼出）が必要ですが、CPU 負荷増加・誤検出率上昇のため**非推奨**。

### リソースコスト（ウェイクワード 1 個あたり追加）

| 項目 | 増加量 |
|---|---|
| Flash サイズ | 約 50〜150 KB（モデルによる） |
| PSRAM | 約 100〜300 KB |
| CPU 負荷 | +5〜15% |
| 誤検出率 | モデル数に比例して上昇 |

---

## 📋 ウェイクワード切替手順

### 手順 1: 現在の設定を確認

```bash
cd $XIAOZHI_SRC
grep -E "^CONFIG_SR_WN_WN9" sdkconfig
```

例（Jarvis + Hi,ESP 有効）:
```
CONFIG_SR_WN_WN9_HIESP=y
CONFIG_SR_WN_WN9_JARVIS_TTS=y
```

### 手順 2: sdkconfig を編集

#### 方法 A: `idf.py menuconfig` で GUI 編集（推奨）

```bash
cd $XIAOZHI_SRC && get_idf
idf.py menuconfig
# → Component config → ESP Speech Recognition → Load Multiple Wake Words
# → スペースキーで選択/解除、S で保存、Q で終了
```

#### 方法 B: `sed` でコマンド一発切替（Hi,ESP + Alexa の例）

```bash
cd $XIAOZHI_SRC
# Jarvis を無効化
sed -i 's/^CONFIG_SR_WN_WN9_JARVIS_TTS=y$/# CONFIG_SR_WN_WN9_JARVIS_TTS is not set/' sdkconfig
# Alexa を有効化
sed -i 's/^# CONFIG_SR_WN_WN9_ALEXA is not set$/CONFIG_SR_WN_WN9_ALEXA=y/' sdkconfig
# 確認
grep -E "^CONFIG_SR_WN_WN9" sdkconfig
```

期待する出力:
```
CONFIG_SR_WN_WN9_HIESP=y
CONFIG_SR_WN_WN9_ALEXA=y
```

### 手順 3: リビルド + 再書込

```bash
get_idf
cd $XIAOZHI_SRC
idf.py build                                  # 約 7〜10 分
python -m esptool --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    write_flash 0x0 build/merged-binary.bin
```

> **注**: `idf.py build` は `merged-binary.bin` を自動再生成しません。`python -m esptool merge_bin` で手動合成するか、個別 partition 書込（[flash-guide.md § 方法1](flash-guide.md#-方法-1-シェル-1-行で書込推奨失敗が少ない)）を使ってください。

### 手順 4: 起動ログで有効化確認

書込後、シリアルログで以下を探す:

```
I (xxxx) AfeWakeWord: Model 0: wn9_hiesp
I (xxxx) AfeWakeWord: Model 1: wn9_alexa
I (xxxx) AFE_CONFIG: Set WakeNet Model: wn9_hiesp
I (xxxx) AFE_CONFIG: Set Second WakeNet Model: wn9_alexa
I (xxxx) AFE: AFE Pipeline: [input] -> |VAD(WebRTC)| -> |WakeNet(wn9_hiesp,wn9_alexa)| -> [output]
```

両方のモデルがロードされていれば成功。

---

## 📚 プリビルド済みウェイクワード完全リスト

ESP-SR v2.x 同梱の Wakenet モデル。Kconfig シンボルで選択。

### 🇬🇧 英語系（TTS 学習モデル）

| ウェイクワード | Kconfig シンボル | 日本語話者適性 |
|---|---|---|
| Alexa | `CONFIG_SR_WN_WN9_ALEXA` | ◎ |
| Computer | `CONFIG_SR_WN_WN9_COMPUTER_TTS` | ◎ |
| Jarvis | `CONFIG_SR_WN_WN9_JARVIS_TTS` | ❌ |
| Mycroft | `CONFIG_SR_WN_WN9_MYCROFT_TTS` | ○ |
| Sophia | `CONFIG_SR_WN_WN9_SOPHIA_TTS` | ○ |
| Hi, ESP | `CONFIG_SR_WN_WN9_HIESP` | ✅ |
| Hey Willow | `CONFIG_SR_WN_WN9_HEYWILLOW_TTS` | △ |
| Hey Wanda | `CONFIG_SR_WN_WN9_HEYWANDA_TTS` | △ |
| Hey Kira | `CONFIG_SR_WN_WN9_HEYKIRA_TTS3` | ○ |
| Hey Ivy | `CONFIG_SR_WN_WN9_HEYIVY_TTS2` | △ |
| Hey Ily | `CONFIG_SR_WN_WN9_HEYILY_TTS2` | △ |
| Hey Printer | `CONFIG_SR_WN_WN9_HEYPRINTER_TTS` | △ |
| Hi, Andy | `CONFIG_SR_WN_WN9_HIANDY_TTS2` | ○ |
| Hi, Fairy | `CONFIG_SR_WN_WN9_HIFAIRY_TTS2` | ○ |
| Hi, Jason | `CONFIG_SR_WN_WN9_HIJASON_TTS2` | ○ |
| Hi, Jolly | `CONFIG_SR_WN_WN9_HIJOLLY_TTS2` | ○ |
| Hi, Joy | `CONFIG_SR_WN_WN9_HIJOY_TTS` | ○ |
| Hi, Lily | `CONFIG_SR_WN_WN9_HILILI_TTS` | ○ |
| Hi, M Five | `CONFIG_SR_WN_WN9_HIMFIVE` | ○ |
| Hi, Telly | `CONFIG_SR_WN_WN9_HITELLY_TTS` | ○ |
| Hi, Stack Chan | `CONFIG_SR_WN_WN9_HISTACKCHAN_TTS3` | ◎（日本発ロボット由来）|
| Hi, Wall-E | `CONFIG_SR_WN_WN9_HIWALLE_TTS2` | ○（ピクサー）|
| Blue Chip | `CONFIG_SR_WN_WN9_BLUECHIP_TTS2` | △ |
| Astrolabe | `CONFIG_SR_WN_WN9_ASTROLABE_TTS` | × |

**適性判定基準**:
- ◎: 日本語話者でも高精度検出可能と期待できる
- ○: 発音次第で通る
- △: 要発音注意
- ❌: 日本語話者では検出困難（実機確認済）
- ×: 発音が難しい

### 🇨🇳 中国語系

| ウェイクワード | Kconfig シンボル |
|---|---|
| 你好小智 | `CONFIG_SR_WN_WN9_NIHAOXIAOZHI_TTS` |
| 你好小智（大モデル） | `CONFIG_SR_WN_WN9L_NIHAOXIAOZHI_TTS3` |
| 你好小智（小モデル） | `CONFIG_SR_WN_WN9S_NIHAOXIAOZHI` |
| 小爱同学 | `CONFIG_SR_WN_WN9_XIAOAITONGXUE` / `_WN9L_XIAOAITONGXUE` |
| Hi, 乐鑫 | `CONFIG_SR_WN_WN9_HILEXIN` / `_WN9S_HILEXIN` |
| 小龙小龙 | `CONFIG_SR_WN_WN9_XIAOLONGXIAOLONG_TTS` |
| 小鸭小鸭 | `CONFIG_SR_WN_WN9_XIAOYAXIAOYA_TTS2` |
| 小宇同学 | `CONFIG_SR_WN_WN9_XIAOYUTONGXUE_TTS2` |
| …他多数（全 30+ 種類） | — |

全リストは以下で取得:
```bash
grep -oP 'config SR_WN_WN9\w+' $XIAOZHI_SRC/managed_components/espressif__esp-sr/Kconfig.* | sort -u
```

### 🇯🇵 日本語ウェイクワード

**プリビルド無し** — ESP-SR のカタログに日本語ネイティブウェイクワードは存在しません。

対応方針:
- **A**: 日本語話者でも通りやすい英語ウェイクワードで代替（本ガイドの推奨）
- **B**: Espressif にカスタムモデル発注（公式: https://www.espressif.com/en/products/software/esp-sr）

---

## 🔗 関連ドキュメント

- [flash-guide.md](flash-guide.md) — ビルド済ファームの書込手順
- [audio-assets.md](audio-assets.md) — 音声アセット全般（ウェイクワード検出後に再生される welcome/activation/err_* 等）
- [../build-plan.md](../build-plan.md) — プロジェクト計画書（STEP1/STEP2）
- [../Review/linux-environment-setup-log.md](../Review/linux-environment-setup-log.md) — 環境構築実測ログ
- [../Review/action-items.md](../Review/action-items.md) — アクションアイテム（D-11 にウェイクワード再選定を追記）

## 🔗 外部参照

- ESP-SR 公式ドキュメント: https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/wake_word_engine/index.html
- カスタムウェイクワード制作依頼: https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/wake_word_engine/ESP_Wake_Words_Customization.html

---

## 改訂履歴

| 日付 | バージョン | 内容 | 作成者 |
|---|---|---|---|
| 2026-04-18 | 1.0 | 初版。Jarvis 日本語話者検出失敗の実機確認結果を反映、日本語版推奨を `Hi,ESP + Alexa` に決定 | xxc@ctoch.jp |
