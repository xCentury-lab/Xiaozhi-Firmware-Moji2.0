# Windows セットアップ手順

> **対象 OS**: Windows 11
> **Linux (Ubuntu) の方**: [linux.md](linux.md) を参照してください
> **ドキュメント目次**: [../README.md](../README.md)

---

## クイックセットアップ

### 前提条件

以下を事前にインストールしてください:

| ソフトウェア | ダウンロード先 |
|---|---|
| Git for Windows | https://git-scm.com/download/win |
| Python 3.11+ | https://www.python.org/downloads/ |
| ESP-IDF **v5.5.2+**（推奨 v5.5.4） | https://dl.espressif.com/dl/esp-idf/ |

> **ESP-IDF インストールの注意**:
> - **v5.5.2 以上**が必須（xiaozhi-esp32 v2.2.4 の `main/idf_component.yml` が `idf >=5.5.2` を要求）。v5.4.x では `cmake set-target` が失敗します
> - インストールパスは短い英数字（例: `C:\esp\v5.5\esp-idf`）
> - ターゲット `ESP32-S3` を選択
> - ウイルス対策ソフトは `C:\esp\` を除外推奨

### ワンショットセットアップ

ESP-IDF インストール後、PowerShell で以下を実行:

```powershell
cd C:\xiaozhi-work
git clone https://github.com/xCentury-lab/Xiaozhi-Firmware-update.git
cd Xiaozhi-Firmware-update

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup-windows.ps1
```

このスクリプトは以下を自動実行します:
- Git / Python / ESP-IDF の存在確認
- 本家 78/xiaozhi-esp32 (v2.2.4) のクローン
- Python 依存パッケージ（pyyaml）のインストール
- 環境変数 `XIAOZHI_SRC` / `XIAOZHI_FW` の永続設定
- backup / firmware ディレクトリの作成

セットアップ完了後の確認:

```powershell
powershell scripts\check-env.ps1
```

以下は手動でセットアップする場合の詳細手順です。

---

## ステップ 1: ESP-IDF 環境構築

1. [ESP-IDF Windows Installer](https://dl.espressif.com/dl/esp-idf/) から **v5.5.x**（v5.5.2 以上、推奨 v5.5.4）をダウンロード
2. 管理者権限でオフラインインストーラ実行
3. インストールパスは短い英数字（例: `C:\esp\v5.5\esp-idf`）
4. ターゲット `ESP32-S3` を選択
5. `ESP-IDF 5.5 PowerShell` ショートカットから起動

```powershell
idf.py --version
```

## ステップ 2: 本家リポジトリのクローン

ESP-IDF PowerShell で実行:

```powershell
mkdir C:\xiaozhi-work
cd C:\xiaozhi-work
git clone https://github.com/78/xiaozhi-esp32.git
cd xiaozhi-esp32
git checkout v2.2.4
git submodule update --init --recursive
```

## ステップ 3: 本プロジェクトのクローン

```powershell
cd C:\xiaozhi-work
git clone https://github.com/xCentury-lab/Xiaozhi-Firmware-update.git
cd Xiaozhi-Firmware-update
pip install -r requirements.txt
```

### 環境変数の設定

```powershell
# ユーザー環境変数に永続設定
[Environment]::SetEnvironmentVariable("XIAOZHI_SRC", "C:\xiaozhi-work\xiaozhi-esp32", "User")
[Environment]::SetEnvironmentVariable("XIAOZHI_FW", "C:\xiaozhi-work\Xiaozhi-Firmware-update", "User")

# 現在のセッションにも反映
$env:XIAOZHI_SRC = "C:\xiaozhi-work\xiaozhi-esp32"
$env:XIAOZHI_FW = "C:\xiaozhi-work\Xiaozhi-Firmware-update"
```

## ステップ 4: 中国語版ビルド再現（Phase 0-C）

ESP-IDF PowerShell で実行:

```powershell
cd $env:XIAOZHI_SRC
idf.py set-target esp32s3
idf.py menuconfig    # デフォルトの中国語のまま
idf.py build

# 焼込前にフルバックアップ（重要）
esptool.py -p COM7 -b 460800 read-flash 0x0 0x1000000 `
  C:\xiaozhi-work\backup\waveshare-1.85c_stock_$(Get-Date -Format yyyyMMdd).bin

# 焼込＆モニター
idf.py -p COM7 flash monitor
```

## ステップ 5: 英語版ビルド（Phase 1-A）

```powershell
cd $env:XIAOZHI_SRC

idf.py menuconfig
# → Xiaozhi Assistant → Default Language → English
# → Xiaozhi Assistant → OTA URL → https://classism.net/xiaozhi/ota/

idf.py fullclean
idf.py build
idf.py -p COM7 flash monitor
```

## ステップ 6: 量産ビルド（Phase 1-D 以降）

```powershell
cd $env:XIAOZHI_FW

# 単一ボードをビルド
python build\build_matrix.py --board waveshare-esp32-s3-touch-lcd-1.85c --lang English

# 全バリエーション一括ビルド
python build\build_matrix.py --all

# ビルド成果物を検証
python build\verify_build.py firmware\v2.2.4_waveshare-esp32-s3-touch-lcd-1.85c_en_company\merged-binary.bin
```

---

## GitHub 認証

### 方法1: Git Credential Manager（推奨、Git for Windows 付属）

- 初回 push 時にブラウザが開き、GitHub へのログインを促される
- ログイン後、認証情報が Windows 資格情報マネージャーに保存される

### 方法2: GitHub CLI

```powershell
winget install GitHub.cli
gh auth login
```

### 方法3: SSH 鍵

```powershell
ssh-keygen -t ed25519 -C "xxc@ctoch.jp"
# 公開鍵を https://github.com/settings/ssh/new に登録
git remote set-url origin git@github.com:xCentury-lab/Xiaozhi-Firmware-update.git
```

### 方法4: Personal Access Token

1. https://github.com/settings/tokens/new から PAT を作成（Scopes: `repo`）
2. push 時のパスワード欄に PAT を貼り付け

---

## トラブルシューティング

### PowerShell でスクリプトが実行できない

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### `idf.py: command not found`

ESP-IDF PowerShell（スタートメニューの `ESP-IDF 5.4 PowerShell` ショートカット）から実行してください。
通常の PowerShell では idf.py にパスが通っていません。

### COM ポートが見つからない

1. デバイスマネージャーで「ポート (COM & LPT)」を確認
2. ESP32 の USB ドライバがインストールされているか確認
3. `COM7` を実際のポート番号に置き換え

### ビルドが途中で停止する

```powershell
# ウイルス対策ソフトの除外設定を確認
# Windows Defender → ウイルスと脅威の防止 → 設定 → 除外の追加
# 以下を除外: C:\esp\  C:\xiaozhi-work\

# ビルドキャッシュのクリア
idf.py fullclean
idf.py build
```

### OneDrive フォルダでの問題

OneDrive 同期フォルダ内でビルドすると、同期遅延でファイルロックが発生することがあります。
`C:\xiaozhi-work\` のように**OneDrive 外のパス**を使用してください。

---

## Linux との差異まとめ

| 項目 | Windows | Linux |
|---|---|---|
| ESP-IDF 起動 | 専用 PowerShell ショートカット | `source export.sh` or `get_idf` |
| シリアルポート | `COM7` | `/dev/ttyUSB0` or `/dev/ttyACM0` |
| パス | `C:\xiaozhi-work\` | `~/xiaozhi-work/` |
| セットアップ | `scripts\setup-windows.ps1` | `scripts/setup-ubuntu.sh` |
| 環境チェック | `scripts\check-env.ps1` | `scripts/check-env.sh` |
| USB 権限 | 不要 | `dialout` グループ追加 |

---

*ESP-IDF 公式 Windows ガイド: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/get-started/windows-setup.html*
