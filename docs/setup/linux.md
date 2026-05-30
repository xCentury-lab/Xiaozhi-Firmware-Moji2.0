# Linux セットアップ手順（Ubuntu 22.04 / 24.04）

> **対象 OS**: Ubuntu Desktop 22.04 LTS（推奨）/ Ubuntu Desktop 24.04 LTS
> **Windows の方**: [windows.md](windows.md) を参照してください
> **ドキュメント目次**: [../README.md](../README.md)

---

## クイックセットアップ（ワンショット）

Ubuntu Desktop を用意した直後なら、以下の1コマンドで全環境を自動構築できます:

```bash
git clone https://github.com/xCentury-lab/Xiaozhi-Firmware-update.git
cd Xiaozhi-Firmware-update
bash scripts/setup-ubuntu.sh
```

このスクリプトは以下を自動実行します:
- 必要パッケージのインストール（git, cmake, ninja, python3 等）
- brltty 削除（Ubuntu 22.04）
- USB シリアル権限の設定（dialout グループ）
- ESP-IDF v5.5.4 のインストール（v2.2.4 は `idf >=5.5.2` 要求のため v5.4.x 不可）
- 本家 78/xiaozhi-esp32 (v2.2.4) のクローン
- Python 依存パッケージのインストール
- .bashrc への環境変数登録（`get_idf`, `XIAOZHI_SRC`, `XIAOZHI_FW`）

セットアップ完了後の確認:

```bash
source ~/.bashrc    # .bashrc の get_idf エイリアス・環境変数を読込
get_idf             # ESP-IDF 環境を有効化（PATH に idf.py を通す）
bash scripts/check-env.sh
```

> **重要**: `bash scripts/check-env.sh` は新しい子シェルを起動するため、親シェルで `get_idf` を実行していないと `idf.py が見つかりません` と FAIL します。新ターミナルセッションを開いた場合も毎回 `get_idf` を実行してください。

以下は手動でセットアップする場合の詳細手順です。

---

## ステップ 1: 必要パッケージのインストール

```bash
sudo apt update && sudo apt install -y \
  git wget curl flex bison gperf python3 python3-pip python3-venv \
  cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0
```

> **注**: `curl` は `scripts/check-env.sh` の必須コマンドチェックに含まれるため必ずインストールしてください。

> **ディスク要件**: ESP-IDF 本体約 3.3GB、ツールチェーン約 3.7GB（xtensa-esp-elf / riscv32-esp-elf / openocd / python venv など）。合計 **7GB 以上**の空き容量を確保してください。

### Ubuntu 22.04 の追加対応

```bash
# brltty が USB シリアルポートを横取りする問題の対策
sudo apt remove -y brltty
```

## ステップ 2: USB シリアル権限の設定

ESP32 への焼込には `/dev/ttyUSB0`（または `/dev/ttyACM0`）へのアクセスが必要です。

```bash
# dialout グループに追加
sudo usermod -a -G dialout $USER

# 即座に反映（ログアウト不要）
newgrp dialout

# 確認
groups | grep dialout
```

## ステップ 3: ESP-IDF v5.5.x のインストール

> **バージョン要件**: xiaozhi-esp32 v2.2.4 の `main/idf_component.yml` が `idf >=5.5.2` を必須指定するため、v5.4.x では `cmake set-target` が "project depends on idf (>=5.5.2)" エラーで失敗します。v5.5.2 以降（推奨 v5.5.4）を使ってください。

```bash
# インストール先
mkdir -p ~/esp && cd ~/esp

# ESP-IDF クローン（v5.5.4 を推奨）
git clone -b v5.5.4 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf

# ESP32-S3 向けツールチェーンをインストール
./install.sh esp32s3

# 環境変数を読込
source export.sh

# 動作確認
idf.py --version
```

### .bashrc への登録（推奨）

毎回 `source export.sh` を打たなくて済むようにエイリアスを登録:

```bash
echo 'alias get_idf="source ~/esp/esp-idf/export.sh"' >> ~/.bashrc
source ~/.bashrc
```

以降は `get_idf` コマンドで ESP-IDF 環境を有効化できます。

## ステップ 4: 本家リポジトリのクローン

```bash
mkdir -p ~/xiaozhi-work && cd ~/xiaozhi-work

git clone https://github.com/78/xiaozhi-esp32.git
cd xiaozhi-esp32
git checkout v2.2.4
git submodule update --init --recursive
```

## ステップ 5: 中国語版ビルド再現（Phase 0-C）

```bash
cd ~/xiaozhi-work/xiaozhi-esp32

# ESP-IDF 環境を有効化
get_idf    # または source ~/esp/esp-idf/export.sh

# ターゲット設定
idf.py set-target esp32s3

# menuconfig（デフォルトの中国語のまま）
idf.py menuconfig

# ビルド
idf.py build

# 焼込前にフルバックアップ（重要）
esptool.py -p /dev/ttyUSB0 -b 460800 read_flash 0x0 0x1000000 \
  ~/xiaozhi-work/backup/waveshare-1.85c_stock_$(date +%Y%m%d).bin

# 焼込＆モニター
idf.py -p /dev/ttyUSB0 flash monitor
# モニター終了: Ctrl+]
```

## ステップ 6: 本プロジェクトのクローン

```bash
cd ~/xiaozhi-work

git clone https://github.com/xCentury-lab/Xiaozhi-Firmware-update.git
cd Xiaozhi-Firmware-update

# Python 依存パッケージ
pip3 install -r requirements.txt
```

### 環境変数の設定

```bash
# 本家リポジトリのパスを設定
export XIAOZHI_SRC=~/xiaozhi-work/xiaozhi-esp32

# .bashrc に永続化（推奨）
echo 'export XIAOZHI_SRC=~/xiaozhi-work/xiaozhi-esp32' >> ~/.bashrc
```

## ステップ 7: 英語版ビルド（Phase 1-A）

```bash
cd ~/xiaozhi-work/xiaozhi-esp32
get_idf

# menuconfig で言語・OTA URL を変更
idf.py menuconfig
# → Xiaozhi Assistant → Default Language → English
# → Xiaozhi Assistant → OTA URL → https://classism.net/xiaozhi/ota/

# クリーンビルド
idf.py fullclean
idf.py build

# 焼込＆モニター
idf.py -p /dev/ttyUSB0 flash monitor
```

## ステップ 8: 量産ビルド（Phase 1-D 以降）

```bash
cd ~/xiaozhi-work/Xiaozhi-Firmware-update

# 単一ボードをビルド
python build/build_matrix.py --board waveshare-esp32-s3-touch-lcd-1.85c --lang English

# 全バリエーション一括ビルド
python build/build_matrix.py --all

# ビルド成果物を検証
python build/verify_build.py firmware/v2.2.4_waveshare-esp32-s3-touch-lcd-1.85c_en_company/merged-binary.bin
```

---

## GitHub 認証（初回のみ）

### 方法1: GitHub CLI（推奨）

```bash
# GitHub CLI インストール
sudo apt install -y gh

# ログイン
gh auth login
```

### 方法2: SSH 鍵

```bash
# 鍵生成
ssh-keygen -t ed25519 -C "xxc@ctoch.jp"

# 公開鍵を表示してGitHubに登録
cat ~/.ssh/id_ed25519.pub
# → https://github.com/settings/ssh/new に貼り付け

# リモートURLをSSH形式に変更
cd ~/xiaozhi-work/Xiaozhi-Firmware-update
git remote set-url origin git@github.com:xCentury-lab/Xiaozhi-Firmware-update.git
```

### 方法3: Personal Access Token

1. https://github.com/settings/tokens/new から PAT を作成
   - Scopes: `repo` にチェック
2. `git push` 時のパスワード欄に PAT を貼り付け

---

## トラブルシューティング

### `/dev/ttyUSB0` が見つからない

```bash
# 接続されている USB デバイスを確認
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null

# カーネルログで検出状況を確認
dmesg | grep tty

# brltty が横取りしている場合（Ubuntu 22.04）
sudo apt remove brltty
# デバイスを抜き差しして再確認
```

### `Permission denied: '/dev/ttyUSB0'`

```bash
# dialout グループに追加されているか確認
groups | grep dialout

# 追加されていない場合
sudo usermod -a -G dialout $USER
# ログアウト＆再ログイン、または:
newgrp dialout
```

### ESP-IDF インストールで Python エラー

```bash
# Ubuntu 24.04 の場合、venv が必要
sudo apt install -y python3-venv

# ESP-IDF を再インストール
cd ~/esp/esp-idf
./install.sh esp32s3
```

### `idf.py: command not found`

```bash
# ESP-IDF 環境変数が読込まれていない
source ~/esp/esp-idf/export.sh
# または
get_idf
```

### ビルド中に CMake が停止する

```bash
# GitHub Issue #1498 の既知問題
# ESP-IDF のキャッシュをクリア
rm -rf build/
idf.py set-target esp32s3
idf.py build
```

### GCC の const ポインタ型変換エラー

```bash
# GitHub Issue #1428 の既知問題
# sdkconfig.defaults に追加:
echo 'CONFIG_COMPILER_WARN_WRITE_STRINGS=n' >> sdkconfig.defaults
idf.py fullclean && idf.py build
```

---

## Windows との差異まとめ

| 項目 | Windows | Linux |
|---|---|---|
| ESP-IDF 起動 | 専用 PowerShell ショートカット | `source export.sh` or `get_idf` |
| シリアルポート | `COM7` | `/dev/ttyUSB0` or `/dev/ttyACM0` |
| パス | `C:\xiaozhi-work\` | `~/xiaozhi-work/` |
| 初回push | `push.ps1` | `push.sh` |
| USB 権限 | 不要 | `dialout` グループ追加 |
| モニター終了 | `Ctrl+]` | `Ctrl+]` |
| IDE | VSCode + ESP-IDF 拡張 | 同一 |

---

*ESP-IDF 公式 Linux ガイド: https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32/get-started/linux-macos-setup.html*
