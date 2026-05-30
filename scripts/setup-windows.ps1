# ================================================================
# Xiaozhi ファームウェア量産環境 — Windows ワンショットセットアップ
# ================================================================
#
# Windows 11 に ESP-IDF + 本家 xiaozhi-esp32 + 本プロジェクト を準備する。
#
# 前提:
#   - Git for Windows がインストール済み
#   - Python 3.11+ がインストール済み
#   - ESP-IDF v5.5.x（v5.5.2+ 必須、推奨 v5.5.4）は別途インストーラで導入（本スクリプトでは案内のみ）
#     → v5.4.x は xiaozhi-esp32 v2.2.4 の依存（idf >=5.5.2）を満たさずビルド不可
#
# 使い方:
#   PowerShell で:
#     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#     .\scripts\setup-windows.ps1
#
# 完了後:
#   ESP-IDF PowerShell を開き:
#     cd $env:XIAOZHI_SRC     → 本家リポジトリ
#     cd $env:XIAOZHI_FW      → 本プロジェクト
#
# ================================================================

$ErrorActionPreference = "Stop"

$XIAOZHI_TAG = "v2.2.4"
$WORK_DIR = "C:\xiaozhi-work"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

Write-Host "=== Xiaozhi ファームウェア Windows セットアップ ===" -ForegroundColor Cyan
Write-Host ""

# ---- Step 1: Git 確認 ----
Step "Step 1: Git 確認"
try {
    $gitVer = git --version
    Ok "Git: $gitVer"
} catch {
    Fail "Git がインストールされていません。https://git-scm.com/download/win からインストールしてください"
}

# ---- Step 2: Python 確認 ----
Step "Step 2: Python 確認"
try {
    $pyVer = python --version
    Ok "Python: $pyVer"
} catch {
    Fail "Python がインストールされていません。https://www.python.org/downloads/ からインストールしてください"
}

# ---- Step 3: ESP-IDF 確認 ----
Step "Step 3: ESP-IDF 確認"
try {
    $idfVer = idf.py --version
    Ok "ESP-IDF: $idfVer"
} catch {
    Warn "idf.py が見つかりません"
    Write-Host ""
    Write-Host "  ESP-IDF のインストール手順:" -ForegroundColor Yellow
    Write-Host "  1. https://dl.espressif.com/dl/esp-idf/ からインストーラをダウンロード"
    Write-Host "  2. 管理者権限でインストーラを実行"
    Write-Host "  3. バージョン: v5.5.x を選択（v5.5.2+ 必須、推奨 v5.5.4）"
    Write-Host "  4. インストールパス: C:\esp\v5.5\esp-idf （短い英数字パス推奨）"
    Write-Host "  5. ターゲット: ESP32-S3 を選択"
    Write-Host "  6. インストール完了後、'ESP-IDF 5.5 PowerShell' ショートカットから起動"
    Write-Host ""
    Write-Host "  インストール後、ESP-IDF PowerShell で本スクリプトを再実行してください。" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "ESP-IDF なしで続行しますか？ (y/N)"
    if ($continue -ne "y") { exit 0 }
}

# ---- Step 4: 作業ディレクトリ ----
Step "Step 4: 作業ディレクトリ作成"
if (-not (Test-Path $WORK_DIR)) {
    New-Item -ItemType Directory -Path $WORK_DIR | Out-Null
}
Ok "作業ディレクトリ: $WORK_DIR"

# ---- Step 5: 本家リポジトリ ----
Step "Step 5: 本家 78/xiaozhi-esp32 ($XIAOZHI_TAG) のクローン"
$XIAOZHI_SRC = "$WORK_DIR\xiaozhi-esp32"
if (Test-Path $XIAOZHI_SRC) {
    Ok "本家リポジトリが既に存在: $XIAOZHI_SRC"
} else {
    Set-Location $WORK_DIR
    git clone https://github.com/78/xiaozhi-esp32.git
    Set-Location xiaozhi-esp32
    git checkout $XIAOZHI_TAG
    git submodule update --init --recursive
    Ok "本家リポジトリ準備完了 ($XIAOZHI_TAG)"
}

# ---- Step 6: Python 依存 ----
Step "Step 6: Python 依存パッケージ"
Set-Location $ProjectDir
pip install -r requirements.txt
Ok "pyyaml インストール完了"

# ---- Step 7: 環境変数 ----
Step "Step 7: 環境変数の設定"

# ユーザー環境変数に設定
[Environment]::SetEnvironmentVariable("XIAOZHI_SRC", $XIAOZHI_SRC, "User")
Ok "XIAOZHI_SRC = $XIAOZHI_SRC （ユーザー環境変数に永続化）"

[Environment]::SetEnvironmentVariable("XIAOZHI_FW", $ProjectDir, "User")
Ok "XIAOZHI_FW = $ProjectDir （ユーザー環境変数に永続化）"

# 現在のセッションにも反映
$env:XIAOZHI_SRC = $XIAOZHI_SRC
$env:XIAOZHI_FW = $ProjectDir

# ---- Step 8: バックアップディレクトリ ----
Step "Step 8: ディレクトリ構造の準備"
$backupDir = "$WORK_DIR\backup"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}
$fwDir = "$ProjectDir\firmware"
if (-not (Test-Path $fwDir)) {
    New-Item -ItemType Directory -Path $fwDir | Out-Null
}
Ok "backup/ と firmware/ ディレクトリを作成"

# ---- 完了 ----
Write-Host ""
Write-Host "=======================================" -ForegroundColor Green
Write-Host "  セットアップ完了！" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "次のステップ:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. 環境チェック:"
Write-Host "     powershell scripts\check-env.ps1"
Write-Host ""
Write-Host "  2. ESP-IDF PowerShell を開いてビルド:"
Write-Host "     cd $XIAOZHI_SRC"
Write-Host "     idf.py set-target esp32s3"
Write-Host "     idf.py menuconfig"
Write-Host "     idf.py build"
Write-Host ""
Write-Host "  3. 量産ビルド:"
Write-Host "     cd $env:XIAOZHI_FW"
Write-Host "     python build\build_matrix.py --board waveshare-esp32-s3-touch-lcd-1.85c --lang English"
Write-Host ""

Set-Location $ProjectDir
