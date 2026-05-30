# Linux ビルド互換性調査報告

> **調査日**: 2026-04-18
> **対象 OS**: Ubuntu Desktop 22.04 LTS / Ubuntu Desktop 24.04 LTS
> **結論**: ✅ **両環境ともビルド可能** — ESP-IDF は Linux を公式一等サポート

> ⚠️ **更新事項 (2026-04-18 後日、実機検証時)**: 本書で言及している ESP-IDF v5.4.x は、xiaozhi-esp32 v2.2.4 の依存要件 `idf >=5.5.2` を満たさないため、本プロジェクトでは使用できません。実セットアップでは **v5.5.2 以上（推奨 v5.5.4）** を使ってください。本書の v5.4.x 記述は調査時点のスナップショットです。詳細は [../setup/linux.md](../setup/linux.md) および [linux-environment-setup-log.md](linux-environment-setup-log.md) 参照。

---

## 1. 結論サマリ

| 質問 | 回答 |
|---|---|
| ESP-IDF v5.4.x は Ubuntu で動くか？ | ✅ **YES** — 公式サポート |
| 78/xiaozhi-esp32 は Ubuntu でビルドできるか？ | ✅ **YES** — 標準 ESP-IDF プロジェクト、コミュニティ実績あり |
| Ubuntu 22.04 LTS は使えるか？ | ✅ **YES** — `brltty` 削除が必要な場合あり |
| Ubuntu 24.04 LTS は使えるか？ | ✅ **YES** — Python 周りの軽微な問題あり |
| 本プロジェクトのスクリプトに大改修は要るか？ | ⬜ **軽微** — PowerShell → Bash の差異のみ |
| 推奨 Ubuntu バージョン | **22.04 LTS**（より成熟・安定） |

---

## 2. ESP-IDF 公式 Linux サポート

Espressif 公式ドキュメントに [Linux / macOS セットアップガイド](https://docs.espressif.com/projects/esp-idf/en/v5.4/esp32/get-started/linux-macos-setup.html) が存在。

### 2-1. Ubuntu 必要パッケージ

```bash
sudo apt-get install git wget flex bison gperf python3 python3-pip \
  python3-venv cmake ninja-build ccache libffi-dev libssl-dev \
  dfu-util libusb-1.0-0
```

### 2-2. ESP-IDF インストール手順

```bash
# ESP-IDF クローン
git clone -b v5.4.2 --recursive https://github.com/espressif/esp-idf.git ~/esp/esp-idf
cd ~/esp/esp-idf

# ターゲット指定インストール（ESP32-S3 の場合）
./install.sh esp32s3

# 環境変数読込（毎回 or .bashrc に追加）
source ~/esp/esp-idf/export.sh

# 動作確認
idf.py --version
```

---

## 3. Windows → Linux の差異

### 3-1. コマンド・パス対照表

| 項目 | Windows | Linux |
|---|---|---|
| 環境初期化 | `ESP-IDF 5.4 PowerShell` ショートカット | `source ~/esp/esp-idf/export.sh` |
| シリアルポート | `COM7` | `/dev/ttyUSB0` or `/dev/ttyACM0` |
| パス区切り | `\` | `/`（ESP-IDF/CMake が自動処理） |
| スクリプト | PowerShell (`.ps1`) | Bash (`.sh`) |
| IDE | VSCode + ESP-IDF 拡張 | 同一（完全クロスプラットフォーム） |
| USB 権限 | 不要 | `dialout` グループへのユーザー追加が必要 |

### 3-2. 本プロジェクトの Windows 依存箇所

| ファイル | Windows 依存内容 | Linux 対応方法 |
|---|---|---|
| `push.ps1` | PowerShell スクリプト | `push.sh` の Bash 版を別途作成（または `gh` CLI で代替） |
| `build-plan.md` | PowerShell コマンド例 | Linux 版コマンド例を併記 |
| `SETUP.md` | Windows 前提の手順 | Linux セクション追加 |
| `build/build_matrix.py` | `idf.py` 呼出し | **変更不要**（Python + idf.py は OS 非依存） |
| `build/inject_assets.py` | `Path` 使用 | **変更不要**（`pathlib` は OS 非依存） |
| `build/verify_build.py` | `Path` 使用 | **変更不要**（`pathlib` は OS 非依存） |
| `tools/*.py` | `os.path` 使用 | **変更不要**（OS 非依存） |
| `build/matrix.yaml` | データ定義のみ | **変更不要** |

**結論**: Python スクリプト群は**全て OS 非依存**。対応が必要なのは PowerShell スクリプトとドキュメントのみ。

### 3-3. idf.py コマンドの互換性

```bash
# Windows でも Linux でも同一コマンド
idf.py set-target esp32s3
idf.py menuconfig
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor    # ← ポート名のみ異なる
```

---

## 4. Ubuntu 版別の注意事項

### 4-1. Ubuntu 22.04 LTS

| 問題 | 影響 | 対処 |
|---|---|---|
| `brltty` が USB シリアルを横取り | `/dev/ttyUSB0` が消える | `sudo apt remove brltty` |
| Python 3.10 の `venv` 問題 | ESP-IDF インストール失敗 | ESP-IDF v5.4.x では修正済み |
| GCC バージョン差異 | `const` ポインタ型変換で warning/error | `-Wno-error` オプションまたはソース修正 |

### 4-2. Ubuntu 24.04 LTS

| 問題 | 影響 | 対処 |
|---|---|---|
| Python パッケージ管理の変更 | `pip install` が system-wide で失敗 | ESP-IDF の `venv` 内で実行（自動対応） |
| aarch64 環境での問題 | ARM64 マシンでの一部ツールチェーン問題 | x86_64 環境を推奨 |
| 新しすぎる依存関係 | 一部ライブラリの互換性 | ESP-IDF v5.4.x が対応済み |

### 4-3. 推奨

**Ubuntu 22.04 LTS を推奨**。理由:
- ESP-IDF コミュニティでの実績が最も豊富
- LTS サポートが 2027年4月まで継続
- `brltty` 削除のみで安定動作
- 24.04 は新しく、ESP-IDF との組合せでの報告がまだ少ない

---

## 5. Linux 環境セットアップ手順（Quick Start）

### 5-1. 初回環境構築

```bash
# 1. 必要パッケージ
sudo apt update && sudo apt install -y \
  git wget flex bison gperf python3 python3-pip python3-venv \
  cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0

# 2. brltty 削除（22.04 の場合）
sudo apt remove -y brltty

# 3. USB シリアル権限
sudo usermod -a -G dialout $USER
newgrp dialout

# 4. ESP-IDF インストール
mkdir -p ~/esp && cd ~/esp
git clone -b v5.4.2 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf && ./install.sh esp32s3
source export.sh

# 5. 動作確認
idf.py --version
```

### 5-2. 本家ファームウェアのビルド

```bash
# 本家クローン
cd ~/xiaozhi-work
git clone https://github.com/78/xiaozhi-esp32.git
cd xiaozhi-esp32
git checkout v2.2.4
git submodule update --init --recursive

# ビルド
source ~/esp/esp-idf/export.sh
idf.py set-target esp32s3
idf.py menuconfig    # Language → English, OTA URL → classism.net
idf.py build

# 焼込
idf.py -p /dev/ttyUSB0 flash monitor
```

### 5-3. 本プロジェクトのビルドスクリプト実行

```bash
# 本プロジェクトクローン
cd ~/xiaozhi-work
git clone https://github.com/xCentury-lab/Xiaozhi-Firmware-update.git

# 環境変数設定
export XIAOZHI_SRC=~/xiaozhi-work/xiaozhi-esp32

# 量産ビルド（スケルトン実装完了後）
cd Xiaozhi-Firmware-update
pip install pyyaml
python build/build_matrix.py --board waveshare-esp32-s3-touch-lcd-1.85c --lang English
```

---

## 6. コミュニティ実績

| 出典 | 内容 |
|---|---|
| CSDN (liaocao_) | Ubuntu + VSCode + ESP-IDF で xiaozhi-esp32 ビルド成功の完全チュートリアル |
| GitHub Issue #1498 | Linux ビルドで CMake 依存解析が停止する問題（回避策あり） |
| GitHub Issue #1428 | Linux GCC での `const` ポインタ型変換エラー（コンパイラ厳格度差異） |
| 哇酷論壇 | xiaozhi-esp32 を Linux ネイティブに完全移植した事例（全志 SOC 向け） |

---

## 7. 対応ロードマップ（推奨）

### Phase 0 で対応すべき項目

| # | アクション | 工数 | 理由 |
|---|---|---|---|
| L-1 | `build-plan.md` に Linux コマンド例を併記 | 0.5日 | ドキュメント整備 |
| L-2 | `SETUP.md` に Linux セクション追加 | 0.5日 | オンボーディング対応 |
| L-3 | `push.sh`（Bash版）作成 | 0.5時間 | push.ps1 の Linux 対応 |

### STEP1 以降（任意）

| # | アクション | 工数 | 理由 |
|---|---|---|---|
| L-4 | GitHub Actions CI で Ubuntu ビルドテスト | 1日 | 自動検証 |
| L-5 | Docker ビルド環境（`espressif/idf` ベース） | 0.5日 | 再現性向上 |
| L-6 | `matrix.yaml` に `build_os` フィールド追加 | 0.5時間 | OS別設定管理 |

---

## 8. 結論

本プロジェクトの Ubuntu 対応は**低コスト・低リスク**で実現可能:

- **Python スクリプト群**: 変更不要（`pathlib` 使用で OS 非依存）
- **ESP-IDF ビルド**: `idf.py` コマンドが同一（ポート名のみ差異）
- **必要な対応**: ドキュメントの Linux 手順追記 + `push.sh` 作成のみ
- **推奨 OS**: Ubuntu 22.04 LTS（安定性・実績）

**Windows と Linux のデュアル環境での開発・量産が可能な構成です。**

---

*本調査は 2026-04-18 時点の ESP-IDF v5.4.x および 78/xiaozhi-esp32 の状態に基づく。*
