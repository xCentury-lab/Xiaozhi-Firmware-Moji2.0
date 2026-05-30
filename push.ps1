# ================================================================
# Xiaozhi-Firmware-update → GitHub xCentury-lab へ初回push
# ================================================================
#
# 前提:
#   1. GitHub上で空のprivateリポジトリ "xCentury-lab/Xiaozhi-Firmware-update" を作成済みであること
#      （URL: https://github.com/organizations/xCentury-lab/repositories/new）
#      - Repository name: Xiaozhi-Firmware-update
#      - Visibility: Private
#      - Initialize with README: OFF（チェック外す）
#      - Add .gitignore: None
#      - Add license: None
#   2. Git for Windows がインストール済み
#   3. GitHub アカウントの認証設定が済んでいる（SSH鍵 or Personal Access Token）
#
# 使い方:
#   PowerShell でこのディレクトリに移動して:
#     .\push.ps1
#
# ================================================================

$ErrorActionPreference = "Stop"

# スクリプト自身のあるディレクトリへ移動
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "=== Xiaozhi-Firmware-update push script ===" -ForegroundColor Cyan
Write-Host "作業ディレクトリ: $ScriptDir"
Write-Host ""

# ----- Git インストール確認 -----
try {
    $gitVersion = git --version
    Write-Host "✓ Git 検出: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git がインストールされていません" -ForegroundColor Red
    Write-Host "  https://git-scm.com/download/win からインストールしてください"
    exit 1
}

# ----- 既存の壊れた .git を削除 -----
if (Test-Path ".git") {
    Write-Host ""
    Write-Host "既存の .git ディレクトリを検出。削除します..." -ForegroundColor Yellow
    # OneDrive の読み取り専用属性を外してから削除
    Get-ChildItem -Path ".git" -Recurse -Force | ForEach-Object {
        $_.Attributes = 'Normal'
    }
    Remove-Item -Path ".git" -Recurse -Force
    Write-Host "✓ 削除完了" -ForegroundColor Green
}

# ----- リポジトリ初期化 -----
Write-Host ""
Write-Host "=== Step 1: git init ===" -ForegroundColor Cyan
git init -b main
git config user.name "xxc"
git config user.email "xxc@ctoch.jp"

# ----- ファイル追加 -----
Write-Host ""
Write-Host "=== Step 2: git add . ===" -ForegroundColor Cyan
git add .
$staged = git diff --cached --stat
Write-Host $staged

# ----- 初回コミット -----
Write-Host ""
Write-Host "=== Step 3: git commit ===" -ForegroundColor Cyan
$commitMsg = @"
Initial commit: 計画書 + 量産パイプライン雛形

- 2段階構成の計画書（STEP1: 英語版 / STEP2: 日本語版）
- ビルドマトリクス定義 (matrix.yaml)
- 量産ビルドスクリプト雛形 (build_matrix.py)
- アセット注入スクリプト雛形 (inject_assets.py)
- バイナリ検証スクリプト雛形 (verify_build.py)
- 既存OTAパッチツール移管 (tools/)
- アセットディレクトリ構造 (assets/logos, assets/sounds)
- バイナリは .gitignore で除外（firmware/README.md に運用方針記載）

計画の最終目的:
- 英語/日本語切替可能なXiaozhiファームウェアの量産
- OTAサーバーURL (classism.net) のビルド時組込
- ボードごとのカスタムロゴ・起動音差替
- 全て再現可能な形でWaveshareシリーズに展開
"@
git commit -m $commitMsg

# ----- リモート設定 -----
Write-Host ""
Write-Host "=== Step 4: git remote add origin ===" -ForegroundColor Cyan
$remoteUrl = "https://github.com/xCentury-lab/Xiaozhi-Firmware-update.git"

# 既存のoriginを確認
$existingRemote = git remote 2>$null
if ($existingRemote -contains "origin") {
    Write-Host "既存のoriginを更新: $remoteUrl"
    git remote set-url origin $remoteUrl
} else {
    Write-Host "originを追加: $remoteUrl"
    git remote add origin $remoteUrl
}

# ----- push -----
Write-Host ""
Write-Host "=== Step 5: git push -u origin main ===" -ForegroundColor Cyan
Write-Host "（GitHub 認証が求められる場合があります）"
git push -u origin main

Write-Host ""
Write-Host "=======================================" -ForegroundColor Green
Write-Host "✓ push 完了！" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "確認URL: https://github.com/xCentury-lab/Xiaozhi-Firmware-update"
Write-Host ""
