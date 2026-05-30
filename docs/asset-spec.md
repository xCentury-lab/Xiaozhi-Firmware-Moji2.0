# アセット仕様書（ロゴ・起動音）

> **ステータス**: 🟡 一部確定（音声セクションは [operations/audio-assets.md](operations/audio-assets.md) で実地確認完了）
> **対象**: Waveshare ESP32-S3-Touch-LCD-1.85C を最初のリファレンス

> 💡 **音声アセットに関する実地調査結果は [operations/audio-assets.md](operations/audio-assets.md) に分離**しました。本書はロゴ・翻訳・フォント仕様の計画書として継続運用します。

---

## 1. ロゴ仕様

### 1-1. 対象ボードと表示領域

| ボード | 画面サイズ | 形状 | 起動ロゴ表示領域 |
|---|---|---|---|
| waveshare-esp32-s3-touch-lcd-1.85c | 360×360 | 円形（AMOLED） | 中央 80% |
| waveshare-esp32-c6-touch-amoled-1.8 | 368×448 | 矩形 | TBD |
| waveshare-esp32-p4-wifi6-touch-lcd-10.1 | 1280×800 | 矩形 | TBD |

### 1-2. ファイル形式

| 項目 | 要件 |
|---|---|
| マスター形式 | SVG（ベクター） |
| 書出し形式 | PNG（可逆圧縮）→ LVGL C配列 |
| カラーフォーマット | RGB565（1.85C）／ RGB888（P4）※ 要確認 |
| 透過 | 要件未確定（Phase 0-A で確認） |

### 1-3. ソース組込方式

- [ ] 方式確定: C配列 / SPIFFS / Kconfig `LOGO_SET`

---

## 2. 起動音仕様

### 2-1. オーディオパラメータ

| 項目 | 値（想定） |
|---|---|
| サンプルレート | 16 kHz |
| ビット深度 | 16 bit PCM |
| チャンネル | Mono |
| コーデック | WAV または Opus |
| 音量 | -14 LUFS |

### 2-2. ボード別 I2S 仕様（要確認）

| ボード | DAC | スピーカー出力 | 備考 |
|---|---|---|---|
| waveshare-esp32-s3-touch-lcd-1.85c | TBD | TBD | — |

### 2-3. 再生トリガー

- 電源ON時（boot-chime）
- ウェイクワード検出（wake-ding）
- Wi-Fi接続完了（connect-ok）
- エラー時（error-buzz）

### 2-4. ソース組込方式

- [x] 方式確定: **CMake `EMBED_FILES`**（app バイナリに直接埋込、Kconfig `CONFIG_LANGUAGE_XX_YY` で言語別ディレクトリを切替）
- [x] 言語非依存の共通音声は `main/assets/common/` 配下で一括埋込
- [x] シンボルは自動生成の `main/assets/lang_config.h` で `Lang::Sounds::OGG_*` として参照

詳細: [operations/audio-assets.md](operations/audio-assets.md) § 3 参照

---

## 3. 翻訳アセット仕様

### 3-1. 本家のアセット構造（Phase 0-A で確認）

- [ ] `main/assets/en-US/` の有無
- [ ] `main/assets/ja-JP/` の有無
- [ ] 文字列ファイル形式（`.po` / `.json` / `.h`）

### 3-2. 日本語フォント

| 候補 | ライセンス | ファイルサイズ |
|---|---|---|
| Noto Sans JP | OFL | フル 4MB / サブセット ~1MB |
| Source Han Sans JP | OFL | フル 4.8MB / サブセット ~1.2MB |

サブセット化手順:

```powershell
pyftsubset NotoSansJP-Regular.ttf `
    --unicodes="U+0020-007E,U+3000-30FF,U+4E00-9FFF" `
    --output-file=noto-sans-jp-subset.ttf
```

---

## 4. Phase 0-A チェックリスト

本仕様書を完成させるため、以下を実地で確認してください。

- [x] `main/Kconfig.projbuild` の LANGUAGE / OTA URL のキー名（詳細: [operations/audio-assets.md § 4](operations/audio-assets.md) / [operations/wake-word-selection.md](operations/wake-word-selection.md)）
- [x] `main/assets/` 配下のディレクトリ構造（詳細: [operations/audio-assets.md § 1](operations/audio-assets.md)）
- [ ] 起動ロゴのソース位置とフォーマット
- [x] 起動音のソース位置とフォーマット（詳細: [operations/audio-assets.md](operations/audio-assets.md)）
- [ ] 1.85C の画面解像度とカラー深度の確定値
- [ ] 1.85C の I2S / DAC / スピーカー構成
