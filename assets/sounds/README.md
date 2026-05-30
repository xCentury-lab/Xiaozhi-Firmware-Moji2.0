# assets/sounds/

**言語別** の音声マスタを管理します (ja-JP の発音修正用)。

> **2026-05-24 構造簡素化**: 旧「ボード別カスタム起動音」軸を廃止し、`{board}/{brand}/` 層と `master/` (raw WAV) 層を削除。`locales/{lang}/` のみ運用する単純な構造に変更。

## ディレクトリ構成

```
assets/sounds/
└── locales/                        # ★ 言語別音声マスタ (upstream 互換、ビルドで EMBED)
    └── ja-JP/                      # 日本語ロケール (20 ファイル、2026-05-24 整備)
        ├── README.md
        ├── 0.ogg 〜 9.ogg          # 数字読み上げ
        ├── activation.ogg
        ├── err_pin.ogg / err_reg.ogg
        ├── upgrade.ogg
        ├── welcome.ogg
        ├── wificonfig.ogg
        ├── language.json           # UI 文字列定義
        ├── *.ogg.bak               # 過去版 (参考)
        └── soniox-tts-*.wav        # TTS 元 WAV (参考)
```

### 役割

| 層 | 役割 | 状況 |
|---|---|---|
| **`locales/{lang}/`** | upstream xiaozhi-esp32 互換、ビルド時に `main/assets/locales/{lang}/` へコピーして EMBED_FILES で焼込み | ✅ ja-JP 整備済 (2026-05-24) |

### 適用範囲
- **ja-JP のみ**: 本家 ja-JP 音声には発音誤りがあるため自家整備
- **en-US 等**: 本家音声をそのまま使用 (差替不要、本ディレクトリに配置しない)

## フォーマット要件

| 項目 | 要件 |
|---|---|
| サンプルレート | 16 kHz（音声認識と統一） |
| ビット深度 | 16 bit PCM |
| チャンネル | Mono |
| コーデック | WAV（非圧縮）または Opus（圧縮） |
| 音量 | -14 LUFS に統一（全ボード・全音声） |
| 長さ | 起動音 2秒以内、効果音 1秒以内 |

## 変換・正規化コマンド

```powershell
# サンプルレート統一（16kHz Mono）
ffmpeg -i master/boot-chime.wav -ar 16000 -ac 1 -sample_fmt s16 boot-chime-16k.wav

# 音量正規化（-14 LUFS）
ffmpeg -i boot-chime-16k.wav -af loudnorm=I=-14:TP=-1:LRA=11 boot-chime-16k-norm.wav

# Opus圧縮（任意、Flash容量対策）
ffmpeg -i boot-chime-16k.wav -c:a libopus -b:a 32k boot-chime-16k.opus
```

## 組込方式

ボード実装に応じて以下から選択:

1. **C配列（xxd）**: 短い効果音向け、Flash効率良
2. **SPIFFS/LittleFS**: 複数ファイル・長め音声向け
3. **Kconfig `SOUND_SET` 切替**: 量産向け（推奨）

## 著作権上の注意

- マスター音声は**ロイヤリティフリー素材または自社独自制作**のみ使用
- 購入ライセンス素材の場合、ライセンス書面を `docs/licenses/` に保管
- 日本語音声を人間の声優で制作する場合、権利譲渡契約を明示

## マスターファイルについて

`.gitignore` で `assets/sounds/master/*.wav` 等は除外されています。
マスターファイルは社内ファイルサーバの以下パスで管理してください:

- `\\fileserver\xiaozhi-assets\sounds\master\`

リポジトリには**変換済み（ボード最適化済み）**の小容量ファイルのみコミットします。
