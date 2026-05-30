#!/bin/bash
# ================================================================
# 環境検証スクリプト
# ================================================================
#
# セットアップ完了後に実行し、ビルド準備が整っているか確認する。
#
# 使い方:
#   bash scripts/check-env.sh
#
# ================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check_pass() { echo -e "  ${GREEN}✓${NC} $1"; ((PASS++)); }
check_fail() { echo -e "  ${RED}✗${NC} $1"; ((FAIL++)); }
check_warn() { echo -e "  ${YELLOW}⚠${NC} $1"; ((WARN++)); }

echo "=== Xiaozhi ファームウェア ビルド環境チェック ==="
echo ""

# ---- 1. OS ----
echo "[OS]"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    check_pass "OS: $PRETTY_NAME"
else
    check_warn "OS 情報を取得できません"
fi

# ---- 2. 必要コマンド ----
echo "[必要コマンド]"
for cmd in git python3 pip3 cmake ninja ccache wget curl; do
    if command -v $cmd &>/dev/null; then
        check_pass "$cmd: $(command -v $cmd)"
    else
        check_fail "$cmd が見つかりません"
    fi
done

# ---- 3. ESP-IDF ----
echo "[ESP-IDF]"
if command -v idf.py &>/dev/null; then
    check_pass "idf.py: 利用可能"
    IDF_VER=$(idf.py --version 2>/dev/null || echo "取得失敗")
    check_pass "ESP-IDF バージョン: $IDF_VER"
else
    check_fail "idf.py が見つかりません — 'get_idf' または 'source ~/esp/esp-idf/export.sh' を実行してください"
fi

if [ -d "${IDF_PATH:-}" ]; then
    check_pass "IDF_PATH: $IDF_PATH"
else
    check_warn "IDF_PATH が未設定 — ESP-IDF 環境を有効化してください"
fi

# ---- 4. 本家リポジトリ ----
echo "[本家 xiaozhi-esp32]"
if [ -n "${XIAOZHI_SRC:-}" ]; then
    if [ -d "$XIAOZHI_SRC" ]; then
        check_pass "XIAOZHI_SRC: $XIAOZHI_SRC"
        if [ -f "$XIAOZHI_SRC/CMakeLists.txt" ]; then
            check_pass "CMakeLists.txt 存在確認"
        else
            check_fail "CMakeLists.txt が見つかりません — クローンが不完全な可能性"
        fi
        # 言語アセット確認
        if [ -d "$XIAOZHI_SRC/main/assets/locales/en-US" ]; then
            check_pass "en-US アセット: 存在"
        else
            check_warn "en-US アセットが見つかりません"
        fi
        if [ -d "$XIAOZHI_SRC/main/assets/locales/ja-JP" ]; then
            check_pass "ja-JP アセット: 存在"
        else
            check_warn "ja-JP アセットが見つかりません"
        fi
    else
        check_fail "XIAOZHI_SRC ディレクトリが存在しません: $XIAOZHI_SRC"
    fi
else
    check_fail "XIAOZHI_SRC が未設定 — 'export XIAOZHI_SRC=~/xiaozhi-work/xiaozhi-esp32'"
fi

# ---- 5. 本プロジェクト ----
echo "[Xiaozhi-Firmware-update]"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_DIR/build/matrix.yaml" ]; then
    check_pass "matrix.yaml: 存在"
else
    check_fail "matrix.yaml が見つかりません"
fi

if [ -f "$PROJECT_DIR/build/build_matrix.py" ]; then
    check_pass "build_matrix.py: 存在"
else
    check_fail "build_matrix.py が見つかりません"
fi

# Python 依存
if python3 -c "import yaml" 2>/dev/null; then
    check_pass "pyyaml: インストール済み"
else
    check_fail "pyyaml が未インストール — 'pip install -r requirements.txt'"
fi

# ---- 6. USB シリアル ----
echo "[USB シリアル]"
if groups "$USER" | grep -q dialout; then
    check_pass "dialout グループ: 所属済み"
else
    check_fail "dialout グループに未所属 — 'sudo usermod -a -G dialout \$USER'"
fi

if dpkg -l brltty 2>/dev/null | grep -q "^ii"; then
    check_warn "brltty がインストール済み — USB シリアルを横取りする可能性あり"
else
    check_pass "brltty: 未インストール"
fi

# USB デバイス
USB_DEVS=$(ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true)
if [ -n "$USB_DEVS" ]; then
    check_pass "USB シリアルデバイス: $USB_DEVS"
else
    check_warn "USB シリアルデバイスが検出されません（ESP32 が未接続の可能性）"
fi

# ---- サマリ ----
echo ""
echo "=== 結果 ==="
echo -e "  ${GREEN}PASS: $PASS${NC}  ${RED}FAIL: $FAIL${NC}  ${YELLOW}WARN: $WARN${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}ビルド環境は準備完了です。${NC}"
    exit 0
else
    echo -e "${RED}$FAIL 件の問題があります。上記のメッセージを確認してください。${NC}"
    exit 1
fi
