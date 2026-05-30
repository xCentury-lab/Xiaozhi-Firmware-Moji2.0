#!/bin/bash
# ================================================================
# Xiaozhi-Firmware-update → GitHub xCentury-lab へ初回push
# ================================================================
#
# 前提:
#   1. GitHub上で空のprivateリポジトリ "xCentury-lab/Xiaozhi-Firmware-update" を作成済み
#   2. git がインストール済み
#   3. GitHub の認証設定済み（SSH鍵 or gh auth login or PAT）
#
# 使い方:
#   chmod +x push.sh
#   ./push.sh
#
# ================================================================

set -e

# スクリプト自身のあるディレクトリへ移動
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Xiaozhi-Firmware-update push script ==="
echo "作業ディレクトリ: $SCRIPT_DIR"
echo ""

# ----- Git インストール確認 -----
if command -v git &>/dev/null; then
    echo "✓ Git 検出: $(git --version)"
else
    echo "✗ Git がインストールされていません"
    echo "  sudo apt install git"
    exit 1
fi

# ----- 既存の .git を削除 -----
if [ -d ".git" ]; then
    echo ""
    echo "既存の .git ディレクトリを検出。削除します..."
    rm -rf .git
    echo "✓ 削除完了"
fi

# ----- リポジトリ初期化 -----
echo ""
echo "=== Step 1: git init ==="
git init -b main
git config user.name "xxc"
git config user.email "xxc@ctoch.jp"

# ----- ファイル追加 -----
echo ""
echo "=== Step 2: git add . ==="
git add .
git diff --cached --stat

# ----- 初回コミット -----
echo ""
echo "=== Step 3: git commit ==="
git commit -m "Initial commit: 計画書 + 量産パイプライン雛形

- 2段階構成の計画書（STEP1: 英語版 / STEP2: 日本語版）
- ビルドマトリクス定義 (matrix.yaml)
- 量産ビルドスクリプト雛形 (build_matrix.py)
- アセット注入スクリプト雛形 (inject_assets.py)
- バイナリ検証スクリプト雛形 (verify_build.py)
- 既存OTAパッチツール移管 (tools/)
- アセットディレクトリ構造 (assets/logos, assets/sounds)
- バイナリは .gitignore で除外（firmware/README.md に運用方針記載）"

# ----- リモート設定 -----
echo ""
echo "=== Step 4: git remote add origin ==="
REMOTE_URL="https://github.com/xCentury-lab/Xiaozhi-Firmware-update.git"

if git remote | grep -q "^origin$"; then
    echo "既存のoriginを更新: $REMOTE_URL"
    git remote set-url origin "$REMOTE_URL"
else
    echo "originを追加: $REMOTE_URL"
    git remote add origin "$REMOTE_URL"
fi

# ----- push -----
echo ""
echo "=== Step 5: git push -u origin main ==="
echo "（GitHub 認証が求められる場合があります）"
git push -u origin main

echo ""
echo "======================================="
echo "✓ push 完了！"
echo "======================================="
echo ""
echo "確認URL: https://github.com/xCentury-lab/Xiaozhi-Firmware-update"
echo ""
