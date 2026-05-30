# assets/sounds/locales/ja-JP/

> **日本語ロケール音声アセット (マスタ)**
> ファームウェアビルド時に `EMBED_FILES` で app バイナリに焼込まれる正規 .ogg 群。

---

## 📌 役割

このディレクトリはファームウェアビルド時の **音声マスタ** として機能する。
upstream `78/xiaozhi-esp32/main/assets/locales/ja-JP/` と同じディレクトリ構造・ファイル名を採用し、
ビルド時に上書きコピー（or symlink）して埋込音声を制御する。

## 📁 ファイル一覧（2026-05-24 時点）

### 正規 .ogg（ビルドで埋込まれる）

| ファイル | 用途 | 長さ | SHA256 (16c) | spec |
|---|---|---|---|---|
| `0.ogg` 〜 `9.ogg` | 数字読み上げ (アクティベーションコード等) | 0.83〜1.12s | b986e72a... 等 | 16k/Mono/Opus |
| `activation.ogg` | アクティベーション画面遷移時 | 6.81s | 38b7f1b8daa85170 | 16k/Mono/Opus |
| `err_pin.ogg` | SIM カード未挿入エラー | 2.57s | 03e2af375fe73005 | 16k/Mono/Opus |
| `err_reg.ogg` | ネットワーク登録失敗 | 5.89s | 8da287affd5c8ff5 | 16k/Mono/Opus |
| `upgrade.ogg` | OTA アップグレード中の案内 | 2.74s | 9208ccb4fe277e85 | 16k/Mono/Opus |
| `welcome.ogg` | 初期状態起動挨拶 | 2.09s | 24c01749cf0351a3 | 16k/Mono/Opus |
| `wificonfig.ogg` | Wi-Fi 設定モード案内 | 1.88s | 7a7ae8d3b8106fed | 16k/Mono/Opus |

### UI 文字列

| ファイル | 用途 |
|---|---|
| `language.json` | UI 文字列定義（音声ではない、upstream 同梱） |

### 過去版・参考素材（ビルドに含まれない）

| ファイル | 種別 |
|---|---|
| `wificonfig.ogg.bak` | wificonfig.ogg の旧版 (3.93s) |
| `wificonfig_48k_broken.ogg.bak` | 過去事故版 (48kHz encode で壊れた、教訓として保持) |
| `soniox-tts-2026-05-02T06-01-20-837Z.wav` | Soniox TTS で生成した元音声 (44.1kHz WAV) |

## 🔧 仕様要件

全 .ogg は以下を満たすこと:

- **サンプルレート (input)**: **16 kHz** (`-ar 16000`)
- **チャンネル**: **Mono** (`-ac 1`)
- **コーデック**: **Opus / OGG コンテナ** (`-c:a libopus`)
- **音量**: **-14 LUFS** (`-af "loudnorm=I=-14:TP=-1:LRA=11"`)
- **長さ**: 起動音 2 秒以内、案内音声 5 秒以内推奨
- **ファイルサイズ**: < 50 KB

⚠️ **`-ar 48000` は厳禁** — `wificonfig_48k_broken.ogg.bak` 事故の再現になる。

### 標準 encode コマンド

```bash
ffmpeg -i source.wav \
       -ar 16000 -ac 1 \
       -af "loudnorm=I=-14:TP=-1:LRA=11" \
       -c:a libopus -b:a 32k \
       output.ogg
```

## 🏗 ビルド時の取扱

このディレクトリは現状 **手動で本家ソースにコピー** する方式（方式 A）で運用:

```bash
cp -p assets/sounds/locales/ja-JP/*.ogg \
      ~/xiaozhi-work/xiaozhi-esp32/main/assets/locales/ja-JP/
```

将来 [build/inject_assets.py](../../../build/inject_assets.py) (Phase 1-C / action-items B-4) が完成すれば、
このディレクトリから自動注入される。

## 📚 関連ドキュメント

- [../../../docs/operations/audio-assets.md](../../../docs/operations/audio-assets.md) — 音声アセット所在マップ・EMBED_FILES 仕様
- [../../../docs/plans/replace-wificonfig-ogg-ja-JP-2026-05-24.md](../../../docs/plans/replace-wificonfig-ogg-ja-JP-2026-05-24.md) — 当該音声群を反映した再ビルドプラン
- [../README.md](../README.md) — assets/sounds/ 全体構造

## 📝 履歴

- 2026-05-24: `OpenAI-Realtime-LAB/Xiaozhi-Firmware-update/assets/sounds/locales/ja-JP/` から 20 ファイル全コピー。本プロジェクト内で自己完結化。
