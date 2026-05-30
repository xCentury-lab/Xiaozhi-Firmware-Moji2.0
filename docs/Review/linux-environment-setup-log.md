---
title: Linux 実機セットアップログ (Ubuntu 22.04.5)
---

# Linux 実機セットアップログ (Ubuntu 22.04.5)

> **実施日**: 2026-04-18
> **実施ホスト**: HP EliteBook 830 G5 / Ubuntu 22.04.5 LTS / Linux 6.8.0-107-generic
> **目的**: `scripts/setup-ubuntu.sh` 相当の環境構築を実行し、ビルドが通ることを検証。発見された問題・解決策を本家計画書とドキュメントに反映する。

---

## 1. 実施結果サマリ

| 項目 | 結果 |
|---|---|
| `scripts/setup-ubuntu.sh` 相当の環境構築 | ✅ 完了 |
| `scripts/check-env.sh` | ✅ PASS 21 / FAIL 0 / WARN 1（USB 未接続のみ） |
| ベースラインビルド（Waveshare 1.85C） | ✅ 完了（`merged-binary.bin` 9.6MB、`releases/*.zip` 生成） |
| 実機書込＆起動動作 | ✅ 完了（V1.0 設定で Wi-Fi 接続、OTA 疎通、MQTT 接続、ウェイクワード検出、AI応答まで疎通確認） |
| 発見された計画書・ドキュメントの問題 | 🟠 7件（本書「3. 発見事項」参照） |

## 2. 実際にインストールされたバージョン

| コンポーネント | バージョン | 備考 |
|---|---|---|
| OS | Ubuntu 22.04.5 LTS | jammy、kernel 6.8.0 (HWE) |
| git | 2.34.1 | apt 標準 |
| Python | 3.10.12 | apt 標準（ESP-IDF v5.5 最小要件 3.9 を満たす） |
| CMake | 3.22.1 | apt 標準 |
| Ninja | 1.10.1 | apt 標準 |
| ESP-IDF | **v5.5.4** | xiaozhi v2.2.4 の `idf >=5.5.2` 要件に合わせて採用 |
| xtensa-esp-elf | esp-14.2.0_20260121 | ESP-IDF 同梱 |
| riscv32-esp-elf | esp-14.2.0_20260121 | ESP-IDF 同梱 |
| xtensa-esp-elf-gdb | 16.3_20250913 | ESP-IDF 同梱 |
| openocd-esp32 | v0.12.0-esp32-20251215 | ESP-IDF 同梱 |
| Python env | idf5.5_py3.10_env | ~/.espressif/python_env/ 配下 |
| xiaozhi-esp32 | **v2.2.4** | tag `v2.2.4` checkout |

## 3. 発見事項（計画書との差分）

### 3-1. ESP-IDF v5.4.x では xiaozhi-esp32 v2.2.4 はビルドできない 🔴 **致命的**

**現象**: `idf.py set-target esp32s3` 実行時に次のエラーで失敗:

```
Because project depends on idf (>=5.5.2) which doesn't match any
versions, version solving failed.
```

**原因**: `xiaozhi-esp32/main/idf_component.yml` に下記が記述されている:

```yaml
dependencies:
  idf:
    version: '>=5.5.2'
```

**影響**: 計画書・セットアップスクリプト・README ほぼ全ての v5.4.x 記述が誤り。

**対応**:

- `scripts/setup-ubuntu.sh` の `ESP_IDF_VERSION` を v5.5.4 へ変更（修正済み）
- `docs/setup/windows.md` / `docs/setup/linux.md` / `README.md` / `docs/build-plan.md` / `build/matrix.yaml` の v5.4.x 参照を v5.5.x に訂正（修正済み）
- `docs/Review/linux-build-compatibility.md` の冒頭に更新警告を追記（修正済み）

  ※ 旧ファイル名: `SETUP.md`, `SETUP-linux.md`（2026-04-18 時点で `docs/` 配下に統合移動）

### 3-2. `en-US` / `ja-JP` ロケールは本家 v2.2.4 に既に全て存在 🟢 **朗報**

`main/assets/locales/` 配下には **39 ロケール** が同梱されている:

```
ar-SA bg-BG ca-ES cs-CZ da-DK de-DE el-GR en-US es-ES fa-IR fi-FI
fil-PH fr-FR he-IL hi-IN hr-HR hu-HU id-ID it-IT ja-JP ko-KR ms-MY
nb-NO nl-NL pl-PL pt-PT ro-RO ru-RU sk-SK sl-SI sr-RS sv-SE th-TH
tr-TR uk-UA vi-VN zh-CN zh-TW
```

各ロケールは以下を含む:

- `language.json` — UI 文字列（58行・3言語で完全対応済み）
- `0.ogg`〜`9.ogg` — 数字音声
- `activation.ogg` / `welcome.ogg` / `wificonfig.ogg` / `err_pin.ogg` / `err_reg.ogg` / `upgrade.ogg` — 固定音声

`main/Kconfig.projbuild` にも `LANGUAGE_EN_US` / `LANGUAGE_JA_JP` が定義済みで、`menuconfig` で選択可能。

**プロジェクト計画への影響**:

- `docs/build-plan.md` の「en-US アセット存在確認」「ja-JP アセット存在確認」（Phase 0-A 最優先項目）→ **両方 ✅ で解決済み**
- STEP 2 の「日本語アセット制作（ja-JP新規）」工数 2〜3日の想定 → 本家翻訳を採用するなら **0日**（用語統一グロッサリー照合のみ）
- `docs/translation-source.md` の DeepL 下訳〜翻訳会社活用 → 本家翻訳をベースに社内用語統一のみに縮小可能

ただし、本家翻訳が OEM 向けに最適化されているかは別途内容レビュー必須（特に `HELLO_MY_FRIEND: こんにちは、友達！` など、B2B 文脈で要検討）。

### 3-3. `scripts/check-env.sh` 必須コマンドに `curl` あり、手動手順に漏れ 🟡 **軽微**

`scripts/check-env.sh` L40 は `curl` を必須コマンドとして検査するが、`docs/setup/linux.md`（旧 SETUP-linux.md）および `docs/build-plan.md` の apt install 例には `curl` が含まれていなかった。

**対応**: `docs/setup/linux.md` / `docs/build-plan.md` / `README.md` の apt install リストに `curl` を追加（修正済み）。

### 3-4. 新シェルで `check-env.sh` を走らせると `idf.py` が FAIL になる 🟡 **UX**

`bash scripts/check-env.sh` は子シェルを起動するため、親シェルで `get_idf` を実行していないと `idf.py が見つかりません` と FAIL する。これは自然な挙動だが、ユーザーが混乱する。

**対応**: `docs/setup/linux.md` のクイックセットアップ案内に `source ~/.bashrc && get_idf` を明記（修正済み）。

### 3-4-2. Jarvis ウェイクワードは日本語話者では検出困難 🟡 **量産設計影響**

2026-04-18 実機検証（日本語ネイティブ話者）で判明:

- ✅ **Hi, ESP**（wn9_hiesp）: 検出成功
- ❌ **Jarvis**（wn9_jarvis_tts）: 複数回試行で検出失敗

原因: `wn9_jarvis_tts` モデルは英語ネイティブ TTS 音声で学習されたため、日本語話者の発音「ジャービス」（3 音節・母音強め）では AFE の検出閾値（0.627/0.632）を下回る。

**プロジェクト計画への影響**:
- 日本語版 OEM の推奨ウェイクワード組合せを **`Hi, ESP` + `Alexa`** に変更（`Alexa` は日本での認知度が高く、日本語話者の発音適性も良好）
- 英語版は `Jarvis + Hi, ESP` のまま維持（ネイティブ話者向け）
- 詳細と切替手順は [../operations/wake-word-selection.md](../operations/wake-word-selection.md) 参照

### 3-5. Waveshare 1.85C には V1.0 / V2.0 の 2 リビジョンあり 🔴 **実機ハマりポイント**

本家の `main/boards/waveshare/esp32-s3-touch-lcd-1.85c/esp32-s3-touch-lcd-1.85c.cc` は `#ifdef CONFIG_VERSION_1_0` と `#ifdef CONFIG_VERSION_2_0` の二択で、**Kconfig のデフォルトは V2.0**:

```
choice
    prompt "ESP32S3_TOUCH_LCD_1_85C version"
    default VERSION_2_0
    config VERSION_1_0 bool "version 1.0"
    config VERSION_2_0 bool "version 2.0"
endchoice
```

| リビジョン | オーディオ構成 | I2C ES8311 |
|---|---|---|
| V1.0 | `NoAudioCodecSimplex`（I2S 単純 mic + スピーカー） | なし |
| V2.0（default） | `BoxAudioCodec`（ES8311 + ES7210 via I2C 0x30） | あり |

**2026-04-18 実機（xxc 所持）は V1.0**。デフォルト（V2.0）でビルドして書込むと:
```
W i2c.master: Please check pull-up resistances...
E (1289) ES8311: Open fail
assert failed: BoxAudioCodec(...) box_audio_codec.cc:51
Rebooting...（LCD が点灯するがちかちかする無限ループ）
```

`menuconfig` または sdkconfig で `CONFIG_VERSION_1_0=y` に切替→再ビルド→再書込で正常動作。

**プロジェクト計画への影響**:
- `build/matrix.yaml` の 1.85c 定義に **V1.0 / V2.0 をバリアントとして分けるべき**（または出荷前に実機選別）
- Waveshare に V1.0 と V2.0 の見分け方を確認必要（基板シルク、チップ目視、I2C スキャンなど）
- STEP 1-F（Waveshare 全ボード展開）時は他ボードも同様のリビジョン問題がないか調査
- 出荷検査フロー（build-plan.md § Phase 1-E / § shipping-workflow）に **「実機リビジョン確認→対応 bin 書込」** を追加

### 3-6. `matrix.yaml` の `idf_version` が実インストール版と不整合 🟡 **整合性**

`build/matrix.yaml` L10 が `v5.4.1` と記述されていたが、setup スクリプトは v5.4.2 をインストールする設定だった（v5.5.x 必須が発覚する前から既に不整合）。

**対応**: `build/matrix.yaml` を `v5.5.4` へ更新し、コメントで「`idf >=5.5.2` 要件」を明記（修正済み）。

## 4. 所要時間実測値

| 段階 | 所要 | 備考 |
|---|---|---|
| apt install（14パッケージ） | 約 2〜3 分 | ネット依存、初回のみ |
| `git clone --recursive` (ESP-IDF v5.4.2 → v5.5.4) | 約 9〜10 分 | 最終 3.3GB、Bluetooth/OpenThread/wifi-lib がボトルネック |
| `./install.sh esp32s3` (v5.4.2) | 約 5 分 | 最終 ~3.7GB |
| v5.4.2 → v5.5.4 の submodule diff 更新 | 約 1 分 | 差分のみ |
| `./install.sh esp32s3` (v5.5.4) | 約 6〜7 分 | 新バージョンのツールチェーンを追加ダウンロード、合計 ~7.5GB |
| xiaozhi-esp32 の clone + v2.2.4 checkout | 約 1 分 | submodule なし（本家は .gitmodules 未使用） |
| Python venv + pyyaml | 数秒 | pip 済み環境 |
| check-env.sh 実行 | 即時 | - |
| **合計** | 約 25〜30 分 | - |

## 5. 実行コマンド履歴（再現手順）

```bash
# 1. apt パッケージ
sudo apt-get update
sudo apt-get install -y \
    git wget curl flex bison gperf \
    python3 python3-pip python3-venv \
    cmake ninja-build ccache \
    libffi-dev libssl-dev \
    dfu-util libusb-1.0-0

# 2. brltty（USB シリアル横取り対策 / Ubuntu 22.04 のみ）
dpkg -l brltty &>/dev/null && sudo apt remove -y brltty || true

# 3. dialout グループへの追加
sudo usermod -a -G dialout $USER    # 新ログインで反映、または `newgrp dialout`

# 4. ESP-IDF v5.5.4 のクローン・サブモジュール・インストール
mkdir -p ~/esp && cd ~/esp
git clone -b v5.5.4 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32s3
source export.sh

# 5. 本家 xiaozhi-esp32 v2.2.4
mkdir -p ~/xiaozhi-work && cd ~/xiaozhi-work
git clone https://github.com/78/xiaozhi-esp32.git
cd xiaozhi-esp32
git checkout v2.2.4
git submodule update --init --recursive   # v2.2.4 は submodule なし

# 6. 本プロジェクトの Python 依存
cd /home/xxc/project/Xiaozhi-Firmware-VoCat
pip install -r requirements.txt

# 7. .bashrc に環境変数
cat >> ~/.bashrc <<'EOF'

# ESP-IDF 環境有効化エイリアス
alias get_idf='source $HOME/esp/esp-idf/export.sh'

# 本家 xiaozhi-esp32 リポジトリパス
export XIAOZHI_SRC=$HOME/xiaozhi-work/xiaozhi-esp32

# Xiaozhi-Firmware-update プロジェクトパス
export XIAOZHI_FW=$HOME/project/Xiaozhi-Firmware-VoCat
EOF

# 8. 環境検証（新シェル推奨）
source ~/.bashrc
get_idf
bash $XIAOZHI_FW/scripts/check-env.sh

# 9. ベースラインビルド
cd $XIAOZHI_SRC
python scripts/release.py waveshare/esp32-s3-touch-lcd-1.85c   # 初期設定＋ビルド
# or: idf.py set-target esp32s3 && idf.py build
```

## 6. 今後の TODO

- [x] v5.4.x → v5.5.x への全ドキュメント修正
- [x] curl 追加
- [x] check-env.sh の使い方を `docs/setup/linux.md` に明記
- [ ] 本家 ja-JP 翻訳が OEM 用途で使えるか文言レビュー（営業・サポート確認）
- [ ] Phase 0-A の「en-US / ja-JP 有無確認」完了マーク（build-plan.md § 5-1）
- [ ] 実機（Waveshare 1.85C）での焼込動作試験

## 7. ディスク占有状況（参考）

セットアップ完了時点:

| ディレクトリ | サイズ | 用途 |
|---|---|---|
| `~/esp/esp-idf/` | 3.3 GB | ESP-IDF 本体 + submodule |
| `~/.espressif/` | 7.5 GB | ツールチェーン + Python venv（v5.4.x と v5.5.x が併存） |
| `~/xiaozhi-work/xiaozhi-esp32/` | 約 1 GB | 本家ソース + managed_components |
| **合計** | **約 12 GB** | - |

不要な v5.4.x のツールチェーンを削除する場合:

```bash
source ~/esp/esp-idf/export.sh
python ~/esp/esp-idf/tools/idf_tools.py uninstall --dry-run   # 実削除前に確認
python ~/esp/esp-idf/tools/idf_tools.py uninstall              # 実削除
```

---

*本書は実機セットアップ時に発見された知見を記録したもの。以降の新規環境構築者が同じ手戻りを避けるため参照すること。*
