#!/bin/bash
# ================================================================
# Xiaozhi ファームウェア量産環境 — Ubuntu ワンショットセットアップ
# ================================================================
#
# Ubuntu Desktop 22.04 / 24.04 を新規インストールした直後に実行し、
# ESP-IDF + 本家 xiaozhi-esp32 + 本プロジェクト をすべて準備する。
#
# 使い方:
#   chmod +x scripts/setup-ubuntu.sh
#   ./scripts/setup-ubuntu.sh
#
# 所要時間: 約 15-30 分（回線速度による）
#
# 完了後:
#   get_idf            → ESP-IDF 環境有効化
#   cd $XIAOZHI_SRC    → 本家リポジトリ
#   cd $XIAOZHI_FW     → 本プロジェクト
#
# ================================================================

set -euo pipefail

# ---- 設定 ----
# 注意: xiaozhi-esp32 v2.2.4 の main/idf_component.yml は `idf >=5.5.2` を要求する
# v5.4.x ではビルド時に "project depends on idf (>=5.5.2)" エラーになるため v5.5.x 必須
ESP_IDF_VERSION="v5.5.4"
XIAOZHI_TAG="v2.2.4"
WORK_DIR="$HOME/xiaozhi-work"
ESP_DIR="$HOME/esp"
IDF_DIR="$ESP_DIR/esp-idf"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ---- カラー出力 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

step() { echo -e "\n${CYAN}=== $1 ===${NC}"; }
ok()   { echo -e "${GREEN}✓ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }

# ---- OS 確認 ----
step "Step 0: OS 確認"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "  OS: $PRETTY_NAME"
    case "$VERSION_ID" in
        22.04|24.04) ok "Ubuntu $VERSION_ID — サポート対象" ;;
        *)           warn "Ubuntu $VERSION_ID — テスト未実施、続行します" ;;
    esac
else
    warn "/etc/os-release が見つかりません。続行します。"
fi

# ---- Step 1: 必要パッケージ ----
step "Step 1: 必要パッケージのインストール"
sudo apt update
sudo apt install -y \
    git wget curl flex bison gperf \
    python3 python3-pip python3-venv \
    cmake ninja-build ccache \
    libffi-dev libssl-dev \
    dfu-util libusb-1.0-0
ok "パッケージインストール完了"

# ---- Step 2: brltty 削除（22.04 のみ） ----
step "Step 2: brltty 対策"
if dpkg -l brltty &>/dev/null 2>&1; then
    sudo apt remove -y brltty
    ok "brltty を削除しました（USB シリアル横取り防止）"
else
    ok "brltty は未インストール — スキップ"
fi

# ---- Step 3: USB シリアル権限 ----
step "Step 3: USB シリアル権限 (dialout)"
if groups "$USER" | grep -q dialout; then
    ok "既に dialout グループに所属"
else
    sudo usermod -a -G dialout "$USER"
    ok "dialout グループに追加しました"
    warn "ログアウト＆再ログイン、または 'newgrp dialout' で反映してください"
fi

# ---- Step 4: ESP-IDF ----
step "Step 4: ESP-IDF $ESP_IDF_VERSION のインストール"
mkdir -p "$ESP_DIR"

if [ -d "$IDF_DIR" ]; then
    ok "ESP-IDF ディレクトリが既に存在します: $IDF_DIR"
    cd "$IDF_DIR"
    CURRENT_TAG=$(git describe --tags 2>/dev/null || echo "unknown")
    echo "  現在のバージョン: $CURRENT_TAG"
else
    cd "$ESP_DIR"
    git clone -b "$ESP_IDF_VERSION" --recursive https://github.com/espressif/esp-idf.git
    ok "ESP-IDF クローン完了"
fi

cd "$IDF_DIR"
./install.sh esp32s3
ok "ESP-IDF ツールチェーンインストール完了"

# 環境変数テスト
set +u  # export.sh 内で未定義変数を使う場合があるため
source "$IDF_DIR/export.sh" 2>/dev/null || true
set -u
if command -v idf.py &>/dev/null; then
    ok "idf.py 動作確認: $(idf.py --version 2>/dev/null || echo 'OK')"
else
    warn "idf.py が PATH に見つかりません — 'source $IDF_DIR/export.sh' を手動実行してください"
fi

# ---- Step 5: 本家リポジトリ ----
step "Step 5: 本家 78/xiaozhi-esp32 ($XIAOZHI_TAG) のクローン"
mkdir -p "$WORK_DIR"

XIAOZHI_SRC_DIR="$WORK_DIR/xiaozhi-esp32"
if [ -d "$XIAOZHI_SRC_DIR" ]; then
    ok "本家リポジトリが既に存在します: $XIAOZHI_SRC_DIR"
else
    cd "$WORK_DIR"
    git clone https://github.com/78/xiaozhi-esp32.git
    cd xiaozhi-esp32
    git checkout "$XIAOZHI_TAG"
    git submodule update --init --recursive
    ok "本家リポジトリ準備完了 ($XIAOZHI_TAG)"
fi

# ---- Step 6: 本プロジェクト ----
step "Step 6: 本プロジェクトの Python 依存インストール"
cd "$PROJECT_DIR"
pip install -r requirements.txt 2>/dev/null || pip install --break-system-packages -r requirements.txt 2>/dev/null || {
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ok "venv 内にインストールしました (.venv/)"
}
ok "Python 依存インストール完了"

# ---- Step 7: .bashrc 設定 ----
step "Step 7: .bashrc への環境設定追加"
BASHRC="$HOME/.bashrc"

add_to_bashrc() {
    local line="$1"
    local comment="$2"
    if ! grep -Fq "$line" "$BASHRC" 2>/dev/null; then
        echo "" >> "$BASHRC"
        echo "# $comment" >> "$BASHRC"
        echo "$line" >> "$BASHRC"
        ok "追加: $line"
    else
        ok "既存: $line"
    fi
}

add_to_bashrc "alias get_idf='source $IDF_DIR/export.sh'" \
              "ESP-IDF 環境有効化エイリアス"
add_to_bashrc "export XIAOZHI_SRC=$XIAOZHI_SRC_DIR" \
              "本家 xiaozhi-esp32 リポジトリパス"
add_to_bashrc "export XIAOZHI_FW=$PROJECT_DIR" \
              "Xiaozhi-Firmware-update プロジェクトパス"

# ---- Step 8: バックアップディレクトリ ----
step "Step 8: ディレクトリ構造の準備"
mkdir -p "$WORK_DIR/backup"
mkdir -p "$PROJECT_DIR/firmware"
ok "backup/ と firmware/ ディレクトリを作成"

# ---- 完了 ----
echo ""
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}  セットアップ完了！${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo "次のステップ:"
echo ""
echo "  1. 環境変数を反映:"
echo "     source ~/.bashrc"
echo ""
echo "  2. ESP-IDF 環境を有効化:"
echo "     get_idf"
echo ""
echo "  3. 環境チェック:"
echo "     bash scripts/check-env.sh"
echo ""
echo "  4. 中国語版ビルド再現 (Phase 0-C):"
echo "     cd \$XIAOZHI_SRC"
echo "     idf.py set-target esp32s3"
echo "     idf.py build"
echo ""
echo "  5. 英語版ビルド (Phase 1-A):"
echo "     idf.py menuconfig"
echo "     # → Xiaozhi Assistant → Default Language → English"
echo "     # → Xiaozhi Assistant → OTA URL → https://classism.net/xiaozhi/ota/"
echo "     idf.py fullclean && idf.py build"
echo ""
echo "  6. 量産ビルド (Phase 1-D 以降):"
echo "     cd \$XIAOZHI_FW"
echo "     python build/build_matrix.py --board waveshare-esp32-s3-touch-lcd-1.85c --lang English"
echo ""
