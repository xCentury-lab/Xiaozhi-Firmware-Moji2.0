# ================================================================
# 環境検証スクリプト（Windows PowerShell）
# ================================================================
#
# セットアップ完了後に実行し、ビルド準備が整っているか確認する。
#
# 使い方:
#   powershell scripts\check-env.ps1
#
# ================================================================

$PASS = 0
$FAIL = 0
$WARN = 0

function Check-Pass($msg) { Write-Host "  ✓ $msg" -ForegroundColor Green; $script:PASS++ }
function Check-Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; $script:FAIL++ }
function Check-Warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Yellow; $script:WARN++ }

Write-Host "=== Xiaozhi ファームウェア ビルド環境チェック ===" -ForegroundColor Cyan
Write-Host ""

# ---- 1. OS ----
Write-Host "[OS]"
$osInfo = (Get-CimInstance Win32_OperatingSystem).Caption
Check-Pass "OS: $osInfo"

# ---- 2. 必要コマンド ----
Write-Host "[必要コマンド]"
foreach ($cmd in @("git", "python", "pip", "cmake")) {
    try {
        $path = (Get-Command $cmd -ErrorAction Stop).Source
        Check-Pass "$cmd : $path"
    } catch {
        Check-Fail "$cmd が見つかりません"
    }
}

# ---- 3. ESP-IDF ----
Write-Host "[ESP-IDF]"
try {
    $idfVer = idf.py --version 2>$null
    Check-Pass "idf.py: $idfVer"
} catch {
    Check-Fail "idf.py が見つかりません — ESP-IDF PowerShell で実行してください"
}

if ($env:IDF_PATH) {
    Check-Pass "IDF_PATH: $env:IDF_PATH"
} else {
    Check-Warn "IDF_PATH が未設定 — ESP-IDF PowerShell を使ってください"
}

# ---- 4. 本家リポジトリ ----
Write-Host "[本家 xiaozhi-esp32]"
if ($env:XIAOZHI_SRC) {
    if (Test-Path $env:XIAOZHI_SRC) {
        Check-Pass "XIAOZHI_SRC: $env:XIAOZHI_SRC"
        $cmakePath = Join-Path $env:XIAOZHI_SRC "CMakeLists.txt"
        if (Test-Path $cmakePath) {
            Check-Pass "CMakeLists.txt 存在確認"
        } else {
            Check-Fail "CMakeLists.txt が見つかりません — クローンが不完全な可能性"
        }
        # 言語アセット確認
        $enUS = Join-Path $env:XIAOZHI_SRC "main\assets\locales\en-US"
        if (Test-Path $enUS) {
            Check-Pass "en-US アセット: 存在"
        } else {
            Check-Warn "en-US アセットが見つかりません"
        }
        $jaJP = Join-Path $env:XIAOZHI_SRC "main\assets\locales\ja-JP"
        if (Test-Path $jaJP) {
            Check-Pass "ja-JP アセット: 存在"
        } else {
            Check-Warn "ja-JP アセットが見つかりません"
        }
    } else {
        Check-Fail "XIAOZHI_SRC ディレクトリが存在しません: $env:XIAOZHI_SRC"
    }
} else {
    Check-Fail "XIAOZHI_SRC が未設定 — scripts\setup-windows.ps1 を実行してください"
}

# ---- 5. 本プロジェクト ----
Write-Host "[Xiaozhi-Firmware-update]"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

$matrixPath = Join-Path $ProjectDir "build\matrix.yaml"
if (Test-Path $matrixPath) {
    Check-Pass "matrix.yaml: 存在"
} else {
    Check-Fail "matrix.yaml が見つかりません"
}

$buildScript = Join-Path $ProjectDir "build\build_matrix.py"
if (Test-Path $buildScript) {
    Check-Pass "build_matrix.py: 存在"
} else {
    Check-Fail "build_matrix.py が見つかりません"
}

# Python 依存
try {
    python -c "import yaml" 2>$null
    Check-Pass "pyyaml: インストール済み"
} catch {
    Check-Fail "pyyaml が未インストール — 'pip install -r requirements.txt'"
}

# ---- 6. シリアルポート ----
Write-Host "[シリアルポート]"
$ports = [System.IO.Ports.SerialPort]::GetPortNames()
if ($ports.Count -gt 0) {
    Check-Pass "COM ポート: $($ports -join ', ')"
} else {
    Check-Warn "COM ポートが検出されません（ESP32 が未接続の可能性）"
}

# ---- サマリ ----
Write-Host ""
Write-Host "=== 結果 ===" -ForegroundColor Cyan
Write-Host "  PASS: $PASS  FAIL: $FAIL  WARN: $WARN"
Write-Host ""

if ($FAIL -eq 0) {
    Write-Host "ビルド環境は準備完了です。" -ForegroundColor Green
    exit 0
} else {
    Write-Host "$FAIL 件の問題があります。上記のメッセージを確認してください。" -ForegroundColor Red
    exit 1
}
